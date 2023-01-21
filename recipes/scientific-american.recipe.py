#!/usr/bin/env python
__license__ = "GPL v3"

# Original at https://github.com/kovidgoyal/calibre/blob/29cd8d64ea71595da8afdaec9b44e7100bff829a/recipes/scientific_american.recipe

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe
from css_selectors import Select


def absurl(url):
    if url.startswith("/"):
        url = "https://www.scientificamerican.com" + url
    return url


_name = "Scientific American"


class ScientificAmerican(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = (
        "Popular Science. Monthly magazine. Should be downloaded around the middle of each month. "
        "https://www.scientificamerican.com/"
    )
    category = "science"
    __author__ = "Kovid Goyal"
    language = "en"
    publisher = "Nature Publishing Group"

    masthead_url = (
        "https://static.scientificamerican.com/sciam/assets/Image/newsletter/salogo.png"
    )
    remove_empty_feeds = True

    remove_attributes = ["width", "height"]
    keep_only_tags = [
        dict(
            class_=[
                "feature-article--header-title",
                "article-header",
                "article-content",
                "article-media",
                "article-author",
                "article-text",
            ]
        ),
    ]
    remove_tags = [
        dict(id=["seeAlsoLinks"]),
        dict(alt="author-avatar"),
        dict(
            class_=[
                "article-author__suggested",
                "aside-banner",
                "moreToExplore",
                "article-footer",
            ]
        ),
    ]

    extra_css = """
    h1[itemprop="headline"] { font-size: 1.8rem; margin-bottom: 0.4rem; }
    p.t_article-subtitle { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .meta-list { padding-left: 0; }
    .article-media img, .image-captioned img { max-width: 100%; height: auto; }
    .image-captioned div, .t_caption { font-size: 0.8rem; margin-top: 0.2rem; margin-bottom: 0.5rem; }
    """

    def get_browser(self, *a, **kw):
        kw[
            "user_agent"
        ] = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        br = BasicNewsRecipe.get_browser(self, *a, **kw)
        return br

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        for script in soup.find_all(name="script"):
            if not script.contents:
                continue
            article_js = script.contents[0].strip()
            if not article_js.startswith("dataLayer"):
                continue
            article_js = re.sub(r"dataLayer\s*=\s*", "", article_js)
            if article_js.endswith(";"):
                article_js = article_js[:-1]
            try:
                info = json.loads(article_js)
            except json.JSONDecodeError:
                continue
            for i in info:
                if not i.get("content"):
                    continue
                content = i["content"]
                soup.find("h1")["published_at"] = content["contentInfo"]["publishedAt"]

        # shift article media to after heading
        article_media = soup.find(class_="article-media")
        article_heading = soup.find(name="h1")
        if article_heading and article_media:
            article_heading.parent.append(article_media)
        return str(soup)

    def populate_article_metadata(self, article, soup, first):
        published_ele = soup.find(attrs={"published_at": True})
        if published_ele:
            pub_date = datetime.utcfromtimestamp(
                int(published_ele["published_at"])
            ).replace(tzinfo=timezone.utc)
            article.utctime = pub_date

            # pub date is always 1st of the coming month
            if pub_date > datetime.utcnow().replace(tzinfo=timezone.utc):
                pub_date = (pub_date - timedelta(days=1)).replace(day=1)
            if not self.pub_date or pub_date > self.pub_date:
                self.pub_date = pub_date

    def parse_index(self):
        # Get the cover, date and issue URL
        root = self.index_to_soup(
            "https://www.scientificamerican.com/sciammag/", as_tree=True
        )
        select = Select(root)
        url = [x.get("href", "") for x in select("main .store-listing__img a")][0]
        url = absurl(url)

        # Now parse the actual issue to get the list of articles
        select = Select(self.index_to_soup(url, as_tree=True))
        parsed_cover_url = urlparse(
            [x.get("src", "") for x in select("main .product-detail__image img")][0]
        )
        self.cover_url = f"{parsed_cover_url.scheme}://{parsed_cover_url.netloc}{parsed_cover_url.path}?w=1200"

        for x in select(".t_course-title"):
            self.title = f"{_name}: {x.text}"
            break

        feeds = []
        for i, section in enumerate(select("#sa_body .toc-articles")):
            if i == 0:
                feeds.append(
                    ("Features", list(self.parse_sciam_features(select, section)))
                )
            else:
                feeds.extend(self.parse_sciam_departments(select, section))

        return feeds

    def parse_sciam_features(self, select, section):
        for article in select("article[data-article-title]", section):
            title = article.get("data-article-title")
            url = "https://www.scientificamerican.com/{}/".format(
                article.get("id").replace("-", "/", 1)
            )
            desc = ""
            for p in select("p.t_body", article):
                desc += self.tag_to_string(p)
                break
            for p in select(".t_meta", article):
                desc += " " + self.tag_to_string(p)
                break
            self.log("Found feature article: %s at %s" % (title, url))
            self.log("\t" + desc)
            yield {"title": title, "url": url, "description": desc}

    def parse_sciam_departments(self, select, section):
        section_title, articles = "Unknown", []
        for li in select("li[data-article-title]", section):
            for span in select("span.department-title", li):
                if articles:
                    yield section_title, articles
                section_title, articles = self.tag_to_string(span), []
                self.log("\nFound section: %s" % section_title)
                break
            url = "https://www.scientificamerican.com/{}/".format(
                li.get("id").replace("-", "/", 1)
            )
            for h2 in select("h2.t_listing-title", li):
                title = self.tag_to_string(h2)
                break
            else:
                continue
            articles.append({"title": title, "url": url, "description": ""})
            self.log("\tFound article: %s at %s" % (title, url))
        if articles:
            yield section_title, articles
