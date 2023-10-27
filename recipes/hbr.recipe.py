import json
import os
import re
import sys
from collections import OrderedDict
from urllib.parse import urlencode, urljoin

from calibre import browser, random_user_agent

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicCookielessNewsrackRecipe, get_date_format

from calibre.web.feeds.news import BasicNewsRecipe, classes
from mechanize import Request

# Original https://github.com/kovidgoyal/calibre/blob/49a1d469ce4f04f79ce786a75b8f4bdcfd32ad2c/recipes/hbr.recipe

_name = "Harvard Business Review"
_issue_url = ""


class HBR(BasicCookielessNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Harvard Business Review is the leading destination for smart management thinking. "
        "Through its flagship magazine, books, and digital content and tools published on HBR.org, "
        "Harvard Business Review aims to provide professionals around the world with rigorous insights "
        "and best practices to help lead themselves and their organizations more effectively and to "
        "make a positive impact. https://hbr.org/magazine"
    )
    language = "en"
    base_url = "https://hbr.org"
    masthead_url = "https://hbr.org/resources/css/images/hbr_logo.svg"
    publication_type = "magazine"

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
            "headline-container article-dek-group pub-date hero-image-content "
            "article-body standard-content"
        ),
    ]

    remove_tags = [
        classes(
            "left-rail--container translate-message follow-topic "
            "newsletter-container by-prefix related-topics--common"
        ),
        dict(name=["article-sidebar"]),
    ]

    def preprocess_raw_html(self, raw_html, article_url):
        soup = self.soup(raw_html)

        # set article date
        pub_datetime = soup.find("meta", attrs={"property": "article:published_time"})
        mod_datetime = soup.find("meta", attrs={"property": "article:modified_time"})
        # Example 2022-06-21T17:35:44Z "%Y-%m-%dT%H:%M:%SZ"
        post_date = self.parse_date(pub_datetime["content"])
        pub_date_ele = soup.find("div", class_="pub-date")
        pub_date_ele["data-pub-date"] = pub_datetime["content"]
        pub_date_ele["data-mod-date"] = mod_datetime["content"]
        post_date_ele = soup.new_tag("span")
        post_date_ele["class"] = "article-pub-date"
        post_date_ele.append(f"{post_date:{get_date_format()}}")

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

        # Extract full article content
        content_ele = soup.find(
            "content",
            attrs={
                "data-index": True,
                "data-page-year": True,
                "data-page-month": True,
                "data-page-seo-title": True,
                "data-page-slug": True,
            },
        )
        endpoint_url = "https://hbr.org/api/article/piano/content?" + urlencode(
            {
                "year": content_ele["data-page-year"],
                "month": content_ele["data-page-month"],
                "seotitle": content_ele["data-page-seo-title"],
            }
        )
        data = {
            "contentKey": content_ele["data-index"],
            "pageSlug": content_ele["data-page-slug"],
        }
        headers = {
            "User-Agent": random_user_agent(),
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Referer": article_url,
        }
        br = browser()
        req = Request(
            endpoint_url,
            headers=headers,
            data=json.dumps(data),
            method="POST",
            timeout=self.timeout,
        )
        res = br.open(req)
        article = json.loads(res.read())
        new_soup = self.soup(article["content"])
        # clear out existing partial content
        for c in list(content_ele.children):
            c.extract()  # use extract() instead of decompose() because of strings
        content_ele.append(new_soup.body)
        return str(soup)

    def populate_article_metadata(self, article, soup, _):
        mod_date_ele = soup.find(attrs={"data-mod-date": True})
        post_date = self.parse_date(mod_date_ele["data-mod-date"])
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
            issue_url = _issue_url
            mobj = re.search(r"archive-toc/(?P<issue>(BR)?\d+)\b", issue_url)
            if mobj:
                self.cover_url = f'https://hbr.org/resources/images/covers/{mobj.group("issue")}_500.png'

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
            feeds.setdefault(section_title, []).append(
                {"title": title, "url": url, "description": article_desc}
            )
        return feeds.items()
