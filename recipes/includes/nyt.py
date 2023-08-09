import json
import os
import random
import time
from urllib.parse import urlparse

from calibre import browser
from calibre.ebooks.BeautifulSoup import BeautifulSoup

from recipes_shared import BasicNewsrackRecipe, get_date_format


class NYTRecipe(BasicNewsrackRecipe):
    use_embedded_content = False
    auto_cleanup = False
    compress_news_images_auto_size = 10
    ignore_duplicate_articles = {"title", "url"}

    delay = 0
    simultaneous_downloads = 1
    delay_range = list(range(2, 5))
    bot_blocked = False

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

        if urlparse(target_url).hostname not in ("static01.nyt.com", "mwcm.nyt.com"):
            # we could have used the new get_url_specific_delay() but
            # wayback requests don't need to be delayed
            sleep_interval = random.choice(self.delay_range)
            self.log.debug(f"Sleeping {sleep_interval}s before fetching {target_url}")
            time.sleep(sleep_interval)

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
            # for live articles
            err_msg = f"Skip live article: {url}"
            self.log.warning(err_msg)
            self.abort_article(err_msg)

        if (info.get("initialData", {}) or {}).get("data", {}).get("article"):
            return self.preprocess_initial_data(info, raw_html, url)

        # Sometimes the page does not have article content in the <script>
        # particularly in the Sports section, so we fallback to
        # raw_html and rely on remove_tags to clean it up
        self.log(f"Unable to find article from script in {url}")
        return raw_html
