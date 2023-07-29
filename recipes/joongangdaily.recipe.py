# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
koreajoongangdaily.joins.com
"""
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds.news import BasicNewsRecipe

_name = "JoongAng Daily"


class KoreaJoongAngDaily(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = "The Korea JoongAng Daily is an English-language daily published by the JoongAng Group, Korea’s leading media group, in association with The New York Times. https://koreajoongangdaily.joins.com/"
    language = "en"
    __author__ = "ping"
    publication_type = "newspaper"
    masthead_url = (
        "https://koreajoongangdaily.joins.com/resources/images/common/logo.png"
    )
    use_embedded_content = True
    auto_cleanup = True
    compress_news_images_auto_size = 10

    oldest_article = 1  # days
    max_articles_per_feed = 60

    extra_css = """
    .caption { font-size: 0.8rem; margin: 0.5rem 0; }
    """

    feeds = [
        ("Korea JoongAng Daily", "https://koreajoongangdaily.joins.com/xmls/joins"),
    ]

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, article.utctime)

    def parse_feeds(self):
        return self.group_feeds_by_date(timezone_offset_hours=9)  # Seoul time
