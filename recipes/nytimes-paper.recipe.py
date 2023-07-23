#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: GPLv3 Copyright: 2018, Kovid Goyal <kovid at kovidgoyal.net>

# Original at https://github.com/kovidgoyal/calibre/blob/8597c509ed04f7435246f84ddf3e10a0227ccc7e/recipes/nytimes_sub.recipe

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import json
import os
import re
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title
from nyt import NYTRecipe

from calibre import strftime
from calibre.web.feeds.news import BasicNewsRecipe

_name = "New York Times (Print)"


class NewYorkTimesPrint(NYTRecipe, BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = "Today's New York Times https://www.nytimes.com/section/todayspaper"
    encoding = "utf-8"
    __author__ = "Kovid Goyal"
    language = "en"
    publication_type = "newspaper"
    masthead_url = "https://mwcm.nyt.com/.resources/mkt-wcm/dist/libs/assets/img/logo-nyt-header.svg"

    INDEX = "https://www.nytimes.com/section/todayspaper"

    remove_attributes = ["style", "font"]
    remove_tags_before = [dict(id="story")]
    remove_tags_after = [dict(id="story")]

    remove_tags = [
        dict(
            id=["in-story-masthead", "sponsor-wrapper", "top-wrapper", "bottom-wrapper"]
        ),
        dict(
            class_=[
                "NYTAppHideMasthead",
                "live-blog-meta",
                "css-13xl2ke",  # nyt logo in live-blog-byline
                "css-8r08w0",  # after storyline-context-container
            ]
        ),
        dict(role=["toolbar", "navigation", "contentinfo"]),
        dict(name=["script", "noscript", "style", "button", "svg"]),
    ]

    extra_css = """
    .live-blog-reporter-update {
        font-size: 0.8rem;
        padding: 0.2rem;
        margin-bottom: 0.5rem;
    }
    [data-testid="live-blog-byline"] {
        color: #444;
        font-style: italic;
    }
    [datetime] > span {
        margin-right: 0.6rem;
    }
    picture img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    [aria-label="media"] {
        font-size: 0.8rem;
        display: block;
        margin-bottom: 1rem;
    }
    [role="complementary"] {
        font-size: 0.8rem;
        padding: 0.2rem;
    }
    [role="complementary"] h2 {
        font-size: 0.85rem;
        margin-bottom: 0.2rem;
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
    .article-img .caption { font-size: 0.8rem; }
    div.summary { font-size: 1.2rem; margin: 1rem 0; }
    """

    def read_todays_paper(self):
        try:
            soup = self.index_to_soup(self.INDEX)
        except Exception as err:
            if getattr(err, "code", None) == 404:
                try:
                    soup = self.index_to_soup(
                        strftime(
                            "https://www.nytimes.com/issue/todayspaper/%Y/%m/%d/todays-new-york-times"
                        )
                    )
                except Exception as err:
                    if getattr(err, "code", None) == 404:
                        dt = datetime.datetime.today() - datetime.timedelta(days=1)
                        soup = self.index_to_soup(
                            dt.strftime(
                                "https://www.nytimes.com/issue/todayspaper/%Y/%m/%d/todays-new-york-times"
                            )
                        )
                    else:
                        raise
            else:
                raise
        return soup

    def read_nyt_metadata(self):
        soup = self.read_todays_paper()
        pdate = soup.find("meta", attrs={"name": "pdate", "content": True})["content"]
        date = self.parse_date(pdate)
        self.cover_url = (
            "https://static01.nyt.com/images/{}/nytfrontpage/scan.jpg".format(
                date.strftime("%Y/%m/%d")
            )
        )
        # self.timefmt = strftime(" [%d %b, %Y]", date)
        self.pub_date = date
        self.title = format_title(_name, date)
        return soup

    def parse_index(self):
        soup = self.read_nyt_metadata()
        script = soup.findAll(
            "script", text=lambda x: x and "window.__preloadedData" in x
        )[0]
        script = type("")(script)
        json_data = script[script.find("{") : script.rfind(";")].strip().rstrip(";")
        data = json.loads(json_data.replace(":undefined", ":null"))["initialState"]
        containers, sections = {}, {}
        article_map = {}
        gc_pat = re.compile(r"groupings.(\d+).containers.(\d+)")
        pat = re.compile(r"groupings.(\d+).containers.(\d+).relations.(\d+)")
        for key in data:
            if "Article" in key:
                adata = data[key]
                if adata.get("__typename") == "Article":
                    url = adata.get("url")
                    summary = adata.get("summary")
                    headline = adata.get("headline")
                    if url and headline:
                        title = data[headline["id"]]["default"]
                        article_map[adata["id"]] = {
                            "title": title,
                            "url": url,
                            "description": summary or "",
                        }
            elif "Legacy" in key:
                sdata = data[key]
                tname = sdata.get("__typename")
                if tname == "LegacyCollectionContainer":
                    m = gc_pat.search(key)
                    containers[int(m.group(2))] = sdata["label"] or sdata["name"]
                elif tname == "LegacyCollectionRelation":
                    m = pat.search(key)
                    grouping, container, relation = map(int, m.groups())
                    asset = sdata["asset"]
                    if asset and asset["typename"] == "Article" and grouping == 0:
                        if container not in sections:
                            sections[container] = []
                        sections[container].append(asset["id"].split(":", 1)[1])

        feeds = []
        for container_num in sorted(containers):
            section_title = containers[container_num]
            if container_num in sections:
                articles = sections[container_num]
                if articles:
                    feeds.append((section_title, []))
                    for artid in articles:
                        if artid in article_map:
                            art = article_map[artid]
                            feeds[-1][1].append(art)

        def skey(x):
            name = x[0].strip()
            if name == "The Front Page":
                return 0, ""
            return 1, name.lower()

        feeds.sort(key=skey)
        for section, articles in feeds:
            self.log("\n" + section)
            for article in articles:
                self.log(article["title"] + " - " + article["url"])
        return feeds
