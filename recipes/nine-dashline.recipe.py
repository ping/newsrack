# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
fivebooks.com
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds.news import BasicNewsRecipe

_name = "9DASHLINE"


class NineDashLine(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "9DASHLINE is a digital platform designed to host expert analysis focused on the key issues and dynamics shaping the Indo-Pacific — the world's most dynamic region. https://www.9dashline.com/"
    language = "en"
    publication_type = "blog"
    masthead_url = "https://images.squarespace-cdn.com/content/v1/5d57de05f940b100012af924/1668015012563-F5HGIPIR9FWXODQXN69S/9DASHLINE_Email+Signature.png?format=2500w"
    oldest_article = 30
    compress_news_images_auto_size = 8
    INDEX = "https://www.9dashline.com/"

    keep_only_tags = [dict(class_="Content-outer")]
    remove_tags = [
        dict(
            class_=[
                "BlogItem-meta",
                "BlogItem-share",
                "BlogItem-comments",
                "BlogItem-pagination",
            ]
        )
    ]
    remove_attributes = ["align", "style", "width", "height"]
    extra_css = """
    .image-title-wrapper { font-size: 0.8rem; margin-top: 0.2rem; margin-bottom: 0.5rem; }
    .image-title-wrapper strong { font-weight: normal; }
    blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    blockquote strong { font-weight: normal; }
    blockquote em { font-style: normal; }
    """

    def preprocess_html(self, soup):
        date_ele = soup.find(
            "meta", itemprop="dateModified", content=True
        ) or soup.find("meta", itemprop="datePublished", content=True)
        article_dt = self.parse_date(date_ele["content"])
        if not self.pub_date or article_dt > self.pub_date:
            self.pub_date = article_dt
            self.title = format_title(_name, article_dt)
        return soup

    def parse_index(self):
        cutoff_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=self.oldest_article)

        soup = self.index_to_soup(self.INDEX)
        sections = soup.find_all(class_="summary-v2-block")
        section_articles = {}
        for sect in sections:
            articles = sect.find_all(attrs={"data-animation-role": "content"})
            for article in articles:
                if not article.find("time", attrs={"datetime": True}):
                    continue
                article_dt = self.parse_date(
                    article.find("time", attrs={"datetime": True})["datetime"]
                )
                if article_dt < cutoff_date:
                    continue
                title_link = article.find("a", class_="summary-title-link", href=True)
                a = {
                    "title": self.tag_to_string(title_link),
                    "url": urljoin(self.INDEX, title_link["href"]),
                    "description": self.tag_to_string(
                        article.find(class_="summary-excerpt")
                    ),
                    "date": article_dt,
                }
                for cat_ele in soup.select(".summary-metadata-item--cats a"):
                    category = self.tag_to_string(cat_ele)
                    section_articles.setdefault(category, []).append(a)

        for k in list(section_articles.keys()):
            if not section_articles[k]:
                del section_articles[k]
        return section_articles.items()
