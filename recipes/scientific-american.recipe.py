#!/usr/bin/env python
__license__ = "GPL v3"

# Original at https://github.com/kovidgoyal/calibre/blob/29cd8d64ea71595da8afdaec9b44e7100bff829a/recipes/scientific_american.recipe

import os
import sys
from datetime import datetime, timezone, timedelta
from os.path import splitext
from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre.web.feeds.news import BasicNewsRecipe


_name = "Scientific American"
_issue_url = ""


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
    compress_news_images_auto_size = 8

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
                "article-date-published",
            ]
        ),
    ]

    extra_css = """
    h1[itemprop="headline"] { font-size: 1.8rem; margin-bottom: 0.4rem; }
    p.t_article-subtitle { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .meta-list { padding-left: 0; margin-bottom: 1rem; }
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
        soup = self.soup(raw_html)
        info = self.get_script_json(soup, r"dataLayer\s*=\s*")
        if info:
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

        # unset author meta ul li
        for ul in soup.find_all("ul", class_="meta-list"):
            for li in ul.find_all("li"):
                li.name = "div"
            ul.name = "div"
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
        if not _issue_url:
            fp_soup = self.index_to_soup("https://www.scientificamerican.com")
            curr_issue_link = fp_soup.select(".tout_current-issue__cover a")
            if not curr_issue_link:
                self.abort_recipe_processing("Unable to find issue link")
            issue_url = curr_issue_link[0]["href"]
        else:
            issue_url = _issue_url

        soup = self.index_to_soup(issue_url)
        info = self.get_script_json(soup, "", attrs={"id": "__NEXT_DATA__"})
        if not info:
            self.abort_recipe_processing("Unable to find script")

        issue_info = info.get("props", {}).get("pageProps", {}).get("issue", {})
        if not issue_info:
            self.abort_recipe_processing("Unable to find issue info")

        image_id, ext = splitext(issue_info["image"])
        self.cover_url = f"https://static.scientificamerican.com/sciam/cache/file/{image_id}_source{ext}?w=960"

        # "%Y-%m-%d"
        issue_date = self.parse_date(issue_info["issue_date"])
        self.title = (
            f"{_name}: {issue_date:%B %Y} "
            f'Vol. {issue_info.get("volume", "")}, Issue {issue_info.get("issue", "")}'
        )

        feeds = {}
        for section in ("featured", "departments"):
            for article in issue_info.get("article_previews", {}).get(section, []):
                if section == "featured":
                    feed_name = "Features"
                else:
                    feed_name = article["category"]
                if feed_name not in feeds:
                    feeds[feed_name] = []
                feeds[feed_name].append(
                    {
                        "title": article["title"],
                        "url": urljoin(
                            "https://www.scientificamerican.com/article/",
                            article["slug"],
                        ),
                        "description": article["summary"],
                    }
                )

        return feeds.items()
