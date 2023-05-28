#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: GPLv3 Copyright: 2015, Kovid Goyal <kovid at kovidgoyal.net>
from __future__ import unicode_literals

import json
import os
import re
import sys
from datetime import datetime, timezone

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe


def embed_image(soup, block):
    caption = block.get("captionText", "")
    if caption and block.get("attributionText", "").strip():
        caption += " (" + block["attributionText"].strip() + ")"

    container = soup.new_tag("div", attrs={"class": "article-img"})
    img = soup.new_tag("img", src=block["url"])
    container.append(img)
    cap = soup.new_tag("div", attrs={"class": "caption"})
    cap.append(BeautifulSoup(caption))
    container.append(cap)
    return container


def json_to_html(raw):
    data = json.loads(raw)

    # open('/t/p.json', 'w').write(json.dumps(data, indent=2))
    data = sorted(
        (v["data"] for v in data["props"]["pageProps"]["urqlState"].values()), key=len
    )[-1]
    article = json.loads(data)["article"]

    new_soup = BeautifulSoup(
        """<html><head></head><body><main id="from-json-by-calibre"></main></body></html>"""
    )
    if article.get("issue"):
        issue_ele = new_soup.new_tag("div", attrs={"class": "issue"})
        issue_ele.append(article["issue"]["issueName"])
        new_soup.main.append(issue_ele)

    headline = new_soup.new_tag("h1", attrs={"class": "headline"})
    headline.append(BeautifulSoup(article["title"]))
    new_soup.main.append(headline)

    subheadline = new_soup.new_tag("h2", attrs={"class": "sub-headline"})
    subheadline.append(BeautifulSoup(article["dek"]))
    new_soup.main.append(subheadline)

    meta = new_soup.new_tag("div", attrs={"class": "article-meta"})
    authors = [x["displayName"] for x in article["authors"]]
    author_ele = new_soup.new_tag("span", attrs={"class": "author"})
    author_ele.append(", ".join(authors))
    meta.append(author_ele)

    # Example: 2022-04-04T10:00:00Z
    published_date = datetime.strptime(
        article["datePublished"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc)
    pub_ele = new_soup.new_tag("span", attrs={"class": "published-dt"})
    pub_ele["data-published"] = f"{published_date:%Y-%m-%dT%H:%M:%SZ}"
    pub_ele.append(f"{published_date:%-I:%M%p, %-d %B, %Y}")
    meta.append(pub_ele)
    if article.get("dateModified"):
        modified_date = datetime.strptime(
            article["dateModified"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
        upd_ele = new_soup.new_tag("span", attrs={"class": "modified-dt"})
        upd_ele["data-modified"] = f"{modified_date:%Y-%m-%dT%H:%M:%SZ}"
        upd_ele.append(f"Updated {modified_date:%-I.%M%p, %-d %B, %Y}")
        meta.append(upd_ele)

    new_soup.main.append(meta)

    if article.get("leadArt") and "image" in article["leadArt"]:
        new_soup.main.append(embed_image(new_soup, article["leadArt"]["image"]))
    for item in article["content"]:
        tn = item.get("__typename", "")
        if tn.endswith("Image"):
            new_soup.main.append(embed_image(new_soup, item))
            continue
        content_html = item.get("innerHtml")
        if (
            (not content_html)
            or "</iframe>" in content_html
            or "newsletters/sign-up" in content_html
        ):
            continue
        if tn == "ArticleHeading":
            tag_name = "h2"
            mobj = re.match(r"HED(?P<level>\d)", item.get("headingSubtype", ""))
            if mobj:
                tag_name = f'h{mobj.group("level")}'
            header_ele = new_soup.new_tag(tag_name)
            header_ele.append(BeautifulSoup(content_html))
            new_soup.main.append(header_ele)
            continue
        if tn == "ArticlePullquote":
            container_ele = new_soup.new_tag("blockquote")
            container_ele.append(BeautifulSoup(content_html))
            new_soup.main.append(container_ele)
            continue
        if tn == "ArticleRelatedContentLink":
            container_ele = new_soup.new_tag("div", attrs={"class": "related-content"})
            container_ele.append(BeautifulSoup(content_html))
            new_soup.main.append(container_ele)
            continue
        content_ele = new_soup.new_tag(item.get("tagName", "p").lower())
        content_ele.append(BeautifulSoup(content_html))
        new_soup.main.append(content_ele)
    return str(new_soup)


class NoJSON(ValueError):
    pass


def extract_html(soup):
    script = soup.findAll("script", id="__NEXT_DATA__")
    if not script:
        raise NoJSON("No script tag with JSON data found")
    raw = script[0].contents[0]
    return json_to_html(raw)


_name = "The Atlantic Magazine"


class TheAtlanticMagazine(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = "Current affairs and politics focused on the US https://www.theatlantic.com/magazine/"
    INDEX = "https://www.theatlantic.com/magazine/"

    __author__ = "Kovid Goyal"
    language = "en"
    encoding = "utf-8"

    masthead_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/The_Atlantic_magazine_logo.svg/1200px-The_Atlantic_magazine_logo.svg.png"

    publication_type = "magazine"
    compress_news_images_auto_size = 12
    remove_empty_feeds = True
    remove_attributes = ["style"]
    remove_tags = [dict(class_=["related-content"])]

    extra_css = """
    .issue { font-weight: bold; margin-bottom: 0.2rem; }
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .sub-headline { font-size: 1.2rem; font-style: italic; font-weight: normal; margin-bottom: 0.5rem; }
    .article-meta {  margin-top: 0.5rem; margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; display: inline-block; }
    .article-meta .published-dt { display: inline-block; margin-left: 0.5rem; }
    .article-meta .modified-dt { display: block; margin-top: 0.2rem; font-style: italic; }
    .caption { font-size: 0.8rem; margin-top: 0.2rem; margin-bottom: 0.5rem; }
    .article-img { display: block; max-width: 100%; height: auto; }
    h3 span.smallcaps { font-weight: bold; }
    p span.smallcaps { text-transform: uppercase; }
    blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    div.related-content { margin-left: 0.5rem; color: #444; font-style: italic; }
    """

    def get_browser(self):
        br = BasicNewsRecipe.get_browser(self)
        br.set_cookie("inEuropeanUnion", "0", ".theatlantic.com")
        return br

    def preprocess_raw_html(self, raw_html, url):
        try:
            return extract_html(self.index_to_soup(raw_html))
        except NoJSON:
            self.log.warn("No JSON found in: {} falling back to HTML".format(url))
        except Exception:
            self.log.exception(
                "Failed to extract JSON data from: {} falling back to HTML".format(url)
            )
        return raw_html

    def preprocess_html(self, soup):
        for img in soup.findAll("img", attrs={"data-srcset": True}):
            data_srcset = img["data-srcset"]
            if "," in data_srcset:
                img["src"] = data_srcset.split(",")[0]
            else:
                img["src"] = data_srcset.split()[0]
        for img in soup.findAll("img", attrs={"data-src": True}):
            img["src"] = img["data-src"]
        return soup

    def populate_article_metadata(self, article, soup, _):
        headline = soup.find("h1", attrs={"class": "headline"})
        if headline:
            # reset the title because the title in the rss feed can contain tags, e.g. <em>
            article.title = headline.text

        # modified = soup.find(attrs={"data-modified": True})
        # if modified:
        #     modified_date = datetime.strptime(
        #         modified["data-modified"], "%Y-%m-%dT%H:%M:%SZ"
        #     ).replace(tzinfo=timezone.utc)
        #     if (not self.pub_date) or modified_date > self.pub_date:
        #         self.pub_date = modified_date

        published = soup.find(attrs={"data-published": True})
        if published:
            published_date = datetime.strptime(
                published["data-published"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
            article.utctime = published_date
            if (not self.pub_date) or published_date > self.pub_date:
                self.pub_date = published_date

    def parse_index(self):
        soup = self.index_to_soup(self.INDEX)
        script = soup.findAll("script", id="__NEXT_DATA__")
        if not script:
            raise NoJSON("No script tag with JSON data found")
        data = json.loads(script[0].contents[0])
        issue = None
        for t in (
            data.get("props", {}).get("pageProps", {}).get("urqlState", {}).values()
        ):
            d = json.loads(t["data"])
            if not d.get("latestMagazineIssue"):
                continue
            issue = d["latestMagazineIssue"]
        self.title = f'{_name}: {issue["displayName"]}'
        self.cover_url = (
            issue["cover"]["srcSet"].split(",")[-1].strip().split(" ")[0].strip()
        )
        feeds = []
        for section in issue["toc"]["sections"]:
            articles = [
                {"url": i["url"], "title": i["title"], "description": i["dek"]}
                for i in section.get("items", [])
            ]
            feeds.append((section["title"], articles))

        return feeds
