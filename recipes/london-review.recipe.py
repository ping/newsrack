#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: GPLv3 Copyright: 2019, Kovid Goyal <kovid at kovidgoyal.net>
# Original at: https://github.com/kovidgoyal/calibre/blob/640ca33197ea2c7772278183b3f77701009bb733/recipes/lrb.recipe

import os
import sys
from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre.web.feeds.news import BasicNewsRecipe, classes


_issue_url = ""  # custom issue url
_name = "London Review of Books"


class LondonReviewOfBooks(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "Kovid Goyal"
    description = "Literary review publishing essay-length book reviews and topical articles on politics, literature, history, philosophy, science and the arts by leading writers and thinkers https://www.lrb.co.uk/"  # noqa
    category = "news, literature, UK"
    publisher = "LRB Ltd."
    language = "en_GB"

    # delay = 1
    encoding = "utf-8"
    INDEX = "https://www.lrb.co.uk"
    publication_type = "magazine"
    needs_subscription = False
    requires_version = (3, 0, 0)

    masthead_url = (
        "https://www.pw.org/files/small_press_images/london_review_of_books.png"
    )

    keep_only_tags = [
        classes(
            "article-header--title paperArticle-reviewsHeader article-content letters"
        ),
    ]
    remove_tags = [
        classes(
            "social-button article-mask lrb-readmorelink article-send-letter article-share lettersnav prev-next-buttons"
        ),
        dict(id=["letters-aside"]),
    ]
    remove_attributes = ["width", "height"]

    extra_css = """
    .embedded-image-caption { font-size: 0.8rem; }
    .article-reviewed-item { margin-bottom: 1rem; margin-left: 0.5rem; }
    .article-reviewed-item .article-reviewed-item-title { font-weight: bold; }
    """

    def get_browser(self, *a, **kw):
        kw[
            "user_agent"
        ] = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        br = BasicNewsRecipe.get_browser(self, *a, **kw)
        return br

    def preprocess_html(self, soup):
        info = self.get_ld_json(
            soup,
            lambda d: d,
            attrs={"data-schema": "Article", "type": "application/ld+json"},
        )
        if info:
            soup.body["data-og-summary"] = info.get("description", "")
            # example: 2022-07-28T12:07:08+00:00
            modified_date = self.parse_date(info["dateModified"])
            soup.body["data-og-date"] = f"{modified_date:%Y-%m-%d %H:%M:%S}"
            if not self.pub_date or modified_date > self.pub_date:
                self.pub_date = modified_date
        else:
            letter_ele = soup.find(attrs={"class": "letters-titles--date"})
            if letter_ele:
                # "%d %B %Y"
                published_date = self.parse_date(letter_ele.text)
                soup.body["data-og-date"] = f"{published_date:%Y-%m-%d %H:%M:%S}"
            for letter in soup.find_all(attrs={"class": "letter"}):
                letter.insert_before(soup.new_tag("hr"))

        for img in soup.findAll("img", attrs={"data-srcset": True}):
            for x in img["data-srcset"].split():
                if "/" in x:
                    img["src"] = x
        return soup

    def populate_article_metadata(self, article, soup, _):
        article_summary = soup.find(attrs={"data-og-summary": True})
        if article_summary:
            article.text_summary = article_summary["data-og-summary"]

        article_date = soup.find(attrs={"data-og-date": True})
        if article_date:
            # "%Y-%m-%d %H:%M:%S"
            modified_date = self.parse_date(article_date["data-og-date"])
            article.utctime = modified_date
            article.localtime = modified_date

    def parse_index(self):
        if not _issue_url:
            soup = self.index_to_soup(self.INDEX)
            container = soup.find(class_="issue-grid")
            a = container.find("a")

            soup = self.index_to_soup(urljoin(self.INDEX, a["href"]))
        else:
            soup = self.index_to_soup(_issue_url)
        cover_link = soup.find("a", class_="issue-cover-link")
        if cover_link:
            self.cover_url = cover_link["href"]

        h1 = soup.find("h1", class_="toc-title")
        self.title = f"{_name}: {self.tag_to_string(h1)}"

        grid = soup.find(attrs={"class": "toc-grid-items"})
        articles = []
        for a in grid.findAll(**classes("toc-item")):
            url = urljoin(self.INDEX, a["href"])
            h3 = a.find("h3")
            h4 = a.find("h4")
            review_items = h4.find_all(
                name="div", attrs={"class": "article-reviewed-item"}
            )
            if not review_items:
                if self.tag_to_string(h3) == "Letters":
                    title = self.tag_to_string(h3)
                else:
                    title = "{} - {}".format(
                        self.tag_to_string(h3), self.tag_to_string(h4)
                    )
            else:
                item_descriptions = []
                for item in review_items:
                    desc = ""
                    for c in [
                        "article-reviewed-item-title",
                        "article-reviewed-item-subtitle",
                    ]:
                        s = item.find(name="span", attrs={"class": c})
                        if s:
                            desc += s.contents[0]
                    if desc:
                        item_descriptions.append(desc)

                title = "{} - {}".format(
                    self.tag_to_string(h3), " / ".join(item_descriptions)
                )
            articles.append({"title": title, "url": url})

        return [("Articles", articles)]
