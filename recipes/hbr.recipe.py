import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre import browser
from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe, classes

# Original https://github.com/kovidgoyal/calibre/blob/49a1d469ce4f04f79ce786a75b8f4bdcfd32ad2c/recipes/hbr.recipe

_name = "Harvard Business Review"
_issue_url = ""


class HBR(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "unkn0wn"
    description = (
        "Harvard Business Review is the leading destination for smart management thinking."
        " Through its flagship magazine, books, and digital content and tools published on HBR.org,"
        " Harvard Business Review aims to provide professionals around the world with rigorous insights"
        " and best practices to help lead themselves and their organizations more effectively and to make a positive impact."
        " https://hbr.org/magazine"
    )
    language = "en"
    encoding = "utf-8"
    base_url = "https://hbr.org"
    masthead_url = "http://hbr.org/resources/css/images/hbr_logo.svg"
    publication_type = "magazine"
    use_embedded_content = False
    auto_cleanup = False
    ignore_duplicate_articles = {"url"}

    remove_attributes = ["height", "width", "style"]
    extra_css = """
        h1.article-hed { font-size: 1.8rem; margin-bottom: 0.4rem; }
        .article-dek {  font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
        .article-byline { margin-top: 0.7rem; font-size: 1rem; color: #444; font-style: normal; font-weight: bold; }
        .pub-date { font-size: 0.8rem; margin-bottom: 1rem; }
        .article-pub-date { margin-left: 0.5rem; font-weight: normal; color: unset; }
        img {
            display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
            box-sizing: border-box;
        }
        .container--caption-credits-hero, .container--caption-credits-inline, span.credit { font-size: 0.8rem; }
        .article-sidebar { border: 1px solid #000; padding: 0.8rem; display: block; }
        .question { font-weight: bold; }
        .description-text {
            margin: 1rem 0;
            border-top: 1px solid #444;
            padding-top: 0.5rem;
            font-style: italic;
        }
        """

    keep_only_tags = [
        classes(
            "headline-container article-dek-group pub-date hero-image-content article-body standard-content"
        ),
        dict(name="article-sidebar"),
    ]

    remove_tags = [
        classes(
            "left-rail--container translate-message follow-topic newsletter-container by-prefix"
        ),
    ]

    def preprocess_raw_html(self, raw_html, _):
        soup = BeautifulSoup(raw_html)

        # set article date
        pub_datetime = soup.find("meta", attrs={"property": "article:published_time"})
        mod_datetime = soup.find("meta", attrs={"property": "article:modified_time"})
        # Example 2022-06-21T17:35:44Z
        post_date = datetime.strptime(pub_datetime["content"], "%Y-%m-%dT%H:%M:%SZ")
        pub_date_ele = soup.find("div", class_="pub-date")
        pub_date_ele["data-pub-date"] = pub_datetime["content"]
        pub_date_ele["data-mod-date"] = mod_datetime["content"]
        post_date_ele = soup.new_tag("span")
        post_date_ele["class"] = "article-pub-date"
        post_date_ele.append(f"{post_date:%-d %B, %Y}")
        # pub_date_ele.append(post_date_ele)    # set this below together with the byline logic

        # break author byline out of list
        byline_list = soup.find("ul", class_="article-byline-list")
        if byline_list:
            byline = byline_list.parent
            byline.append(
                ", ".join(
                    [
                        self.tag_to_string(author)
                        for author in byline_list.find_all(class_="article-author")
                    ]
                )
            )
            byline_list.decompose()
            byline.append(post_date_ele)  # attach post date to byline
        else:
            pub_date_ele.append(post_date_ele)  # attach post date to issue

        return str(soup)

    def populate_article_metadata(self, article, soup, _):
        mod_date_ele = soup.find(attrs={"data-mod-date": True})
        post_date = datetime.strptime(
            mod_date_ele["data-mod-date"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
        if (not self.pub_date) or post_date > self.pub_date:
            self.pub_date = post_date

    def parse_index(self):
        if not _issue_url:
            soup = self.index_to_soup(f"{self.base_url}/magazine")
            a = soup.find("a", href=lambda x: x and x.startswith("/archive-toc/"))
            cov_url = a.find("img", attrs={"src": True})["src"]
            self.cover_url = urljoin(self.base_url, cov_url)
            issue_url = urljoin(self.base_url, a["href"])
        else:
            # no cover if custom issue url is specified
            issue_url = _issue_url

        self.log("Downloading issue:", issue_url)
        soup = self.index_to_soup(issue_url)
        issue_title = soup.find("h1")
        if issue_title:
            self.title = f"{_name}: {self.tag_to_string(issue_title)}"

        feeds = OrderedDict()

        for h3 in soup.find_all("h3", attrs={"class": "hed"}):
            article_link_ele = h3.find("a")
            if not article_link_ele:
                continue

            article_ele = h3.find_next_sibling(
                "div", attrs={"class": "stream-item-info"}
            )
            if not article_ele:
                continue

            articles = []
            title = self.tag_to_string(article_link_ele)
            url = urljoin(self.base_url, article_link_ele["href"])

            authors_ele = article_ele.select("ul.byline li")
            authors = ", ".join([self.tag_to_string(a) for a in authors_ele])

            article_desc = ""
            dek_ele = h3.find_next_sibling("div", attrs={"class": "dek"})
            if dek_ele:
                article_desc = self.tag_to_string(dek_ele) + " | " + authors
            section_ele = (
                h3.findParent("li")
                .find_previous_sibling("div", **classes("stream-section-label"))
                .find("h4")
            )
            section_title = self.tag_to_string(section_ele).title()
            self.log(section_title)
            self.log("\t", title)
            self.log("\t", article_desc)
            self.log("\t\t", url)

            articles.append({"title": title, "url": url, "description": article_desc})
            if articles:
                if section_title not in feeds:
                    feeds[section_title] = []
                feeds[section_title] += articles
        ans = [(key, val) for key, val in feeds.items()]
        return ans

    # HBR changes the content it delivers based on cookies, so the
    # following ensures that we send no cookies
    def get_browser(self, *args, **kwargs):
        return self

    def clone_browser(self, *args, **kwargs):
        return self.get_browser()

    def open_novisit(self, *args, **kwargs):
        br = browser()
        return br.open_novisit(*args, **kwargs)

    open = open_novisit
