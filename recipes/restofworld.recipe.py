# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
restofworld.org
"""
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Rest of World"


class RestOfWorld(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = "Reporting Global Tech Stories https://restofworld.org/"
    language = "en"
    __author__ = "ping"
    publication_type = "blog"
    oldest_article = 30  # days
    max_articles_per_feed = 25
    masthead_url = "https://restofworld.org/style-guide/images/Variation_3.svg"
    timeout = 60

    keep_only_tags = [dict(id="content")]

    remove_tags = [
        dict(
            class_=[
                "reading-header",
                "footer-recirc",
                "contrib-headshots",
                "post-image-credit",
                "series-callout",
            ]
        ),
        dict(attrs={"aria-hidden": "true"}),
    ]
    extra_css = """
    h1.post-header__text__title { font-size: 1.8rem; margin-bottom: 0.4rem; }
    h3.post-header__text__dek { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; font-weight: normal; }
    .post-subheader { margin-bottom: 1rem; }
    .post-subheader .post-subheader__byline, .contrib-byline { font-weight: bold; color: #444; }
    .post-header__text__contrib p.contrib-bio { margin: 0.2rem 0; }
    .post-header__image { margin-top: 0.5rem; margin-bottom: 0.8rem; }
    .image__wrapper img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    .figcaption { font-size: 0.8rem; }
    blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    .post-footer { margin: 1rem 0; padding-top: 0.5rem; border-top: 1px solid #444; }
    .post-footer .post-footer__authors { font-size: 0.85rem; color: #444; font-style: italic; }
    """

    feeds = [
        ("Rest of World", "https://restofworld.org/feed/latest/"),
    ]

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, article.utctime)

    def preprocess_html(self, soup):
        for h in soup.find_all("h2", class_="contrib-byline"):
            h.name = "div"
        for img in soup.find_all("img", attrs={"data-srcset": True}):
            img["src"] = self.extract_from_img_srcset(
                img["data-srcset"], max_width=1000
            )
        for picture in soup.find_all("picture"):
            sources = picture.find_all("source", attrs={"srcset": True})
            if not sources:
                continue
            if picture.find("img", attrs={"src": True}):
                for s in sources:
                    s.decompose()
        return soup

    def parse_feeds(self):
        return self.group_feeds_by_date()
