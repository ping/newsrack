# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title
from nyt import NYTRecipe

from calibre.web.feeds.news import BasicNewsRecipe

_name = "New York Times Books"


class NYTimesBooks(NYTRecipe, BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    language = "en"
    description = (
        "The latest book reviews, best sellers, news and features from "
        "The NY TImes critics and reporters. https://www.nytimes.com/section/books"
    )
    __author__ = "ping"
    publication_type = "newspaper"
    oldest_article = 7  # days
    max_articles_per_feed = 25

    remove_attributes = ["style", "font"]
    remove_tags_before = [dict(id="story")]
    remove_tags_after = [dict(id="story")]
    remove_tags = [
        dict(
            id=["in-story-masthead", "sponsor-wrapper", "top-wrapper", "bottom-wrapper"]
        ),
        dict(
            class_=[
                "NYTAppHideMasthead",
                "css-170u9t6",  # book affliate links
            ]
        ),
        dict(role=["toolbar", "navigation"]),
        dict(name=["script", "noscript", "style"]),
    ]

    extra_css = """
    time > span { margin-right: 0.5rem; }
    [data-testid="photoviewer-children"] span {
        font-size: 0.8rem;
    }

    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .sub-headline { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .article-meta { margin-bottom: 1rem; }
    .author { font-weight: bold; color: #444; display: inline-block; }
    .published-dt { margin-left: 0.5rem; }
    .article-img { margin-bottom: 0.8rem; max-width: 100%; }
    .article-img img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box; }
    .article-img .caption { font-size: 0.8rem; }
    div.summary { font-size: 1.2rem; margin: 1rem 0; }
    """

    feeds = [
        ("NYTimes Books", "https://rss.nytimes.com/services/xml/rss/nyt/Books.xml"),
    ]

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, article.utctime)

    def parse_feeds(self):
        return self.group_feeds_by_date()
