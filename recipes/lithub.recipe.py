# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import json
import os
import sys
from datetime import datetime

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
try:
    from recipes_shared import WordPressNewsrackRecipe
except ImportError:
    # just for Pycharm to pick up for auto-complete
    from includes.recipes_shared import WordPressNewsrackRecipe

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Literary Hub"


class LitHub(WordPressNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Lit Hub is a site readers can rely on for smart, engaged, entertaining writing "
        "about all things books. https://lithub.com/"
    )
    language = "en"
    publication_type = "blog"
    masthead_url = (
        "https://s26162.pcdn.co/wp-content/themes/rigel/images/social_logo.png"
    )
    encoding = "utf-8"
    reverse_article_order = False
    compress_news_images_auto_size = 10

    oldest_article = 7  # days

    remove_tags = [
        dict(name=["script", "noscript", "style"]),
    ]

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .article-meta {  margin-top: 1rem; margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    .article-img img, .block--article-image__image img, .wp-caption img { display: block; max-width: 100%; height: auto; }
    .article-img .caption, .block--article-image__caption, .wp-caption-text {
        font-size: 0.8rem; display: block; margin-top: 0.2rem;
    }

    .pullquote, blockquote { text-align: center; margin-left: 0; margin-bottom: 0.4rem; font-size: 1.25rem; }
    """

    feeds = [
        (_name, "https://www.lithub.com/wp-json/wp/v2/posts"),
    ]

    def _extract_featured_media(self, post, soup):
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
                # higher-res
                container_ele = soup.new_tag("p", attrs={"class": "article-img"})
                img_ele = soup.new_tag("img", src=feature_info["source_url"])
                container_ele.append(img_ele)
                if feature_info.get("title", {}).get("rendered"):
                    cap_ele = soup.new_tag("span", attrs={"class": "caption"})
                    cap_ele.append(feature_info["title"]["rendered"])
                    container_ele.append(cap_ele)
                post_content = str(container_ele) + post_content
            else:
                post_content = (
                    feature_info.get("description", {}).get("rendered", "")
                    + post_content
                )
        return post_content

    def preprocess_raw_html(self, raw_html, url):
        # formulate the api response into html
        post = json.loads(raw_html)
        date_published_loc = datetime.strptime(post["date"], "%Y-%m-%dT%H:%M:%S")
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
            </article>
        </body></html>"""
        )
        soup.body.article.append(
            BeautifulSoup(self._extract_featured_media(post, soup))
        )
        return str(soup)

    def parse_index(self):
        articles = {}
        br = self.get_browser()
        for feed_name, feed_url in self.feeds:
            custom_params = {"rest_route": None, "categories_exclude": "43110"}
            articles = self.get_articles(
                articles, feed_name, feed_url, self.oldest_article, custom_params, br
            )
        return articles.items()
