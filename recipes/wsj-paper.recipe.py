# vim:fileencoding=utf-8
# License: GPLv3 Copyright: 2016, Kovid Goyal <kovid at kovidgoyal.net>

# Original at https://github.com/kovidgoyal/calibre/blob/9a6671c3ce0669590b0b658d23928bd9aa21cb5b/recipes/wsj_free.recipe

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import random
import re
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

from calibre.web.feeds.news import BasicNewsRecipe, classes
from calibre.ebooks.BeautifulSoup import BeautifulSoup


_name = "Wall Street Journal (Print)"


class WSJ(BasicNewsRecipe):
    title = _name
    __author__ = "Kovid Goyal"
    description = "Print edition of the WSJ https://www.wsj.com/print-edition/today"
    language = "en"
    masthead_url = (
        "https://vir.wsj.net/fp/assets/webpack4/img/wsj-logo-small.1e2f0a7a.svg"
    )

    compress_news_images = True
    compress_news_images_auto_size = 7
    scale_news_images = (800, 1200)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images

    no_stylesheets = True
    ignore_duplicate_articles = {"url"}
    remove_attributes = ["style", "height", "width"]
    needs_subscription = False

    timefmt = ""
    pub_date = None  # custom publication date

    extra_css = """
        .wsj-article-headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
        .sub-head { font-size: 1.2rem; font-style: italic; margin-bottom: 0.5rem; font-weight: normal; }
        .bylineWrap { margin-top: 0.5rem; margin-bottom: 1rem; font-weight: bold; color: #444;  }
        .image-container img, .media-object img {
            display: block; margin-bottom: 0.3rem;
            max-width: 100%; height: auto;
            box-sizing: border-box;
        }
        .imageCaption { font-size: 0.8rem; }
    """

    keep_only_tags = [
        classes("wsj-article-headline-wrap articleLead bylineWrap bigTop-hero"),
        dict(name="section", attrs={"subscriptions-section": "content"}),
    ]

    remove_tags = [
        classes(
            "wsj-ad newsletter-inset media-object-video media-object-podcast "
            "podcast--iframe dynamic-inset-overflow-button columnist_mini"
        ),
        dict(name="amp-iframe"),  # interactive graphics
    ]

    def publication_date(self):
        return self.pub_date

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        # find pub date
        mod_date_ele = soup.find(
            "meta", attrs={"name": "article.updated"}
        ) or soup.find("meta", itemprop="dateModified")
        post_mod_date = datetime.strptime(
            mod_date_ele["content"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).replace(tzinfo=timezone.utc)
        if not self.pub_date or post_mod_date > self.pub_date:
            self.pub_date = post_mod_date

        for h in soup.select("[subscriptions-section=content] h6"):
            # headers inside content
            h.name = "h3"
        for by in soup.find_all(**classes("byline")):
            for p in by.find_all("p"):
                p.name = "span"
        for img in soup.find_all("amp-img"):
            if img["src"] == "https://s.wsj.net/img/meta/wsj-social-share.png":
                img.decompose()
                continue
            img.name = "img"
        return str(soup)

    def get_browser(self, *a, **kw):
        br = BasicNewsRecipe.get_browser(self, *a, **kw)
        br.set_cookie("wsjregion", "na,us", ".wsj.com")
        br.set_cookie("gdprApplies", "false", ".wsj.com")
        br.set_cookie("ccpaApplies", "false", ".wsj.com")
        return br

    def _get_page_info(self, soup):
        for script in soup.find_all("script"):
            if not script.contents:
                continue
            if not script.contents[0].strip().startswith("window.__STATE__"):
                continue
            index_js = re.sub(
                r"window.__STATE__\s*=\s*", "", script.contents[0].strip()
            )
            if index_js.endswith(";"):
                index_js = index_js[:-1]
            try:
                info = json.loads(index_js)
                return info
            except json.JSONDecodeError:
                self.log.exception("Unable to parse __STATE__")
        return None

    def _do_wait(self, message):
        if message:
            self.log.warn(message)
        pause = random.choice((1, 1.5, 2, 2.5))
        self.log.warn(f"Retrying after {pause} seconds")
        time.sleep(pause)

    def parse_index(self):
        max_retry_attempts = 3
        sections = []

        for d in range(3):
            issue_date = datetime.today() - timedelta(days=d)
            issue_url = (
                f'https://www.wsj.com/print-edition/{issue_date.strftime("%Y%m%d")}'
            )
            soup = self.index_to_soup(issue_url)
            info = self._get_page_info(soup)

            for k, v in info["data"].items():
                if k != f'rss_subnav_collection_{issue_date.strftime("%Y%m%d")}':
                    continue
                for s in v["data"]["data"]["list"]:
                    if s.get("id") and s.get("label"):
                        sections.append(s)
            if sections:
                self.title = f"{_name}: {issue_date:%-d %b, %Y}"
                break

        if not sections:
            for attempt in range(max_retry_attempts + 1):
                # try default redirect
                soup = self.index_to_soup("https://www.wsj.com/print-edition/today")
                info = self._get_page_info(soup)
                for k, v in info["data"].items():
                    if not k.startswith("rss_subnav_collection_"):
                        continue
                    issue_date = datetime.strptime(v["data"]["id"], "%Y%m%d")
                    self.title = f"{_name}: {issue_date:%-d %b, %Y}"
                    self.log(
                        f'Issue date is: {issue_date:%Y%m%d}, title is "{self.title}"'
                    )
                    for s in v["data"]["data"]["list"]:
                        if s.get("id") and s.get("label"):
                            sections.append(s)
                    break
                if sections:
                    break
                else:
                    if attempt < max_retry_attempts:
                        self._do_wait("Unable to determine issue date")

        if not sections:
            self.abort_recipe_processing("Unable to find issue.")

        section_feeds = OrderedDict()
        for section in sections:
            section_url = f'https://www.wsj.com/print-edition/{issue_date.strftime("%Y%m%d")}/{section["id"]}'
            for attempt in range(max_retry_attempts + 1):
                section_soup = self.index_to_soup(section_url)
                section_info = self._get_page_info(section_soup)
                section_articles = []
                for k, v in section_info["data"].items():
                    if (
                        k
                        != f'rss_collection_{{"section":"{section["id"]}","date":"{issue_date.strftime("%Y%m%d")}"}}'
                    ):
                        continue
                    for i in v["data"]["data"]["list"]:
                        if not i.get("url"):
                            continue
                        section_articles.append(
                            {
                                "url": i["url"].replace("/articles/", "/amp/articles/"),
                                "title": i["headline"],
                                "description": i["summary"],
                            }
                        )
                    break
                if section_articles:
                    section_feeds[section["label"]] = section_articles
                    break
                else:
                    if attempt < max_retry_attempts:
                        self._do_wait(f'No articles found in "{section_url}".')
                    else:
                        self.log.warn(f'Unable to get articles in "{section_url}"')

        return section_feeds.items()
