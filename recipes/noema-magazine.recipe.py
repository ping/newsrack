# Copyright (c) 2023 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0
import json
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import WordPressNewsrackRecipe, get_datetime_format

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Noema Magazine"


class NoemaMagazine(WordPressNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "Noema is an award-winning magazine exploring the transformations sweeping our world. We publish essays, interviews, reportage, videos and art on the overlapping realms of philosophy, governance, geopolitics, economics, technology and culture. https://www.noemamag.com/"
    language = "en"
    publication_type = "magazine"
    oldest_article = 30  # days
    masthead_url = "https://www.noemamag.com/wp-content/uploads/2020/04/noema-logo.png"
    reverse_article_order = False
    compress_news_images_auto_size = 6

    remove_tags = [
        dict(class_=["eos-subscribe-push", "quote__social-media"]),
        dict(name=["script", "noscript", "style"]),
    ]

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .article-meta {  margin-top: 1rem; margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    .article-img img, img.attachment-full { display: block; max-width: 100%; height: auto; }
    .article-img p, .wp-caption-text div {
        font-size: 0.8rem; display: block; margin-top: 0.2rem;
    }
    .quote { text-align: center; }
    .quote .quote__text { margin-left: 0; margin-bottom: 0.4rem; font-size: 1.25rem; }
    """

    feeds = [
        (_name, "https://www.noemamag.com/wp-json/wp/v2/wpm-article"),
    ]

    def extract_categories(self, post):
        categories = []
        if post.get("categories"):
            try:
                for terms in post.get("_embedded", {}).get("wp:term", []):
                    categories.extend(
                        [
                            t["name"]
                            for t in terms
                            if t["taxonomy"] == "wpm-article-topic"
                        ]
                    )
            except (KeyError, TypeError):
                pass
        return categories

    def _extract_featured_media(self, post, soup):
        """
        Include featured media with post content.

        :param post: post dict
        :param post_content: Extracted post content
        :return:
        """
        post_soup = self.soup(post["content"]["rendered"])
        for h in post_soup.find_all("h5"):
            h.name = "h3"
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
                container_ele = soup.new_tag("div", attrs={"class": "article-img"})
                img_ele = soup.new_tag("img", src=feature_info["source_url"])
                container_ele.append(img_ele)
                if feature_info.get("caption", {}).get("rendered"):
                    container_ele.append(self.soup(feature_info["caption"]["rendered"]))
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
            custom_params = {"rest_route": None}
            articles = self.get_articles(
                articles, feed_name, feed_url, self.oldest_article, custom_params, br
            )
        return articles.items()
