# Copyright (c) 2023 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import os
import sys
from collections import OrderedDict
from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre.web.feeds.news import BasicNewsRecipe, prefixed_classes

_name = "Prospect Magazine"
_issue_url = ""


class ProspectMagazine(BasicNewsrackRecipe, BasicNewsRecipe):
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
    masthead_url = "https://media.prospectmagazine.co.uk/prod/images/gm_grid_thumbnail/358ffc17208c-f4c3cddcdeda-prospect-masthead.png"
    encoding = "utf-8"
    compress_news_images_auto_size = 8
    ignore_duplicate_articles = {"url"}
    INDEX = "https://www.prospectmagazine.co.uk/issues"

    keep_only_tags = [dict(class_="prop-book-article-panel_main")]
    remove_tags = [
        dict(
            class_=[
                "prop-book-review-header-wrapper_magazine",
                "prop-mobile-social-share_header",
                "prop-magazine-link-block",
                "pros-article-body__img-credit",
                "pros-article-topics__wrapper",
                "pros-article-author__image-wrapper",
                "prop-book-review-promo_details-buy-mobile",
            ]
        ),
        dict(id=["disqus_thread", "newsletter_wrapper"]),
        prefixed_classes("dfp-slot-"),
    ]

    extra_css = """
    h1 { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .prop-book-review-header-wrapper_standfirst { font-size: 1.2rem; font-style: italic; font-weight: normal; margin-bottom: 0.5rem; }

    .prop-book-review-header-wrapper_details {  margin-top: 1rem; margin-bottom: 1rem; }
    .prop-book-review-header-wrapper_details-byline {
        display: inline-block; font-weight: bold; color: #444; margin-right: 0.5rem; }
    .prop-book-review-header-wrapper_details-date { display: inline-block; }
    .gd-picture img { display: block; max-width: 100%; height: auto; }
    .pros-article-body__img-caption, .prop-book-review-header-wrapper__image-caption {
        font-size: 0.8rem; display: block; margin-top: 0.2rem;
    }
    .pullquote, blockquote { text-align: center; margin-left: 0; margin-bottom: 0.4rem; font-size: 1.25rem; }
    .prop-book-review-article_author { margin-top: 1.5rem; font-style: italic; }
    
    .prop-book-review-promo { margin-bottom: 1rem; }
    """

    def preprocess_html(self, soup):
        # re-position lede image
        lede_img = soup.find("img", class_="prop-book-review-header-wrapper_image")
        leded_img_caption = soup.find(
            "div", class_="prop-book-review-header-wrapper__image-caption"
        )
        meta = soup.find("div", class_="prop-book-review-header-wrapper_details")
        if lede_img and meta:
            lede_img = lede_img.extract()
            meta.insert_after(lede_img)
            if leded_img_caption:
                lede_img.insert_after(leded_img_caption)

        for img in soup.find_all("img", attrs={"data-src": True}):
            img["src"] = img["data-src"]
            del img["data-src"]

        for byline_link in soup.find_all("a", attrs={"data-author-name": True}):
            byline_link.unwrap()
        for author_link in soup.find_all("a", class_="pros-article-author"):
            author_link.unwrap()

        # "%B %d, %Y"
        article_date = self.parse_date(
            self.tag_to_string(
                soup.find(class_="prop-book-review-header-wrapper_details-date")
            )
        )
        if (not self.pub_date) or article_date > self.pub_date:
            self.pub_date = article_date

        return soup

    def parse_index(self):
        if not _issue_url:
            issues_soup = self.index_to_soup(self.INDEX)
            curr_issue_a_ele = issues_soup.find(
                "a", class_="pros-collection-landing__item"
            )
            curr_issue_url = urljoin(self.INDEX, curr_issue_a_ele["href"])
        else:
            curr_issue_url = _issue_url

        soup = self.index_to_soup(curr_issue_url)
        issue_name = (
            self.tag_to_string(soup.find(class_="magazine-lhc__issue-name"))
            .replace(" issue", "")
            .strip()
        )
        self.title = f"{_name}: {issue_name}"

        self.cover_url = soup.find("img", class_="magazine-lhc__cover-image")[
            "data-src"
        ].replace("portrait_small_fit", "portrait_large_fit")

        # sections order
        sections_order = [
            "Essays",
            "People",
            "Columns",
            "Regulars",
            "Arts & Books",
            "Lives",
        ]
        articles = OrderedDict()
        for s in sections_order:
            articles[s] = []
        sections = soup.find_all("div", class_="pro-magazine-section")
        for section in sections:
            section_name = self.tag_to_string(
                section.find(class_="pro-magazine-section__name")
            )
            for sect_article in section.find_all(
                class_="pro-magazine-section__article"
            ):
                articles.setdefault(section_name, []).append(
                    {
                        "url": urljoin(self.INDEX, sect_article.find("a")["href"]),
                        "title": self.tag_to_string(
                            sect_article.find(
                                class_="pro-magazine-section__article-headline"
                            )
                        ),
                    }
                )

        # remove empty sections
        for k in list(articles.keys()):
            if not articles[k]:
                del articles[k]

        return articles.items()
