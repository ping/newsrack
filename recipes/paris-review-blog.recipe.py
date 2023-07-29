# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
theparisreview.org
"""
import json
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import WordPressNewsrackRecipe, get_datetime_format

from calibre.web.feeds.news import BasicNewsRecipe

_name = "The Paris Review - Daily"


class ParisReviewBlog(WordPressNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = (
        "The Paris Review is a quarterly English-language literary magazine established in Paris in 1953. "
        "This is a compilation of the daily feed at https://www.theparisreview.org/blog/"
    )
    language = "en"
    __author__ = "ping"

    oldest_article = 10
    max_articles_per_feed = 14
    encoding = "utf-8"
    masthead_url = (
        "https://www.theparisreview.org/il/7d2a53fbaa/medium/Hadada-Circle-holding.png"
    )
    reverse_article_order = False

    remove_attributes = ["style", "width", "height"]
    remove_tags = [dict(class_=["video-title", "videoplayer", "video-footer"])]

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .article-meta { padding-bottom: 0.5rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    p.featured-media img, p img { display: block; max-width: 100%; height: auto; }
    .wp-caption-text { display: block; font-size: 0.8rem; margin-top: 0.2rem; }
    """

    feeds = [
        (_name, "https://www.theparisreview.org/blog/"),
    ]

    def _extract_featured_media(self, post):
        """
        Include featured media with post content.

        :param post: post dict
        :param post_content: Extracted post content
        :return:
        """
        post_content = post["content"]["rendered"]
        if not post.get("featured_media"):
            return post_content

        # featured media post - Kuensel, BBS
        feature_media_css = f"wp-image-{post['featured_media']}"
        if feature_media_css in post_content:
            return post_content

        for feature_info in post.get("_embedded", {}).get("wp:featuredmedia", []):
            # put feature media at the start of the post
            if feature_info.get("source_url"):
                # higher-res
                image_src = f'<p class="featured-media"><img src="{feature_info["source_url"]}"></p>'
                post_content = image_src + post_content
            else:
                post_content = (
                    feature_info.get("description", {}).get("rendered", "")
                    + post_content
                )
        return post_content

    def preprocess_raw_html(self, raw_html, url):
        # formulate the api response into html
        post = json.loads(raw_html)
        date_published_loc = self.parse_date(post["date"], tz_info=None, as_utc=False)
        post_authors = self.extract_authors(post)
        categories = self.extract_categories(post)

        return f"""<html>
        <head><title>{post["title"]["rendered"]}</title></head>
        <body>
            <article data-og-link="{post["link"]}">
            {f'<span class="article-section">{" / ".join(categories)}</span>' if categories else ''}
            <h1 class="headline">{post["title"]["rendered"]}</h1>
            <div class="article-meta">
                {f'<span class="author">{", ".join(post_authors)}</span>' if post_authors else ''}
                <span class="published-dt">
                    {date_published_loc:{get_datetime_format()}}
                </span>
            </div>
            {self._extract_featured_media(post)}
            </article>
        </body></html>"""

    def parse_index(self):
        articles = {}
        br = self.get_browser()
        for feed_name, feed_url in self.feeds:
            articles = self.get_articles(
                articles, feed_name, feed_url, self.oldest_article, {}, br
            )
        return articles.items()
