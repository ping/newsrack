# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import json
import os
import sys
from datetime import timedelta, timezone

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, get_date_format

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.ptempfile import PersistentTemporaryDirectory, PersistentTemporaryFile
from calibre.web.feeds.news import BasicNewsRecipe

_name = "TIME"


class TimeMagazine(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "Weekly US magazine. https://time.com/magazine/"
    language = "en"
    masthead_url = "https://time.com/img/logo.png"
    oldest_article = 14
    auto_cleanup = False
    reverse_article_order = False

    remove_attributes = ["style"]
    extra_css = """
    .issue { font-weight: bold; margin-bottom: 0.2rem; }
    .headline { font-size: 1.8rem; margin-bottom: 0.5rem; }
    .article-meta {  margin-top: 1rem; margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; display: inline-block; }
    .article-meta .published-dt { display: inline-block; margin-left: 0.5rem; }
    .image-caption { font-size: 0.8rem; margin-top: 0.2rem; margin-bottom: 0.5rem; }
    img { max-width: 100%; height: auto; }
    span.credit { margin-right: 0.5rem; }
    """

    def preprocess_raw_html(self, raw_html, url):
        # formulate the api response into html
        article = json.loads(raw_html)
        try:
            authors = [a["name"] for a in article.get("authors", [])]
        except TypeError:
            # sometimes authors = [[]]
            authors = []
        # "%Y-%m-%d %H:%M:%S"
        date_published_loc = self.parse_date(
            article["time"]["published"],
            tz_info=timezone(timedelta(hours=-4)),
            as_utc=False,
        )
        date_published_utc = date_published_loc.astimezone(timezone.utc)
        if not self.pub_date or date_published_utc > self.pub_date:
            self.pub_date = date_published_utc

        content_soup = BeautifulSoup(article["content"])
        cover_url = self.canonicalize_internal_url(self.cover_url)
        # clean up weirdness
        div_gmail = content_soup.find_all(name="div", attrs={"class": "gmail_default"})
        for div in div_gmail:
            div.name = "p"
        img_lazy = content_soup.find_all(name="img", attrs={"data-lazy-src": True})
        for img in img_lazy:
            # remove cover image
            if cover_url == self.canonicalize_internal_url(img["data-lazy-src"]):
                img.parent.decompose()
                continue
            img["src"] = img["data-lazy-src"]

        return f"""<html>
        <head><title>{article["friendly_title"]}</title></head>
        <body>
            <article data-og-link="{article["url"]}">
            <h1 class="headline">{article["friendly_title"]}</h1>
            <div class="article-meta">
                <span class="author">
                    {", ".join(authors)}
                </span>
                <span class="published-dt">
                    {date_published_loc:{get_date_format()}}
                </span>
            </div>
            {str(content_soup.body)}
            </article>
        </body></html>"""

    def populate_article_metadata(self, article, soup, first):
        # pick up the og link from preprocess_raw_html() and set it as url instead of the api endpoint
        og_link = soup.select("[data-og-link]")
        if og_link:
            article.url = og_link[0]["data-og-link"]

    def parse_index(self):
        br = self.get_browser()
        # Time also has WP endpoints, e.g. https://api.time.com/wp-json/ti-api/v1/posts
        # https://time.com/api/magazine/region/us/
        # https://time.com/api/magazine/region/europe/
        # https://time.com/api/magazine/region/asia/
        # https://time.com/api/magazine/region/south-pacific/
        res = br.open_novisit("https://time.com/api/magazine/region/us/")
        issue_json_raw = res.read().decode("utf-8")
        issue = json.loads(issue_json_raw)[0]
        self.cover_url = issue.get("hero", {}).get("src", {}).get("large_2x")
        self.title = f'{_name}: {issue["title"]}'
        articles = []
        self.temp_dir = PersistentTemporaryDirectory()
        for article in issue["articles"]:
            with PersistentTemporaryFile(suffix=".json", dir=self.temp_dir) as f:
                f.write(json.dumps(article).encode("utf-8"))
            description = article.get("excerpt") or ""
            section = article.get("section", {}).get("name", "")
            if section:
                description = section + (" | " if description else "") + description
            articles.append(
                {
                    "title": article["friendly_title"],
                    "url": "file://" + f.name,
                    "description": description,
                }
            )
        return [("Articles", articles)]
