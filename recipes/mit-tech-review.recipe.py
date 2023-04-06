# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import json
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import WordPressNewsrackRecipe

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe

_name = "MIT Technology Review"


class MITTechologyReview(WordPressNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "MIT Technology articles. https://www.technologyreview.com/"
    language = "en"
    publication_type = "blog"
    oldest_article = 3  # days
    encoding = "utf-8"
    masthead_url = "https://wp.technologyreview.com/wp-content/uploads/custom-story/1026960/images/logo-MIT-tecnology-review2.svg"
    compress_news_images = False
    compress_news_images_auto_size = 8
    reverse_article_order = False

    remove_tags = [
        dict(name=["script", "noscript", "style"]),
    ]

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .article-meta { padding-bottom: 0.5rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    .wp-block-image img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    .wp-block-image div, .image-credit { font-size: 0.8rem; }
    .wp-block-pullquote blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    .wp-block-pullquote blockquote cite { font-size: 1rem; margin-left: 0; text-align: center; }
    """

    feeds = [
        (_name, "https://www.technologyreview.com/wp-json/wp/v2/posts"),
    ]

    def _extract_featured_media(self, post):
        """
        Include featured media with post content.

        :param post: post dict
        :param post_content: Extracted post content
        :return:
        """
        post_soup = BeautifulSoup(post["content"]["rendered"])
        for img in post_soup.find_all("img", attrs={"data-src": True}):
            img["src"] = img["data-src"]
        post_content = str(post_soup)
        if not post.get("featured_media"):
            return post_content

        feature_media_css = f"wp-image-{post['featured_media']}"
        if feature_media_css in post_content:
            # check already not embedded
            return post_content

        for feature_info in post.get("_embedded", {}).get("wp:featuredmedia", []):
            # put feature media at the start of the post
            if feature_info.get("source_url"):
                caption = feature_info.get("caption", {}).get("rendered", "")
                # higher-res
                image_src = f"""
                <div class="wp-block-image">
                    <img src="{feature_info["source_url"]}">
                    <div class="image-credit">{caption}</div>
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
        date_published_loc = self.parse_datetime(post["date"])
        post_authors = self.extract_authors(post)
        categories = self.extract_categories(post)

        soup = BeautifulSoup(
            f"""<html>
        <head><title>{post["title"]["rendered"]}</title></head>
        <body>
            <article data-og-link="{post["link"]}">
            {f'<span class="article-section">{" / ".join(categories)}</span>' if categories else ''}
            <h1 class="headline">{post["title"]["rendered"]}</h1>
            <div class="article-meta">
                {f'<span class="author">{", ".join(post_authors)}</span>' if post_authors else ''}
                <span class="published-dt">
                    {date_published_loc:%-I:%M%p, %-d %b, %Y}
                </span>
            </div>
            {self._extract_featured_media(post)}
            </article>
        </body></html>"""
        )
        for bq in soup.find_all("blockquote"):
            for strong in bq.find_all("strong"):
                strong.name = "span"
        # for img in soup.find_all(srcset=True):
        #     img["src"] = absurl(img["srcset"].split()[0])
        #     del img["srcset"]
        for img in soup.find_all("img", attrs={"src": True}):
            img["src"] = img["src"].split("?")[0] + "?w=800"
        return str(soup)

    def parse_index(self):
        articles = {}
        br = self.get_browser()
        for feed_name, feed_url in self.feeds:
            custom_params = {"rest_route": None}
            articles = self.get_articles(
                articles, feed_name, feed_url, self.oldest_article, custom_params, br
            )
        return articles.items()
