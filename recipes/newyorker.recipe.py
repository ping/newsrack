#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: GPLv3 Copyright: 2016, Kovid Goyal <kovid at kovidgoyal.net>

# Original from https://github.com/kovidgoyal/calibre/blob/29cd8d64ea71595da8afdaec9b44e7100bff829a/recipes/new_yorker.recipe
from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
import json
from datetime import datetime, timezone

from calibre import browser
from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe, classes, prefixed_classes


def absurl(x):
    if x.startswith("/") and not x.startswith("//"):
        x = "https://www.newyorker.com" + x
    return x


_name = "New Yorker"


class NewYorker(BasicNewsRecipe):

    title = _name
    description = (
        "Articles of the week's New Yorker magazine https://www.newyorker.com/"
    )

    url_list = []
    language = "en"
    __author__ = "Kovid Goyal"
    encoding = "utf-8"
    no_stylesheets = True
    remove_javascript = True
    remove_empty_feeds = True
    masthead_url = "https://www.newyorker.com/verso/static/the-new-yorker/assets/logo-seo.38af6104b89a736857892504d04dbb9a3a56e570.png"

    compress_news_images = True
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    timeout = 20
    timefmt = ""
    pub_date = None  # custom publication date

    extra_css = """
        [data-testid="message-banner"] { font-size: 0.8rem; }
        [data-testid="message-banner"] h4 { margin-bottom: 0.2rem; }
        .headline { font-size: 1.8rem; margin-bottom: 0.5rem; }
        .sub-headline { font-size: 1.2rem; margin-top: 0; margin-bottom: 0.5rem; font-style: italic; }
        .article-meta {  margin-top: 1rem; margin-bottom: 1rem; }
        .article-meta .author { font-weight: bold; color: #444; display: inline-block; }
        .article-meta .published-dt { display: inline-block; margin-left: 0.5rem; }
        .article-meta .modified-dt { display: block; margin-top: 0.2rem; font-style: italic; }
        .responsive-asset img { max-width: 100%; height: auto; }
        h3 { margin-bottom: 6px; }
        .caption { font-size: 0.8rem; font-weight: normal; }
    """
    keep_only_tags = [
        prefixed_classes("IframeEmbedWrapper-sc-"),
        dict(class_="og"),
        dict(attrs={"data-attribute-verso-pattern": "article-body"}),
        dict(
            attrs={
                "data-testid": [
                    # "ContentHeaderRubric",
                    # "SplitScreenContentHeaderWrapper",
                    "MagazineDisclaimerWrapper",
                ]
            }
        ),
    ]

    remove_tags = [
        classes("social-icons"),
        dict(childtypes="iframe"),
        dict(name=["button"]),
    ]
    remove_attributes = ["style"]

    def publication_date(self):
        return self.pub_date

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        for script in soup.find_all(name="script", type="application/ld+json"):
            info = json.loads(script.contents[0])
            if not info.get("headline"):
                continue

            h1 = soup.new_tag("h1", attrs={"class": "og headline"})
            h1.append(info["headline"])
            soup.body.insert(0, h1)

            meta = soup.new_tag("div", attrs={"class": "og article-meta"})
            authors = [a["name"] for a in info.get("author", [])]
            if authors:
                author_ele = soup.new_tag("span", attrs={"class": "author"})
                author_ele.append(", ".join(authors))
                meta.append(author_ele)

            pub_date = datetime.fromisoformat(info["datePublished"])
            pub_ele = soup.new_tag("span", attrs={"class": "published-dt"})
            pub_ele["datePublished"] = info["datePublished"]
            pub_ele.append(f"{pub_date:%-d %B, %Y}")
            meta.append(pub_ele)

            if info.get("dateModified"):
                mod_date = datetime.fromisoformat(info["dateModified"])
                mod_ele = soup.new_tag("span", attrs={"class": "modified-dt"})
                mod_ele["dateModified"] = info["dateModified"]
                mod_ele.append(f"Updated {mod_date:%-I:%M%p %-d %B, %Y}")
                meta.append(mod_ele)
            h1.insert_after(meta)

            if info.get("description"):
                subheadline = soup.new_tag("div", attrs={"class": "og sub-headline"})
                subheadline.append(info["description"])
                h1.insert_after(subheadline)

            break

        return str(soup)

    def preprocess_html(self, soup):
        for noscript in soup.findAll("noscript"):
            noscript.name = "div"

        # rearrange page elements
        article_body = soup.find(attrs={"data-attribute-verso-pattern": "article-body"})
        rubric = soup.find(attrs={"data-testid": "ContentHeaderRubric"})
        if rubric:
            rubric = rubric.extract()
            article_body.insert_before(rubric)
        header = soup.find(attrs={"data-testid": "SplitScreenContentHeaderWrapper"})
        if header:
            header = header.extract()
            article_body.insert_before(header)
        return soup

    def populate_article_metadata(self, article, soup, _):
        pub_ele = soup.find(attrs={"datepublished": True})
        if pub_ele:
            pub_date = datetime.fromisoformat(pub_ele["datepublished"])
            pub_date_utc = pub_date.astimezone(timezone.utc)
            article.localtime = pub_date
            article.utctime = pub_date_utc
            if not self.pub_date or pub_date_utc > self.pub_date:
                self.pub_date = pub_date_utc

        mod_ele = soup.find(attrs={"datemodified": True})
        if mod_ele:
            mod_date = datetime.fromisoformat(mod_ele["datemodified"])
            mod_date_utc = mod_date.astimezone(timezone.utc)
            if not self.pub_date or mod_date_utc > self.pub_date:
                self.pub_date = mod_date_utc

    def parse_index(self):

        # Get cover

        cover_soup = self.index_to_soup("https://www.newyorker.com/archive")
        cover_img = cover_soup.find(
            attrs={"class": lambda x: x and "MagazineSection__cover___" in x}
        )
        if cover_img is not None:
            cover_img = cover_img.find("img")
            if cover_img is not None:
                self.cover_url = cover_img.get("src")
                try:
                    # the src original resolution w_280 was too low, replace w_280 with w_560
                    cover_url_width_index = self.cover_url.find("w_")
                    old_width = self.cover_url[
                        cover_url_width_index : cover_url_width_index + 5
                    ]
                    self.cover_url = self.cover_url.replace(old_width, "w_560")
                except Exception:
                    self.log.warning(
                        "Failed enlarging cover img, using the original one"
                    )

                self.log("Found cover:", self.cover_url)

        # Get content

        soup = self.index_to_soup("https://www.newyorker.com/magazine?intcid=magazine")
        header_title = soup.select_one("header h2")
        if header_title:
            self.title = f"{_name}: {self.tag_to_string(header_title)}"

        stories = OrderedDict()  # So we can list sections in order

        # Iterate sections of content

        for section_soup in soup.findAll(
            attrs={"class": lambda x: x and "MagazinePageSection__section___21cc7" in x}
        ):
            section = section_soup.find("h2").text
            self.log("Found section:", section)

            # Iterate stories in section

            is_mail_section = section == "Mail"

            if is_mail_section:
                cname = "Link__link___"
            else:
                cname = "River__riverItemContent___"

            for story in section_soup.findAll(
                attrs={"class": lambda x: x and cname in x}
            ):
                desc = ""
                if is_mail_section:
                    title = story.text
                    url = absurl(story["href"])
                else:
                    h4 = story.find("h4")
                    title = self.tag_to_string(h4)
                    a = story.find("h4").parent
                    url = absurl(a["href"])
                    # Get description
                    body = story.find(attrs={"class": "River__dek___CayIg"})
                    if body is not None:
                        desc = body.contents[0]

                self.log("Found article:", title)
                self.log("\t" + url)
                self.log("\t" + desc)
                self.log("")

                if section not in stories:
                    stories[section] = []
                stories[section].append(
                    {"title": title, "url": url, "description": desc}
                )

        return [(k, stories[k]) for k, v in stories.items()]

    # The New Yorker changes the content it delivers based on cookies, so the
    # following ensures that we send no cookies
    def get_browser(self, *args, **kwargs):
        return self

    def clone_browser(self, *args, **kwargs):
        return self.get_browser()

    def open_novisit(self, *args, **kwargs):
        br = browser()
        return br.open_novisit(*args, **kwargs)

    open = open_novisit
