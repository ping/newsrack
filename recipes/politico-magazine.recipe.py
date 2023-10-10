# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
politico.com
"""
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds.news import BasicNewsRecipe

_name = "POLITICO Magazine"


class PoliticoMagazine(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "News, Analysis and Opinion from POLITICO https://www.politico.com/"
    publisher = "Capitol News Company, LLC"
    category = "news, politics, USA"
    publication_type = "magazine"
    language = "en"
    masthead_url = "https://www.politico.com/dims4/default/bbb0fd2/2147483647/resize/1160x%3E/quality/90/?url=https%3A%2F%2Fstatic.politico.com%2F0e%2F5b%2F3cf3e0f04ca58370112ab667c255%2Fpolitico-logo.png"

    oldest_article = 7
    max_articles_per_feed = 25

    keep_only_tags = [dict(name=["main"])]
    remove_tags = [
        dict(
            class_=[
                "story-section",
                "social-tools",
                "below-article-section",
                "pop-up-bar",
                "inline-super-footer",
            ]
        ),
        dict(id=["weekend-promo"]),
        dict(name=["source"]),
    ]

    extra_css = """
    .media-item__summary h2.headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .media-item__summary p.dek { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; margin-top: 0; }
    .fig-graphic img, .story-photo__image img { max-width: 100%; height: auto; }
    .story-meta__credit, .story-photo__caption { font-size: 0.8rem; margin-top: 0.2rem; }
    """

    feeds = [("Magazine", "https://rss.politico.com/magazine.xml")]

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, article.utctime)

    def parse_feeds(self):
        return self.group_feeds_by_date()
