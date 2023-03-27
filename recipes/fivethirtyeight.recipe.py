# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
fivethirtyeight.com
"""
import json
import os
import sys
from datetime import timezone
from html import unescape

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])

try:
    from recipes_shared import WordPressNewsrackRecipe, format_title
except ImportError:
    # just for Pycharm to pick up for auto-complete
    from includes.recipes_shared import WordPressNewsrackRecipe, format_title

from calibre.ptempfile import PersistentTemporaryDirectory, PersistentTemporaryFile
from calibre.web.feeds.news import BasicNewsRecipe

_name = "FiveThirtyEight"


class FiveThirtyEight(WordPressNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = "FiveThirtyEight uses statistical analysis — hard numbers — to tell compelling stories about politics, sports, science, economics and culture. https://fivethirtyeight.com/"
    language = "en"
    __author__ = "ping"

    oldest_article = 14
    max_articles_per_feed = 10
    encoding = "utf-8"
    masthead_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/FiveThirtyEight_Logo.svg/1024px-FiveThirtyEight_Logo.svg.png"
    ignore_duplicate_articles = {"url"}

    reverse_article_order = False

    remove_attributes = ["style", "width", "height"]
    remove_tags = [dict(class_=["video-title", "videoplayer", "video-footer"])]

    extra_css = """
    h1.article-title { font-size: 1.8rem; margin-bottom: 0.4rem; }
    h2.article-subtitle { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; font-weight: normal; }
    .single-header-metadata-wrap { margin-bottom: 1rem; }
    .single-header-metadata-wrap .vcard {
        font-weight: bold; color: #444; margin-right: 0.5rem;
        margin-top: 0; margin-bottom: 0;
    }
    .single-topic { margin-top: 0; margin-bottom: 0; }
    .single-featured-image img, p img, .wp-block-image img { margin-bottom: 0.8rem; max-width: 100%; }
    .single-featured-image .caption { display: block; font-size: 0.8rem; margin-top: 0.2rem; }
    """

    feeds = [
        (_name, "https://fivethirtyeight.com/"),
    ]

    def preprocess_raw_html(self, raw_html, url):
        # formulate the api response into html
        post = json.loads(raw_html)

        return f"""<html>
        <head><title>{post["title"]["rendered"]}</title></head>
        <body>
            <article data-og-link="{post["link"]}">
            {post["content"]["rendered"]}
            </article>
        </body></html>"""

    def parse_index(self):
        br = self.get_browser()
        articles = {}
        self.temp_dir = PersistentTemporaryDirectory()

        for feed_name, feed_url in self.feeds:
            custom_params = {
                "rest_route": "/wp/v2/fte_features",
                "espn_verticals_exclude": 67,  # Sports
                "tags_exclude": 329557888,  # Podcasts
            }
            posts = self.get_posts(feed_url, self.oldest_article, custom_params, br)

            latest_post_date = None
            for p in posts:
                post_update_dt = self.parse_datetime(p["modified_gmt"]).replace(
                    tzinfo=timezone.utc
                )
                if not self.pub_date or post_update_dt > self.pub_date:
                    self.pub_date = post_update_dt
                post_date = self.parse_datetime(p["date"])
                if not latest_post_date or post_date > latest_post_date:
                    latest_post_date = post_date
                    self.title = format_title(_name, post_date)

                section_name = f"{post_date:%-d %B, %Y}"
                if len(self.get_feeds()) > 1:
                    section_name = f"{feed_name}: {post_date:%-d %B, %Y}"
                if section_name not in articles:
                    articles[section_name] = []

                with PersistentTemporaryFile(suffix=".json", dir=self.temp_dir) as f:
                    f.write(json.dumps(p).encode("utf-8"))

                verticals = []
                if p.get("espn_verticals"):
                    try:
                        for terms in p.get("_embedded", {}).get("wp:term", []):
                            verticals.extend(
                                [
                                    t["name"]
                                    for t in terms
                                    if t["taxonomy"] == "espn_verticals"
                                ]
                            )

                    except (KeyError, TypeError):
                        pass

                articles[section_name].append(
                    {
                        "title": unescape(p["title"]["rendered"]) or "Untitled",
                        "url": "file://" + f.name,
                        "date": f"{post_date:%-d %B, %Y}",
                        "description": unescape(" / ".join(verticals)),
                    }
                )
        return articles.items()
