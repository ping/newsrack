# Copyright (c) 2023 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import json
import os
import sys
from datetime import timedelta, timezone

from functools import cmp_to_key
from html import unescape

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import WordPressNewsrackRecipe

from calibre.ptempfile import PersistentTemporaryDirectory, PersistentTemporaryFile
from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Prospect Magazine"


class ProspectMagazine(WordPressNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Prospect is Britain’s leading current affairs monthly magazine. "
        "It is an independent and eclectic forum for writing and thinking—in "
        "print and online. Published every month with two double issues in "
        "the summer and winter, it spans politics, science, foreign affairs, "
        "economics, the environment, philosophy and the arts. "
        "https://www.prospectmagazine.co.uk/issues"
    )
    language = "en"
    publication_type = "magazine"
    masthead_url = "https://www.prospectmagazine.co.uk/content/uploads/2021/12/Prospect_logo_Regular.svg"
    encoding = "utf-8"
    reverse_article_order = False
    compress_news_images_auto_size = 8

    oldest_article = 999  # not really enforced

    remove_tags = [
        dict(name=["script", "noscript", "style"]),
        dict(class_=["wp-block-audio"]),
    ]

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .article-meta {  margin-top: 1rem; margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    .article-img img, .wp-block-image img { display: block; max-width: 100%; height: auto; }
    .article-img .caption, .wp-block-image div {
        font-size: 0.8rem; display: block; margin-top: 0.2rem;
    }
    .pullquote, blockquote { text-align: center; margin-left: 0; margin-bottom: 0.4rem; font-size: 1.25rem; }
    """

    feeds = [
        (_name, "https://www.prospectmagazine.co.uk/wp-json/wp/v2/posts"),
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
                if feature_info.get("caption", {}).get("rendered"):
                    cap_ele = soup.new_tag("span", attrs={"class": "caption"})
                    cap_ele.append(
                        BeautifulSoup(feature_info["caption"]["rendered"]).get_text()
                    )
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
        date_published_loc = self.parse_datetime(post["date"])
        post_authors = self.extract_authors(post)
        categories = self.extract_categories(post)
        categories.remove("Magazine")

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
        br = self.get_browser()
        issues_res = br.open_novisit(
            "https://www.prospectmagazine.co.uk/wp-json/wp/v2/issues?_embed=1&per_page=1"
        )
        latest_issue = json.loads(issues_res.read().decode("utf-8"))[0]
        issue_date = self.parse_datetime(latest_issue["date_gmt"]) - timedelta(
            days=3
        )  # go back a little just in case
        self.title = f'{_name}: {latest_issue["title"]["rendered"]}'

        # extract cover
        featured_media = latest_issue.get("_embedded", {}).get(
            "wp:featuredmedia", [{}]
        )[0]
        self.cover_url = (
            featured_media.get("media_details", {})
            .get("sizes", {})
            .get("1536x1536", {})
            .get("source_url")
            or featured_media.get("media_details", {})
            .get("sizes", {})
            .get("large", {})
            .get("source_url")
            or featured_media.get("media_details", {}).get("source_url")
        )
        custom_params = {
            "rest_route": None,
            "categories": "68085",  # magazine
            "after": issue_date.isoformat(),
            "_embed": "1",
        }

        sections = ["Essays", "People", "Columns", "Regulars", "Arts & Books", "Lives"]
        articles = {}
        posts = self.get_posts(self.feeds[0][1], self.oldest_article, custom_params, br)

        self.temp_dir = PersistentTemporaryDirectory()
        for p in posts:
            post_update_dt = self.parse_datetime(p["modified_gmt"]).replace(
                tzinfo=timezone.utc
            )
            if not self.pub_date or post_update_dt > self.pub_date:
                self.pub_date = post_update_dt
            post_date = self.parse_datetime(p["date_gmt"]).replace(tzinfo=timezone.utc)
            categories = self.extract_categories(p)
            categories = [unescape(c) for c in categories]
            categories.remove("Magazine")
            categories_filtered = list(set(categories) & set(sections))
            if categories_filtered:
                categories = categories_filtered
            else:
                print("*" * 10, "|".join(categories))
            category = next(iter(categories), None)
            if category:
                section_name = category
            else:
                section_name = "Magazine"
            if section_name not in articles:
                articles[section_name] = []

            with PersistentTemporaryFile(suffix=".json", dir=self.temp_dir) as f:
                f.write(json.dumps(p).encode("utf-8"))
            articles[section_name].append(
                {
                    "title": BeautifulSoup(unescape(p["title"]["rendered"])).get_text()
                    or "Untitled",
                    "url": "file://" + f.name,
                    "date": f"{post_date:%-d %B, %Y}",
                    "date_gmt": p["date_gmt"],
                    "description": unescape(p["excerpt"]["rendered"]),
                }
            )
        for section in articles.keys():
            # sort articles
            articles[section] = sorted(articles[section], key=lambda a: a["date_gmt"])

        section_articles = articles.items()

        def sort_sections(a, b):
            a_section = a[0]
            b_section = b[0]

            try:
                a_index = sections.index(a_section)
            except ValueError:
                a_index = 999
            try:
                b_index = sections.index(b_section)
            except ValueError:
                b_index = 999

            if a_index != b_index:
                # sort order found via toc
                return -1 if a_index < b_index else 1

            if a_section != b_section:
                return -1 if a_section < b_section else 1

            return -1 if a_section < b_section else 1

        section_articles = sorted(section_articles, key=cmp_to_key(sort_sections))

        return section_articles
