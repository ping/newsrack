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

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Foreign Policy"
_issue_url = ""


class ForeignPolicy(WordPressNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Foreign Policy is an American news publication, founded in 1970 and "
        "focused on global affairs, current events, and domestic and international "
        "policy. It produces content daily on its website and app, and in four "
        "print issues annually. https://foreignpolicy.com/"
    )
    language = "en"
    publication_type = "blog"
    oldest_article = 7  # days
    encoding = "utf-8"
    masthead_url = "https://foreignpolicy.com/wp-content/themes/foreign-policy-2017/assets/src/images/logos/favicon-256.png"
    reverse_article_order = False
    compress_news_images_auto_size = 12

    remove_tags = [
        dict(
            class_=[
                "Apple-converted-space",
                "graphic-chatter",
                "fp_choose_placement_related_posts",
                "sidebar-box_right",
                "newsletter-unit-signup",
                "newsletter-unit-signup--shortcode-fallback",
            ]
        ),
        dict(style="height:0;opacity:0;"),
        dict(name=["noscript"]),
    ]

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .article-meta {  margin-top: 1rem; margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    .article-img img, img.attachment-full { display: block; max-width: 100%; height: auto; }
    .article-img p, .wp-caption-text {
        font-size: 0.8rem; display: block; margin-top: 0.2rem;
    }
    .pull-quote-sidebar {
        display: block; text-align: center;
        margin-left: 0; margin-bottom: 0.4rem; font-size: 1.25rem;
    }
    """

    feeds = [
        (_name, "https://www.foreignpolicy.com/"),
    ]

    def preprocess_raw_html(self, raw_html, url):
        # formulate the api response into html
        post = json.loads(raw_html)
        if not post:
            self.abort_article()
        date_published_loc = self.parse_date(post["date"], tz_info=None, as_utc=False)
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
                    {date_published_loc:{get_datetime_format()}}
                </span>
            </div>
            </article>
        </body></html>"""
        )

        content = BeautifulSoup(post["content"]["rendered"])
        # FP doesn't use featuremedia, the first attachment is the lede image
        attachment_endpoint = (
            post.get("_links", {}).get("wp:attachment", [{}])[0].get("href")
        )
        if attachment_endpoint:
            attachment = next(
                iter(json.loads(self.index_to_soup(attachment_endpoint, raw=True))), {}
            )
            if attachment:
                lede = soup.new_tag("div", attrs={"class": "image-attachment"})
                img = soup.new_tag("img", attrs={"src": attachment["source_url"]})
                lede.append(img)
                if attachment.get("caption", {}).get("rendered"):
                    caption = soup.new_tag("div", attrs={"class": "wp-caption-text"})
                    caption.append(
                        BeautifulSoup(
                            attachment["caption"]["rendered"], features="html.parser"
                        )
                    )
                    lede.append(caption)
                soup.body.article.append(lede)

        soup.body.article.append(content)

        for img in soup.find_all("img", attrs={"data-lazy-src": True}):
            img["src"] = img["data-lazy-src"]
            # also cleanup a little
            for attribute in (
                "data-lazy-src",
                "data-lazy-srcset",
                "data-lazy-sizes",
                "data-src",
                "loading",
            ):
                if img.get(attribute):
                    del img[attribute]

        return str(soup)

    def parse_index(self):
        articles = {}
        br = self.get_browser()
        for feed_name, feed_url in self.feeds:
            articles = self.get_articles(
                articles, feed_name, feed_url, self.oldest_article, {}, br
            )
        return articles.items()
