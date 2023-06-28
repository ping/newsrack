# Original at https://github.com/kovidgoyal/calibre/blob/29cd8d64ea71595da8afdaec9b44e7100bff829a/recipes/nature.recipe
import os
import re
import sys
from collections import OrderedDict

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds.news import BasicNewsRecipe

BASE = "https://www.nature.com"


def absurl(url):
    if url.startswith("/"):
        url = BASE + url
    elif url.startswith("http://"):
        url = "https" + url[4:]
    return url


_name = "Nature"
_issue_url = ""


class Nature(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "Jose Ortiz"
    description = (
        "Nature is a weekly international multidisciplinary scientific journal"
        " publishing peer-reviewed research in all fields of science and"
        " technology on the basis of its originality, importance,"
        " interdisciplinary interest, timeliness, accessibility, elegance and"
        " surprising conclusions.  Nature also provides rapid, authoritative,"
        " insightful and arresting news and interpretation of topical and coming"
        " trends affecting science, scientists and the wider public."
        " https://www.nature.com/nature/current-issue/"
    )
    language = "en"
    encoding = "utf-8"
    masthead_url = "https://media.springernature.com/full/nature-cms/uploads/product/nature/header-86f1267ea01eccd46b530284be10585e.svg"

    scale_news_images = (800, 1200)

    keep_only_tags = [dict(name="article")]

    remove_tags = [
        dict(
            class_=[
                "u-hide-print",
                "hide-print",
                "c-latest-content__item",
                "c-context-bar",
                "c-pdf-button__container",
                "u-js-hide",
                "recommended",
            ]
        ),
        dict(
            name="img",
            class_=["visually-hidden"],
        ),
    ]

    extra_css = """
    h1.c-article-magazine-title { font-size: 1.8rem; margin-bottom: 0.5rem; }
    h2.c-article-teaser-text { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    div.c-article-identifiers .c-article-identifiers__item { display: inline-block; font-weight: bold; color: #444; }
    div.c-article-identifiers .c-article-identifiers__item time { font-weight: normal; }
    .c-article-author-list .c-author-list__item { font-weight: bold; color: #444; }
    .c-article-body { margin-top: 1rem; }
    p.figure__caption { font-size: 0.8rem; margin-top: 0.2rem; }
    .figure img { max-width: 100%; height: auto; }
    """

    def populate_article_metadata(self, article, soup, _):
        article_identifiers = soup.find_all(
            attrs={"class": "c-article-identifiers__item"}
        )
        for i in article_identifiers:
            t = i.find(name="time")
            if not t:
                continue
            # "%d %B %Y"
            pub_date_utc = self.parse_date(t.text)
            article.utctime = pub_date_utc
            if not self.pub_date or pub_date_utc > self.pub_date:
                self.pub_date = pub_date_utc

    def preprocess_html(self, soup):
        if soup.find(name="h2", id="access-options"):
            # paid access required
            err_msg = "Subscription required"
            self.log.warning(err_msg)
            self.abort_article(err_msg)

        article_identifier = soup.find(
            name="ul", attrs={"class": "c-article-identifiers"}
        )
        if article_identifier:
            for li in article_identifier.find_all(name="li"):
                li.name = "div"
            article_identifier.name = "div"

        article_authors = soup.find(name="ul", attrs={"class": "c-article-author-list"})
        if article_authors:
            for li in article_authors.find_all(name="li") or []:
                li.name = "div"
                a = li.find(name="a")
                if a:
                    a.unwrap()
            article_authors.name = "div"

        subheadline = soup.find(name="div", attrs={"class": "c-article-teaser-text"})
        if subheadline:
            subheadline.name = "h2"

        for img in soup.find_all("img", {"data-src": True}):
            if img["data-src"].startswith("//"):
                img["src"] = "https:" + img["data-src"]
            else:
                img["src"] = img["data-src"]
        for div in soup.find_all("div", {"data-component": "article-container"})[1:]:
            div.decompose()
        return soup

    def parse_index(self):
        soup = self.index_to_soup(
            _issue_url if _issue_url else f"{BASE}/nature/current-issue"
        )
        self.cover_url = soup.find("img", attrs={"data-test": "issue-cover-image"})[
            "src"
        ]
        try:
            self.cover_url = re.sub(
                r"\bw\d+\b", "w1000", self.cover_url
            )  # enlarge cover size resolution
        except:  # noqa
            """
            failed, img src might have changed, use default width 200
            """
            pass

        title_div = soup.find(attrs={"data-container-type": "title"})
        if title_div:
            mobj = re.search(
                r"Volume \d+ Issue \d+, (?P<issue_date>\d+ [a-z]+ \d{4})",
                self.tag_to_string(title_div),
                re.IGNORECASE,
            )
            if mobj:
                # "%d %B %Y"
                issue_date = self.parse_date(mobj.group("issue_date"))
                self.title = format_title(_name, issue_date)

        sectioned_feeds = OrderedDict()
        section_tags = soup.find_all(
            "section", attrs={"data-container-type": "issue-section-list"}
        )
        for section in section_tags:
            section_title = self.tag_to_string(section.find("h2"))
            if section_title not in sectioned_feeds:
                sectioned_feeds[section_title] = []

            article_list_tag = section.find(
                "ul", attrs={"class": "app-article-list-row"}
            )
            article_tags = article_list_tag.find_all("article")
            for article_tag in article_tags:
                subsection_title = self.tag_to_string(
                    article_tag.find("span", attrs={"class": "c-meta__type"})
                )
                a_tag = article_tag.find("a", attrs={"itemprop": "url"})
                sectioned_feeds[section_title].append(
                    {
                        "title": self.tag_to_string(a_tag),
                        "url": absurl(a_tag["href"]),
                        "description": f'{subsection_title} • {self.tag_to_string(article_tag.find("div", attrs={"itemprop": "description"}))}',
                        "date": article_tag.find("time", attrs={"datetime": True})[
                            "datetime"
                        ],
                        "author": self.tag_to_string(
                            article_tag.find("li", {"itemprop": "creator"})
                        ),
                    }
                )
        return sectioned_feeds.items()
