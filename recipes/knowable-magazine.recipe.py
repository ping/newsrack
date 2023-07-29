# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
knowablemagazine.org
"""
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Knowable Magazine"


class KnowableMagazine(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Knowable Magazine explores the real-world significance of scholarly work "
        "through a journalistic lens. We report on the current state of play across "
        "a wide variety of fields — from agriculture to high-energy physics; "
        "biochemistry to water security; the origins of the universe to psychology. "
        "https://knowablemagazine.org/"
    )
    masthead_url = "https://knowablemagazine.org/pb-assets/knowable-assets/images/logo-1586554394067.svg"
    language = "en"
    publication_type = "magazine"
    timeout = 60

    oldest_article = 45  # days
    max_articles_per_feed = 15
    scale_news_images = (800, 1200)

    keep_only_tags = [
        dict(class_=["article-container"]),
    ]
    remove_attributes = ["style"]
    remove_tags = [
        dict(name=["script", "style", "svg"]),
        dict(attrs={"data-widget-def": True}),
        dict(id=["newsletter-promo-item"]),
        dict(
            class_=[
                "promo",
                "ember-view",
                "promo-article-dark",
                "share-icons-box",
                "article-tags",
                "article-republish",
            ]
        ),
    ]

    extra_css = """
    h1 { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .article-subhead { font-size: 1.2rem; font-style: italic; font-weight: normal; margin-bottom: 0.5rem; margin-top: 0; }
    .article-byline {  margin-top: 0.5rem; margin-bottom: 1rem; }
    .article-byline .author-byline {  font-weight: bold; color: #444; display: inline-block; }
    .article-byline .pub-date {  display: inline-block; margin-left: 0.5rem; }
    .article-image img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    .article-image .caption { font-size: 0.8rem; }
    .pull-quote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    """

    feeds = [
        (_name, "https://knowablemagazine.org/rss"),
    ]

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, article.utctime)

    def parse_feeds(self):
        return self.group_feeds_by_date(timezone_offset_hours=-7)  # PST
