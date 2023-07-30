# Copyright (c) 2023 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import os
import sys
from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe
from nyt import NYTRecipe

from calibre.web.feeds.news import BasicNewsRecipe

_name = "New York Times Magazine"


class NYTimesBooks(NYTRecipe, BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    language = "en"
    description = (
        "The New York Times Magazine is an American Sunday magazine "
        "included with the Sunday edition of The New York Times. It "
        "features articles longer than those typically in the newspaper "
        "and has attracted many notable contributors. "
        "https://www.nytimes.com/section/magazine"
    )
    __author__ = "ping"
    publication_type = "magazine"
    oldest_article = 7  # days
    max_articles_per_feed = 25

    remove_attributes = ["style", "font"]
    remove_tags_before = [dict(id="story")]
    remove_tags_after = [dict(id="story")]
    remove_tags = [
        dict(
            id=[
                "in-story-masthead",
                "sponsor-wrapper",
                "top-wrapper",
                "bottom-wrapper",
                "standalone-header",
                "standalone-footer",
            ]
        ),
        dict(class_=["NYTAppHideMasthead", "share", "interactive-header"]),
        dict(role=["toolbar", "navigation"]),
        dict(name=["script", "noscript", "style"]),
    ]

    extra_css = """
    time > span { margin-right: 0.5rem; }
    [data-testid="photoviewer-children"] span {
        font-size: 0.8rem;
    }

    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .sub-headline { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .article-meta { margin-bottom: 1rem; }
    .author { font-weight: bold; color: #444; display: inline-block; }
    .published-dt { margin-left: 0.5rem; }
    .article-img { margin-bottom: 0.8rem; max-width: 100%; }
    .article-img img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box; }
    .article-img .caption, .g-wrappercaption p { margin-top: 0.2rem; margin-bottom: 0; font-size: 0.8rem; }
    div.summary { font-size: 1.2rem; margin: 1rem 0; }
    blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    """

    def populate_article_metadata(self, article, soup, __):
        ts_ele = soup.find(attrs={"data-timestamp": True})
        if not ts_ele:
            return
        post_date = self.parse_date(ts_ele["data-timestamp"])
        if (not self.pub_date) or post_date > self.pub_date:
            self.pub_date = post_date

    def parse_index(self):
        index_url = "https://www.nytimes.com/section/magazine"
        soup = self.index_to_soup(index_url)
        issue_link = next(iter(soup.select(".issue-promo > a.promo-link")), None)
        if not issue_link:
            self.abort_recipe_processing("Unable to find latest issue")

        issue_cover = next(iter(soup.select(".issue-promo .promo-image img")), None)
        if issue_cover:
            # "-superJumbo.jpg" will get an even higher-res version
            self.cover_url = issue_cover["src"].replace("-blog480.jpg", "-jumbo.jpg")
        issue_url = urljoin(index_url, issue_link["href"])
        soup = self.index_to_soup(issue_url)
        info = self.get_script_json(soup, r"window.__preloadedData\s*=\s*")
        if info and info.get("initialState"):
            content_service = info.get("initialState")
            for k, v in content_service["ROOT_QUERY"].items():
                if not (
                    k.startswith("workOrLocation")
                    and v
                    and v["typename"] == "LegacyCollection"
                ):
                    continue
                content_node_id = v["id"]
                break
            issue_info = content_service.get(content_node_id)
            self.pub_date = self.parse_date(
                issue_info.get("lastModified") or issue_info["firstPublished"]
            )
            self.title = f'{_name}: {issue_info["name"]}'
            articles = []
            for v in content_service.values():
                if v.get("__typename", "") != "Article":
                    continue
                try:
                    articles.append(
                        {
                            "url": v["url"],
                            "title": content_service.get(
                                v.get("headline", {}).get("id", "")
                            ).get("default"),
                            "description": v.get("summary", ""),
                            "date": self.parse_date(v["lastMajorModification"]),
                        }
                    )
                except Exception as err:
                    self.log.warning("Error extracting article: %s" % err)

            if articles:
                return [("Articles", articles)]

        self.title = f'{_name}: {self.tag_to_string(soup.find("h1"))}'
        articles = []
        for article in soup.find_all("article"):
            articles.append(
                {
                    "title": self.tag_to_string(article.find("h3")),
                    "url": urljoin(issue_url, article.find("a")["href"]),
                    "description": self.tag_to_string(article.find("p")),
                }
            )
        for article in soup.select("#collection-highlights-container li"):
            a_ele = article.find("a")
            articles.append(
                {
                    "title": self.tag_to_string(a_ele),
                    "url": urljoin(issue_url, a_ele["href"]),
                }
            )
        return [("Articles", articles)]
