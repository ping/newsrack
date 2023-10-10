# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import json
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import WordPressNewsrackRecipe, get_datetime_format

from calibre.web.feeds.news import BasicNewsRecipe, prefixed_classes

_name = "Longreads Features"


class LongreadsFeatures(WordPressNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "Sharing the best nonfiction storytelling on the web since 2011. https://longreads.com/features/"
    language = "en"
    oldest_article = 30  # days
    masthead_url = "https://i0.wp.com/longreads.com/wp-content/uploads/2022/08/longreads-logo-1.png?w=600&ssl=1"
    reverse_article_order = False

    remove_tags = [
        prefixed_classes("subscribe__"),
        dict(name=["script", "noscript", "style"]),
        dict(class_=["wp-block-group"]),
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
    p.has-text-align-center { text-align: center; }
    blockquote.wp-block-quote, .wp-block-pullquote blockquote { text-align: center; margin-left: 0; margin-bottom: 0.4rem; font-size: 1.25rem; }
    """

    feeds = [
        (_name, "https://longreads.com/wp-json/wp/v2/posts"),
    ]

    def _extract_featured_media(self, post, soup):
        """
        Include featured media with post content.

        :param post: post dict
        :param post_content: Extracted post content
        :return:
        """
        post_soup = self.soup(post["content"]["rendered"])
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
        date_published_loc = self.parse_date(post["date"], tz_info=None, as_utc=False)
        post_authors = self.extract_authors(post)
        categories = self.extract_categories(post)

        soup = self.soup(
            f"""<html>
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
            </article>
        </body></html>"""
        )
        soup.body.article.append(self.soup(self._extract_featured_media(post, soup)))
        return str(soup)

    def parse_index(self):
        articles = {}
        br = self.get_browser()
        for feed_name, feed_url in self.feeds:
            custom_params = {
                "rest_route": None,
                "categories": ",".join(
                    [str(i) for i in [6, 15974]]
                ),  # 6 - Essays, 15974 - Features
                "tags_exclude": ",".join([str(i) for i in [3643]]),  # 3643 - Podcast
            }
            articles = self.get_articles(
                articles, feed_name, feed_url, self.oldest_article, custom_params, br
            )
        return articles.items()
