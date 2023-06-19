# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0
import os
import sys
from datetime import datetime
from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe

_issue_url = ""
_name = "The World Today"


class WorldToday(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "The World Today is a bi-monthly global affairs magazine founded by Chatham House, international affairs think tank, in 1945. https://www.chathamhouse.org/publications/the-world-today/"
    masthead_url = (
        "https://www.chathamhouse.org/themes/custom/numiko/logo/chatham-house-logo.png"
    )
    publication_type = "magazine"
    language = "en"
    encoding = "utf-8"
    ignore_duplicate_articles = {"url"}
    compress_news_images_auto_size = 4
    scale_news_images = (800, 1200)
    remove_empty_feeds = True

    BASE_URL = "https://www.chathamhouse.org"
    keep_only_tags = [
        dict(class_=["hero__title", "hero__subtitle", "hero__meta"]),
        dict(name="article", class_=["content-layout"]),
    ]
    remove_attributes = ["style", "width", "height"]
    remove_tags = [
        dict(
            class_=[
                "hero__meta-label",
                "person-teaser__contact",
                "person-teaser__image-container",
            ]
        ),
        dict(name=["svg"]),
    ]
    extra_css = """
    h1.hero__title { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .hero__subtitle { font-size: 1.2rem; margin-bottom: 1.2rem; font-style: italic; }
    .hero__subtitle p { margin: 0; }
    .hero__meta { color: #444; }
    .hero__meta .hero__meta-read-time { margin-left: 1rem; }
    .authors { color: #444; margin-bottom: 1rem; }
    .authors .person-teaser__meta { font-size: 0.85rem; }
    .authors a { color: #444; }
    .authors h3 { margin: 0; font-weight: bold; font-size: 1rem; }
    .authors p { margin: 0; }
    blockquote, .media-callout { font-size: 1.25rem; margin-left: 0; text-align: center; }
    blockquote { margin: 0 }
    .media-callout .h1 { font-weight: bold; font-size: 1.8rem; }
    .media-callout p, blockquote p { margin: 0; }
    .media-image img {
        display: block; margin-bottom: 0.3rem;
        max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    .media-image p { font-size: 0.8rem; margin: 0; }
    .media-image p:first-child { display: inline-block; }
    .js-sidebar-responsive { margin-top: 2rem; }
    .js-sidebar-responsive h2 { font-size: 1rem; }
    """

    def _urlize(self, url_string, base_url=None):
        if url_string.startswith("//"):
            url_string = "https:" + url_string
        if url_string.startswith("/"):
            url_string = urljoin(base_url or self.BASE_URL, url_string)
        return url_string

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        # find pub date
        mod_date_ele = soup.find("meta", attrs={"property": "article:modified_time"})
        # Example: 2022-09-30T12:40:17+0100 "%Y-%m-%dT%H:%M:%S%z"
        post_mod_date = self.parse_date(mod_date_ele["content"])
        if not self.pub_date or post_mod_date > self.pub_date:
            self.pub_date = post_mod_date
        for img in soup.find_all("img", attrs={"srcset": True}):
            img["src"] = self._urlize(
                img["srcset"].strip().split(",")[-1].strip().split(" ")[0]
            )
            del img["srcset"]
        return str(soup)

    def parse_index(self):
        if _issue_url:
            soup = self.index_to_soup(_issue_url)
        else:
            soup = self.index_to_soup(
                "https://www.chathamhouse.org/publications/the-world-today/"
            )

        issue_edition = (
            self.tag_to_string(
                soup.find("h2", attrs={"class": "hero__title-supplementary"})
            )
            .replace("Issue:", "")
            .strip()
        )
        self.title = f"{_name}: {issue_edition}"

        articles = []
        issue_items = soup.find_all("article", attrs={"class": "teaser", "about": True})
        for item in issue_items:
            title = self.tag_to_string(
                item.find("h3", attrs={"class": "teaser__title"})
            )
            description = self.tag_to_string(
                item.find("div", attrs={"class": "teaser__summary"})
            )
            link = self._urlize(item["about"])
            articles.append({"title": title, "url": link, "description": description})

        return [(_name, articles)]
