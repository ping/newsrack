# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
thediplomat.com
"""
import json
import os
import sys
from html import unescape

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import WordPressNewsrackRecipe, get_date_format

from calibre.web.feeds.news import BasicNewsRecipe

_name = "The Diplomat"


class TheDiplomat(WordPressNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = "The Diplomat is a current-affairs magazine for the Asia-Pacific, with news and analysis on politics, security, business, technology and life across the region. https://thediplomat.com/"
    language = "en"
    __author__ = "ping"
    publication_type = "magazine"

    oldest_article = 7
    max_articles_per_feed = 25
    masthead_url = "https://thediplomat.com/wp-content/themes/td_theme_v3/assets/logo/diplomat_logo_black.svg"

    compress_news_images_auto_size = 8
    reverse_article_order = False

    remove_attributes = ["style", "width", "height"]

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .sub-headline { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .sub-headline p { margin-top: 0; }
    .article-meta { margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    .article-img, .wp-caption { margin-bottom: 0.8rem; max-width: 100%; }
    .article-img img, .wp-caption img { display: block; max-width: 100%; height: auto; }
    .article-img .caption, .wp-caption-text { display: block; font-size: 0.8rem; margin-top: 0.2rem; }
    .article-img .caption p { margin: 0; }
    """

    feeds = [
        (_name, "https://thediplomat.com/"),
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

        for feature_info in post.get("_embedded", {}).get("wp:featuredmedia", []):
            # put feature media at the start of the post
            if feature_info.get("source_url"):
                caption = feature_info.get("caption", {}).get("rendered", "")
                # higher-res
                image_src = f"""
                <div class="article-img">
                    <img src="{feature_info["source_url"]}">
                    <div class="caption">{caption}</div>
                </div>"""
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
        post_date = self.parse_date(post["date"], tz_info=None, as_utc=False)
        soup = self.soup(
            f"""<html>
        <head></head>
        <body>
            <h1 class="headline"></h1>
            <article data-og-link="{post["link"]}">
                <div class="sub-headline"></div>
                <div class="article-meta">
                    <span class="published-dt">{post_date:{get_date_format()}}</span>
                </div>
            </div>
            </article>
        </body></html>"""
        )
        title = soup.new_tag("title")
        title.string = unescape(post["title"]["rendered"])
        soup.body.h1.string = unescape(post["title"]["rendered"])
        soup.find("div", class_="sub-headline").append(
            self.soup(post["excerpt"]["rendered"])
        )
        # inject authors
        post_authors = self.extract_authors(post)
        if post_authors:
            soup.find(class_="article-meta").insert(
                0,
                self.soup(f'<span class="author">{", ".join(post_authors)}</span>'),
            )
        # inject categories
        categories = self.extract_categories(post)
        if categories:
            soup.body.article.insert(
                0,
                self.soup(
                    f'<span class="article-section">{" / ".join(categories)}</span>'
                ),
            )
        soup.body.article.append(self.soup(self._extract_featured_media(post)))
        return str(soup)

    def populate_article_metadata(self, article, soup, first):
        # pick up the og link from preprocess_raw_html() and set it as url instead of the api endpoint
        og_link = soup.select("[data-og-link]")
        if og_link:
            article.url = og_link[0]["data-og-link"]
        article.title = soup.find("h1", class_="headline").string

    def parse_index(self):
        articles = {}
        br = self.get_browser()
        for feed_name, feed_url in self.feeds:
            articles = self.get_articles(
                articles, feed_name, feed_url, self.oldest_article, {}, br
            )
        return articles.items()
