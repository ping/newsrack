# Copyright (c) 2023 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urljoin, urlencode

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, get_datetime_format

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe
from calibre.utils.cleantext import clean_ascii_chars

_name = "Washington Post (Print)"
_skip_sections = ["sports", "style", "weekend"]


class TheWashingtonPostPrint(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "Today's Washington Post https://www.washingtonpost.com/todays_paper/updates/"  # noqa
    publisher = "The Washington Post Company"
    category = "news, politics, USA"
    publication_type = "newspaper"
    masthead_url = "https://www.washingtonpost.com/sf/brand-connect/dell-technologies/the-economics-of-change/media/wp_logo_black.png"

    use_embedded_content = False
    remove_empty_feeds = True
    auto_cleanup = False
    encoding = "utf-8"
    language = "en"
    simultaneous_downloads = 8
    compress_news_images_auto_size = 12

    oldest_article = 1
    max_articles_per_feed = 25
    ignore_duplicate_articles = {"url"}

    remove_attributes = ["style"]
    index = "https://www.washingtonpost.com/todays_paper/updates/"

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .sub-headline { font-size: 1.2rem; font-style: italic; margin-bottom: 0.5rem; }
    .article-meta {  margin-top: 0.5rem; margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; display: block; }
    .figure, .video { margin: 0.5rem 0; }
    .figure img { max-width: 100%; height: auto; }
    .figure .caption { font-size: 0.8rem; margin-top: 0.2rem; }
    .video { color: #444; font-size: 0.8rem; }
    .video .caption { margin-top: 0.2rem; }
    .keyupdates li { margin-bottom: 0.5rem; }
    """

    def image_url_processor(self, article_url, image_url):
        image_processor = "https://www.washingtonpost.com/wp-apps/imrs.php"
        if image_url.startswith(image_processor):
            return image_url
        return f'{image_processor}?{urlencode({"src": image_url, "w": 1200})}'

    def _extract_child_nodes(self, nodes, parent_element, soup, url):
        if not nodes:
            return
        for c in nodes:
            node_type = c["type"]
            if node_type in [
                "interstitial_link",
                "",
                "custom_embed",
                "divider",
                "gallery",  # real estate ads
            ]:
                continue
            if node_type == "text":
                para_ele = soup.new_tag("p")
                para_ele.append(BeautifulSoup(c["content"], features="html.parser"))
                parent_element.append(para_ele)
            elif node_type == "image":
                figure_ele = soup.new_tag("figure", attrs={"class": "figure"})
                # this is mad slow -_-, better to just download the original img from s3
                # img_url = f'https://www.washingtonpost.com/wp-apps/imrs.php?{urlencode({"src": c["url"], "w": 916})}'
                img_ele = soup.new_tag("img", src=c["url"])
                figure_ele.append(img_ele)
                caption_ele = soup.new_tag("figcaption", attrs={"class": "caption"})
                caption_ele.string = c.get("credits_caption_display", "")
                figure_ele.append(caption_ele)
                parent_element.append(figure_ele)
            elif node_type == "video":
                video_url = urljoin(
                    "https://www.washingtonpost.com", c["canonical_url"]
                )
                container_ele = soup.new_tag("div", attrs={"class": "video"})
                video_link_ele = soup.new_tag("a", href=video_url)
                video_link_ele.string = video_url
                caption_ele = soup.new_tag("figcaption", attrs={"class": "caption"})
                caption_ele.string = f'Video: {c.get("credits_caption_display", "")}'
                container_ele.append(caption_ele)
                container_ele.append(video_link_ele)
                parent_element.append(container_ele)
            elif node_type == "header":
                header_ele = soup.new_tag(f'h{c["level"]}')
                header_ele.append(BeautifulSoup(c["content"], features="html.parser"))
                parent_element.append(header_ele)
            elif node_type == "correction":
                para_ele = soup.new_tag("p", attrs={"class": "correction"})
                para_ele.append(BeautifulSoup(c.get("content") or c.get("text")))
                parent_element.append(para_ele)
            elif node_type == "oembed_response":
                embed_ele = BeautifulSoup(c["raw_oembed"]["html"])
                parent_element.append(embed_ele)
            elif node_type == "raw_html":
                content = BeautifulSoup(c["content"])
                container = content.find("div", attrs={"data-fallback-image-url": True})
                if container:
                    figure_ele = soup.new_tag("figure")
                    figure_ele["class"] = "figure"
                    img_url = container["data-fallback-image-url"]
                    img_ele = soup.new_tag("img", src=img_url)
                    figure_ele.append(img_ele)
                    caption_ele = soup.new_tag("figcaption", attrs={"class": "caption"})
                    caption_ele.string = c.get("additional_properties", {}).get(
                        "fallback_image_description", ""
                    )
                    figure_ele.append(caption_ele)
                    parent_element.append(figure_ele)
            elif (
                node_type in ["keyupdates", "list"]
                and c.get("list_type") == "unordered"
            ):
                container_ele = soup.new_tag("div", attrs={"class": node_type})
                header_string = c.get("additional_properties", {}).get(
                    "header", ""
                ) or c.get("header")
                if header_string:
                    header_ele = soup.new_tag("h3")
                    header_ele.append(
                        BeautifulSoup(header_string, features="html.parser")
                    )
                    container_ele.append(header_ele)
                ol_ele = soup.new_tag("ol")
                for i in c.get("items", []):
                    li_ele = soup.new_tag("li")
                    li_ele.append(BeautifulSoup(i["content"], features="html.parser"))
                    ol_ele.append(li_ele)
                container_ele.append(ol_ele)
                parent_element.append(container_ele)
            elif node_type == "story" and c["subtype"] in [
                "live-update",
                "live-reporter-insight",
            ]:
                container_ele = soup.new_tag("div", attrs={"class": node_type})
                # add a hr to separate stories
                container_ele.append(soup.new_tag("hr", attrs={"class": "story"}))

                header_ele = soup.new_tag("h3")
                header_ele.append(
                    BeautifulSoup(
                        c.get("headlines", {}).get("basic", ""), features="html.parser"
                    )
                )
                container_ele.append(header_ele)

                # Example 2022-04-13T14:04:03.051Z "%Y-%m-%dT%H:%M:%S.%fZ"
                post_date = self.parse_date(c["display_date"])
                meta_ele = BeautifulSoup(
                    f"""<div class="article-meta">
                        <span class="author"></span>
                        <span class="published-dt">{post_date:{get_datetime_format()}}</span>
                    </div>""",
                    features="html.parser",
                )
                authors = [a["name"] for a in c.get("credits", {}).get("by", [])]
                meta_ele.find("span", class_="author").append(", ".join(authors))
                container_ele.append(meta_ele)
                self._extract_child_nodes(
                    c["content_elements"], container_ele, soup, url
                )
                parent_element.append(container_ele)
            elif node_type == "quote" and c.get("subtype") == "blockquote":
                container_ele = soup.new_tag("blockquote")
                self._extract_child_nodes(
                    c["content_elements"], container_ele, soup, url
                )
                parent_element.append(container_ele)
            else:
                self.log.warning(f"{url} has unexpected element: {node_type}")
                self.log.debug(json.dumps(c))

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        data = self.get_script_json(soup, "", {"id": "__NEXT_DATA__", "src": False})
        content = data.get("props", {}).get("pageProps", {}).get("globalContent", {})
        if not content:
            # E.g. interactive articles
            # https://www.washingtonpost.com/world/interactive/2022/china-shanghai-covid-lockdown-food-shortage/
            if "/interactive/" in url:
                err_msg = f"Exclude interactive article: {url}"
            else:
                err_msg = f"Unable to get content from script: {url}"
            self.log.warning(err_msg)
            self.abort_article(err_msg)

        # Example 2022-04-13T14:04:03.051Z "%Y-%m-%dT%H:%M:%S.%fZ"
        post_date = self.parse_date(content["display_date"])
        if post_date > datetime.utcnow().replace(tzinfo=timezone.utc):  # it happens
            try:
                # "%Y-%m-%dT%H:%M:%S"
                post_date = self.parse_date(content["publish_date"][:-5])
            except:  # noqa
                # do nothing
                pass
        if not self.pub_date or post_date > self.pub_date:
            self.pub_date = post_date
        description = content.get("description", {}).get("basic", "")

        title = content["headlines"]["basic"]
        html = f"""<html>
        <head></head>
        <body>
            <article>
                <h1 class="headline"></h1>
                <div class="sub-headline"></div>
                <div class="article-meta">
                    <span class="author"></span>
                    <span class="published-dt">{post_date:{get_datetime_format()}}</span>
                </div>
            </article>
        </body></html>"""
        new_soup = BeautifulSoup(html)
        title_ele = new_soup.new_tag("title")
        title_ele.append(title)
        new_soup.head.append(title_ele)
        new_soup.body.article.h1.append(title)
        if description:
            new_soup.body.article["data-description"] = description
        if content.get("subheadlines", {}).get("basic", ""):
            new_soup.find("div", class_="sub-headline").append(
                content["subheadlines"]["basic"]
            )
        else:
            new_soup.find("div", class_="sub-headline").decompose()
        authors = [a["name"] for a in content.get("credits", {}).get("by", [])]
        new_soup.find("span", class_="author").append(", ".join(authors))
        self._extract_child_nodes(
            content.get("content_elements"), new_soup.body.article, new_soup, url
        )
        return str(new_soup)

    def populate_article_metadata(self, article, soup, first):
        desc_ele = soup.find(attrs={"data-description": True})
        if desc_ele:
            article.summary = desc_ele["data-description"]
            article.text_summary = clean_ascii_chars(desc_ele["data-description"])

    def parse_index(self):
        soup = self.index_to_soup(self.index)
        today_ele = soup.find("h2")
        if today_ele:
            self.title = f"{_name}: {self.tag_to_string(today_ele)}"
        articles = {}
        for section in soup.find_all("section", attrs={"id": True}):
            section_name = self.tag_to_string(section.find("label")).strip()
            if section_name.lower() in _skip_sections:
                continue
            section_articles = []
            self.log(f"Section: {section_name}")
            for link in section.find_all("a", attrs={"href": True}):
                if link.find("img"):
                    # cover page link
                    continue
                if link["href"] in (
                    "https://www.washingtonpost.com/",
                    "https://www.washingtonpost.com/local/",
                ):
                    # Digest links
                    continue
                section_articles.append(
                    {"url": link["href"], "title": self.tag_to_string(link).strip()}
                )
                self.log(f'\t{self.tag_to_string(link)}\n\t{link["href"]}')
            if not section_articles:
                continue
            if section_name not in articles:
                articles[section_name] = []
            articles[section_name].extend(section_articles)
        return articles.items()
