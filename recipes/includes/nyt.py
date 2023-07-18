import json
import os
from urllib.parse import urlparse

from recipes_shared import get_date_format

from calibre import browser
from calibre.ebooks.BeautifulSoup import BeautifulSoup


class NYTRecipe:
    # The NYT occassionally returns bogus articles for some reason just in case
    # it is because of cookies, dont store cookies
    def get_browser(self, *args, **kwargs):
        return self

    def clone_browser(self, *args, **kwargs):
        return self.get_browser()

    def open_from_wayback(self, url, br=None):
        """
        Fallback to wayback cache from calibre.
        Modified from `download_url()` from https://github.com/kovidgoyal/calibre/blob/d2977ebec40a66af568adff7976cfd16f99ccbe5/src/calibre/web/site_parsers/nytimes.py
        :param url:
        :param br:
        :return:
        """
        from mechanize import Request

        rq = Request(
            "https://wayback1.calibre-ebook.com/nytimes",
            data=json.dumps({"url": url}),
            headers={"User-Agent": "calibre", "Content-Type": "application/json"},
        )
        if br is None:
            br = browser()
        br.set_handle_gzip(True)
        return br.open_novisit(rq, timeout=3 * 60)

    def open_novisit(self, *args, **kwargs):
        target_url = args[0]
        is_wayback_cached = urlparse(target_url).netloc == "www.nytimes.com"

        if is_wayback_cached and self.bot_blocked:
            # don't use wayback for static assets because these are not blocked currently
            # and the wayback cache does not support them anyway
            self.log.warn(f"Block detected. Fetching from wayback cache: {target_url}")
            return self.open_from_wayback(target_url)

        br = browser(
            user_agent="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        )
        try:
            return br.open_novisit(*args, **kwargs)
        except Exception as e:
            if hasattr(e, "code") and e.code == 403:
                self.bot_blocked = True
                self.delay = 0  # I don't think this makes a difference but oh well
                if is_wayback_cached:
                    self.log.warn(
                        f"Blocked by bot detection. Fetching from wayback cache: {target_url}"
                    )
                    return self.open_from_wayback(target_url)

                # if static asset is also blocked, give up
                err_msg = f"Blocked by bot detection: {target_url}"
                self.log.warning(err_msg)
                self.abort_recipe_processing(err_msg)
                self.abort_article(err_msg)
            raise

    open = open_novisit

    def render_content(self, content, soup, parent):
        content_type = content["__typename"]
        if content_type in [
            "Dropzone",
            "RelatedLinksBlock",
            "EmailSignupBlock",
            "CapsuleBlock",  # ???
            "InteractiveBlock",
            "RelatedLinksBlock",
            "UnstructuredBlock",
        ]:
            return

        if content_type == "TextInline":
            if (
                content.get("formats")
                and content["formats"][0]["__typename"] == "LinkFormat"
            ):
                a = soup.new_tag("a", attrs={"href": content["formats"][0]["url"]})
                a.append(content.get("text", ""))
                return a
            else:
                parent.append(content.get("text", ""))
            return
        if content_type == "Heading1Block":
            return soup.new_tag("h1", attrs={"class": "headline"})
        if content_type == "Heading2Block":
            return soup.new_tag("h2")
        if content_type == "Heading3Block":
            return soup.new_tag("h3")
        if content_type == "BylineBlock":
            div = soup.new_tag("div", attrs={"class": "author"})
            for byline in content.get("bylines", []):
                if byline.get("renderedRepresentation"):
                    div.append(byline["renderedRepresentation"])
            return div
        if content_type == "TimestampBlock":
            post_date = self.parse_date(content["timestamp"])
            div = soup.new_tag(
                "time",
                attrs={"data-timestamp": content["timestamp"], "class": "published-dt"},
            )
            div.append(f"{post_date:{get_date_format()}}")
            return div
        if content_type == "ImageBlock":
            div = soup.new_tag("div", attrs={"class": "article-img"})
            if content.get("media"):
                img = self.render_content(content["media"], soup, div)
                if img:
                    div.append(img)
            return div
        if content_type == "Image":
            div = soup.new_tag("div", attrs={"class": "article-img"})
            for v in content.get("crops", []):
                img_url = v["renditions"][0]["url"]
                img_ele = soup.new_tag("img")
                img_ele["src"] = img_url
                div.append(img_ele)
                break
            if content.get("legacyHtmlCaption"):
                span_ele = soup.new_tag("span", attrs={"class": "caption"})
                span_ele.append(BeautifulSoup(content["legacyHtmlCaption"]))
                div.append(span_ele)
            return div
        if content_type == "SummaryBlock":
            div = soup.new_tag("div", attrs={"class": "sub-headline"})
            return div
        if content_type == "ListItemBlock":
            return soup.new_tag("li")
        if content_type in [
            "HeaderBasicBlock",
            "HeaderFullBleedVerticalBlock",
            "HeaderFullBleedHorizontalBlock",
            "HeaderMultimediaBlock",
            "HeaderLegacyBlock",
        ]:
            div = soup.new_tag("div", attrs={"class": content_type})
            for t in ("headline", "summary", "ledeMedia", "byline", "timestampBlock"):
                if content.get(t):
                    c = content[t]
                    d = self.render_content(c, soup, div)
                    if d:
                        for cc in c.get("content", []):
                            dd = self.render_content(cc, soup, d)
                            if dd:
                                d.append(dd)
                        div.append(d)
            return div
        if content_type == "ParagraphBlock":
            p = soup.new_tag("p")
            return p
        if content_type == "DetailBlock":
            div = soup.new_tag("div", attrs={"class": content_type})
            return div
        if content_type == "RuleBlock":
            return soup.new_tag("hr")
        if content_type == "LineBreakInline":
            return soup.new_tag("br")
        if content_type == "DiptychBlock":
            # 2-image block
            div = soup.new_tag("div", attrs={"class": content_type})
            image_blocks = [content["imageOne"], content["imageTwo"]]
            for c in image_blocks:
                img = self.render_content(c, soup, div)
                if img:
                    div.append(img)
            return div
        if content_type == "GridBlock":
            # n-image block
            div = soup.new_tag("div", attrs={"class": content_type})
            for c in content.get("gridMedia", []):
                img = self.render_content(c, soup, div)
                if img:
                    div.append(img)
            caption = (
                f'{content.get("caption", "")} {content.get("credit", "")}'.strip()
            )
            if caption:
                span_ele = soup.new_tag("span", attrs={"class": "caption"})
                span_ele.append(BeautifulSoup(caption))
                div.append(span_ele)
            return div
        if content_type == "BlockquoteBlock":
            return soup.new_tag("blockquote")
        if content_type == "PullquoteBlock":
            blockquote = soup.new_tag("blockquote")
            for c in content["quote"]:
                q = self.render_content(c, soup, blockquote)
                if q:
                    blockquote.append(q)
            return blockquote
        if content_type == "LabelBlock":
            return soup.new_tag("h4", attrs={"class": "label"})
        if content_type == "VideoBlock":
            div = soup.new_tag("div", attrs={"class": "embed"})
            media = content.get("media")
            if media.get("url"):
                a_ele = soup.new_tag("a", attrs={"href": media["url"]})
                a_ele.append("[Embedded video available]")
                div.append(a_ele)
            else:
                div.append("[Embedded video available]")
            return div
        if content_type == "AudioBlock":
            div = soup.new_tag("div", attrs={"class": "embed"})
            media = content.get("media")
            if media.get("url"):
                a_ele = soup.new_tag("a", attrs={"href": media["url"]})
                a_ele.append("[Embedded audio available]")
                div.append(a_ele)
            else:
                div.append("[Embedded audio available]")
            return div
        if content_type == "YouTubeEmbedBlock":
            div = soup.new_tag("div", attrs={"class": "embed"})
            yt_link = f'https://www.youtube.com/watch?v={content["youTubeId"]}'
            a_ele = soup.new_tag("a", href=yt_link)
            a_ele.append(yt_link)
            div.append(a_ele)
            return div
        if content_type == "TwitterEmbedBlock":
            div = soup.new_tag("div", attrs={"class": "embed"})
            div.append(BeautifulSoup(content["html"], features="html.parser"))
            return div
        if content_type == "InstagramEmbedBlock":
            div = soup.new_tag("div", attrs={"class": "embed"})
            a_ele = soup.new_tag("a", href=content["instagramUrl"])
            a_ele.string = content["instagramUrl"]
            div.append(a_ele)
            return div
        if content_type == "ListBlock":
            if content["style"] == "UNORDERED":
                return soup.new_tag("ul")
            return soup.new_tag("ol")

        self.log.warning(
            f'Unknown content type: "{content_type}": {json.dumps(content)}'
        )
        return None

    def nested_render(self, content, soup, parent):
        for cc in content.get("content@filterEmpty", []) or content.get("content", []):
            content_ele = self.render_content(cc, soup, parent)
            if content_ele:
                if cc.get("content"):
                    self.nested_render(cc, soup, content_ele)
                parent.append(content_ele)

    def preprocess_initial_data(self, info, raw_html, url):
        article = (info.get("initialData", {}) or {}).get("data", {}).get("article")
        body = article.get("sprinkledBody") or article.get("body")
        if not body:
            return raw_html

        template_html = """<html><head><title></title></head><body></body></html>"""
        soup = BeautifulSoup(template_html, "html.parser")
        self.nested_render(body, soup, soup)
        return str(soup)

    def preprocess_initial_state(self, info, raw_html, url):
        content_service = info.get("initialState")
        content_node_id = None
        for k, v in content_service["ROOT_QUERY"].items():
            if not (
                k.startswith("workOrLocation") and v and v["typename"] == "Article"
            ):
                continue
            content_node_id = v["id"]
            break
        if not content_node_id:
            for k, v in content_service["ROOT_QUERY"].items():
                if not (
                    k.startswith("workOrLocation")
                    and v
                    and v["typename"] == "LegacyCollection"
                ):
                    continue
                content_node_id = v["id"]
                break

        if not content_node_id:
            self.log(f"Unable to find content in script in {url}")
            return raw_html

        article = content_service.get(content_node_id)
        try:
            body = article.get("sprinkledBody") or article.get("body")
            document_block = content_service[body["id"]]  # typename = "DocumentBlock"
        except:  # noqa
            # live blog probably
            self.log(f"Unable to find content in article object for {url}")
            return raw_html

        template_html = """<html><head><title></title></head>
        <body>
            <article>
            <h1 class="headline"></h1>
            <div class="sub-headline"></div>
            <div class="article-meta">
                <span class="author"></span>
                <span class="published-dt"></span>
            </div>
            </article>
        </body></html>
        """
        new_soup = BeautifulSoup(template_html, "html.parser")

        for c in document_block.get("content@filterEmpty", []):
            content_type = c["typename"]
            if content_type in [
                "Dropzone",
                "RelatedLinksBlock",
                "EmailSignupBlock",
                "CapsuleBlock",  # ???
                "InteractiveBlock",
            ]:
                continue
            if content_type in [
                "HeaderBasicBlock",
                "HeaderFullBleedVerticalBlock",
                "HeaderFullBleedHorizontalBlock",
                "HeaderMultimediaBlock",
                "HeaderLegacyBlock",
            ]:
                # Article Header / Meta
                header_block = content_service[c["id"]]
                if header_block.get("headline"):
                    heading_text = ""
                    headline = content_service[header_block["headline"]["id"]]
                    if headline.get("default@stripHtml"):
                        heading_text += headline["default@stripHtml"]
                    else:
                        for x in headline.get("content", []):
                            heading_text += content_service.get(x["id"], {}).get(
                                "text@stripHtml", ""
                            ) or content_service.get(x["id"], {}).get("text", "")
                    new_soup.head.title.string = heading_text
                    new_soup.body.article.h1.string = heading_text
                if header_block.get("summary"):
                    summary_text = ""
                    for x in content_service.get(header_block["summary"]["id"]).get(
                        "content", []
                    ):
                        summary_text += content_service.get(x["id"], {}).get(
                            "text@stripHtml", ""
                        ) or content_service.get(x["id"], {}).get("text", "")
                    subheadline = new_soup.find("div", class_="sub-headline")
                    subheadline.string = summary_text
                if header_block.get("timestampBlock"):
                    # Example 2022-04-12T09:00:05.000Z "%Y-%m-%dT%H:%M:%S.%fZ"
                    post_date = self.parse_date(
                        content_service[header_block["timestampBlock"]["id"]][
                            "timestamp"
                        ]
                    )
                    pub_dt_ele = new_soup.find("span", class_="published-dt")
                    pub_dt_ele.string = f"{post_date:{get_date_format()}}"
                if header_block.get("ledeMedia"):
                    image_block = content_service.get(
                        content_service[header_block["ledeMedia"]["id"]]["media"]["id"]
                    )
                    container_ele = new_soup.new_tag(
                        "div", attrs={"class": "article-img"}
                    )
                    for k, v in image_block.items():
                        if not k.startswith("crops("):
                            continue
                        img_url = content_service[
                            content_service[v[0]["id"]]["renditions"][0]["id"]
                        ]["url"]
                        img_ele = new_soup.new_tag("img")
                        img_ele["src"] = img_url
                        container_ele.append(img_ele)
                        break
                    if image_block.get("legacyHtmlCaption"):
                        span_ele = new_soup.new_tag("span", attrs={"class": "caption"})
                        span_ele.append(BeautifulSoup(image_block["legacyHtmlCaption"]))
                        container_ele.append(span_ele)
                    new_soup.body.article.append(container_ele)
                if header_block.get("byline"):
                    authors = []
                    for b in content_service[header_block["byline"]["id"]]["bylines"]:
                        for creator in content_service[b["id"]]["creators"]:
                            authors.append(
                                content_service[creator["id"]]["displayName"]
                            )
                    pub_dt_ele = new_soup.find("span", class_="author")
                    pub_dt_ele.string = ", ".join(authors)
            elif content_type == "ParagraphBlock":
                para_ele = new_soup.new_tag("p")
                para_ele.string = ""
                for cc in content_service.get(c["id"], {}).get("content", []):
                    para_ele.string += content_service.get(cc["id"], {}).get("text", "")
                new_soup.body.article.append(para_ele)
            elif content_type == "ImageBlock":
                image_block = content_service.get(
                    content_service.get(c["id"], {}).get("media", {}).get("id", "")
                )
                container_ele = new_soup.new_tag("div", attrs={"class": "article-img"})
                for k, v in image_block.items():
                    if not k.startswith("crops("):
                        continue
                    img_url = content_service[
                        content_service[v[0]["id"]]["renditions"][0]["id"]
                    ]["url"]
                    img_ele = new_soup.new_tag("img")
                    img_ele["src"] = img_url
                    container_ele.append(img_ele)
                    break
                if image_block.get("legacyHtmlCaption"):
                    span_ele = new_soup.new_tag("span", attrs={"class": "caption"})
                    span_ele.append(BeautifulSoup(image_block["legacyHtmlCaption"]))
                    container_ele.append(span_ele)
                new_soup.body.article.append(container_ele)
            elif content_type == "DiptychBlock":
                # 2-image block
                diptych_block = content_service[c["id"]]
                image_block_ids = [
                    diptych_block["imageOne"]["id"],
                    diptych_block["imageTwo"]["id"],
                ]
                for image_block_id in image_block_ids:
                    image_block = content_service[image_block_id]
                    container_ele = new_soup.new_tag(
                        "div", attrs={"class": "article-img"}
                    )
                    for k, v in image_block.items():
                        if not k.startswith("crops("):
                            continue
                        img_url = content_service[
                            content_service[v[0]["id"]]["renditions"][0]["id"]
                        ]["url"]
                        img_ele = new_soup.new_tag("img")
                        img_ele["src"] = img_url
                        container_ele.append(img_ele)
                        break
                    if image_block.get("legacyHtmlCaption"):
                        span_ele = new_soup.new_tag("span", attrs={"class": "caption"})
                        span_ele.append(BeautifulSoup(image_block["legacyHtmlCaption"]))
                        container_ele.append(span_ele)
                    new_soup.body.article.append(container_ele)
            elif content_type == "GridBlock":
                # n-image block
                grid_block = content_service[c["id"]]
                image_block_ids = [
                    m["id"]
                    for m in grid_block.get("media", [])
                    if m["typename"] == "Image"
                ]
                container_ele = new_soup.new_tag("div", attrs={"class": "article-img"})
                for image_block_id in image_block_ids:
                    image_block = content_service[image_block_id]
                    for k, v in image_block.items():
                        if not k.startswith("crops("):
                            continue
                        img_url = content_service[
                            content_service[v[0]["id"]]["renditions"][0]["id"]
                        ]["url"]
                        img_ele = new_soup.new_tag("img")
                        img_ele["src"] = img_url
                        container_ele.append(img_ele)
                        break
                caption = (
                    f'{grid_block.get("caption", "")} {grid_block.get("credit", "")}'
                ).strip()
                if caption:
                    span_ele = new_soup.new_tag("span", attrs={"class": "caption"})
                    span_ele.append(BeautifulSoup(caption))
                    container_ele.append(span_ele)
                new_soup.body.article.append(container_ele)
            elif content_type == "DetailBlock":
                container_ele = new_soup.new_tag("div", attrs={"class": "detail"})
                for x in content_service[c["id"]]["content"]:
                    d = content_service[x["id"]]
                    if d["__typename"] == "LineBreakInline":
                        container_ele.append(new_soup.new_tag("br"))
                    elif d["__typename"] == "TextInline":
                        container_ele.append(d["text"])
                new_soup.body.article.append(container_ele)
            elif content_type == "BlockquoteBlock":
                container_ele = new_soup.new_tag("blockquote")
                for x in content_service[c["id"]]["content"]:
                    if x["typename"] == "ParagraphBlock":
                        para_ele = new_soup.new_tag("p")
                        para_ele.string = ""
                        for xx in content_service.get(x["id"], {}).get("content", []):
                            para_ele.string += content_service.get(xx["id"], {}).get(
                                "text", ""
                            )
                        container_ele.append(para_ele)
                new_soup.body.article.append(container_ele)
            elif content_type in ["Heading1Block", "Heading2Block", "Heading3Block"]:
                if content_type == "Heading1Block":
                    container_tag = "h1"
                elif content_type == "Heading2Block":
                    container_tag = "h2"
                else:
                    container_tag = "h3"
                container_ele = new_soup.new_tag(container_tag)
                for x in content_service[c["id"]]["content"]:
                    if x["typename"] == "TextInline":
                        container_ele.append(
                            content_service[x["id"]].get("text", "")
                            or content_service[x["id"]].get("text@stripHtml", "")
                        )
                new_soup.body.article.append(container_ele)
            elif content_type == "ListBlock":
                list_block = content_service[c["id"]]
                if list_block["style"] == "UNORDERED":
                    container_ele = new_soup.new_tag("ul")
                else:
                    container_ele = new_soup.new_tag("ol")
                for x in content_service[c["id"]]["content"]:
                    li_ele = new_soup.new_tag("li")
                    for y in content_service[x["id"]]["content"]:
                        if y["typename"] == "ParagraphBlock":
                            para_ele = new_soup.new_tag("p")
                            for z in content_service.get(y["id"], {}).get(
                                "content", []
                            ):
                                para_ele.append(
                                    content_service.get(z["id"], {}).get("text", "")
                                )
                            li_ele.append(para_ele)
                    container_ele.append(li_ele)
                new_soup.body.article.append(container_ele)
            elif content_type == "PullquoteBlock":
                container_ele = new_soup.new_tag("blockquote")
                for x in content_service[c["id"]]["quote"]:
                    if x["typename"] == "TextInline":
                        container_ele.append(content_service[x["id"]]["text"])
                    if x["typename"] == "ParagraphBlock":
                        para_ele = new_soup.new_tag("p")
                        for z in content_service.get(x["id"], {}).get("content", []):
                            para_ele.append(
                                content_service.get(z["id"], {}).get("text", "")
                            )
                        container_ele.append(para_ele)
                new_soup.body.article.append(container_ele)
            elif content_type == "VideoBlock":
                container_ele = new_soup.new_tag("div", attrs={"class": "embed"})
                container_ele.string = "[Embedded video available]"
                new_soup.body.article.append(container_ele)
            elif content_type == "AudioBlock":
                container_ele = new_soup.new_tag("div", attrs={"class": "embed"})
                container_ele.string = "[Embedded audio available]"
                new_soup.body.article.append(container_ele)
            elif content_type == "BylineBlock":
                # For podcasts? - TBD
                pass
            elif content_type == "YouTubeEmbedBlock":
                container_ele = new_soup.new_tag("div", attrs={"class": "embed"})
                yt_link = f'https://www.youtube.com/watch?v={content_service[c["id"]]["youTubeId"]}'
                a_ele = new_soup.new_tag("a", href=yt_link)
                a_ele.string = yt_link
                container_ele.append(a_ele)
                new_soup.body.article.append(container_ele)
            elif content_type == "TwitterEmbedBlock":
                container_ele = new_soup.new_tag("div", attrs={"class": "embed"})
                container_ele.append(BeautifulSoup(content_service[c["id"]]["html"]))
                new_soup.body.article.append(container_ele)
            elif content_type == "LabelBlock":
                container_ele = new_soup.new_tag("h4", attrs={"class": "label"})
                for x in content_service[c["id"]]["content"]:
                    if x["typename"] == "TextInline":
                        container_ele.append(content_service[x["id"]]["text"])
                new_soup.body.article.append(container_ele)
            elif content_type == "SummaryBlock":
                container_ele = new_soup.new_tag("div", attrs={"class": "summary"})
                for x in content_service[c["id"]]["content"]:
                    if x["typename"] == "TextInline":
                        container_ele.append(content_service[x["id"]]["text"])
                new_soup.body.article.append(container_ele)
            elif content_type == "TimestampBlock":
                timestamp_val = content_service[c["id"]]["timestamp"]
                container_ele = new_soup.new_tag(
                    "time", attrs={"data-timestamp": timestamp_val}
                )
                container_ele.append(timestamp_val)
                new_soup.body.article.append(container_ele)
            elif content_type == "RuleBlock":
                new_soup.body.article.append(new_soup.new_tag("hr"))
            else:
                self.log.warning(f"{url} has unexpected element: {content_type}")
                self.log.debug(json.dumps(c))
                self.log.debug(json.dumps(content_service[c["id"]]))

        return str(new_soup)

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        info = self.get_script_json(soup, r"window.__preloadedData\s*=\s*")
        if not info:
            if os.environ.get("recipe_debug_folder", ""):
                recipe_folder = os.path.join(
                    os.environ["recipe_debug_folder"], __name__
                )
                if not os.path.exists(recipe_folder):
                    os.makedirs(recipe_folder)
                debug_output_file = os.path.join(
                    recipe_folder, os.path.basename(urlparse(url).path)
                )
                if not debug_output_file.endswith(".html"):
                    debug_output_file += ".html"
                self.log(f'Writing debug raw html to "{debug_output_file}" for {url}')
                with open(debug_output_file, "w", encoding="utf-8") as f:
                    f.write(raw_html)
            self.log(f"Unable to find article from script in {url}")
            return raw_html

        if info.get("initialState"):
            return self.preprocess_initial_state(info, raw_html, url)

        if (info.get("initialData", {}) or {}).get("data", {}).get("article"):
            return self.preprocess_initial_data(info, raw_html, url)

        # Sometimes the page does not have article content in the <script>
        # particularly in the Sports section, so we fallback to
        # raw_html and rely on remove_tags to clean it up
        self.log(f"Unable to find article from script in {url}")
        return raw_html
