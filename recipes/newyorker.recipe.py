#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: GPLv3 Copyright: 2016, Kovid Goyal <kovid at kovidgoyal.net>

# Original from https://github.com/kovidgoyal/calibre/blob/29cd8d64ea71595da8afdaec9b44e7100bff829a/recipes/new_yorker.recipe
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre import browser
from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe, classes, prefixed_classes
from calibre.ebooks.markdown import Markdown


def absurl(x):
    if x.startswith("/") and not x.startswith("//"):
        x = "https://www.newyorker.com" + x
    return x


_name = "New Yorker"


class NewYorker(BasicNewsrackRecipe, BasicNewsRecipe):

    title = _name
    description = (
        "Articles of the week's New Yorker magazine https://www.newyorker.com/magazine"
    )

    url_list = []
    language = "en"
    __author__ = "Kovid Goyal"
    encoding = "utf-8"
    remove_empty_feeds = True
    masthead_url = "https://www.newyorker.com/verso/static/the-new-yorker/assets/logo-seo.38af6104b89a736857892504d04dbb9a3a56e570.png"

    compress_news_images_auto_size = 10

    extra_css = """
        [data-testid="message-banner"] { font-size: 0.8rem; }
        [data-testid="message-banner"] h4 { margin-bottom: 0.2rem; }
        .headline { font-size: 1.8rem; margin-bottom: 0.5rem; }
        .sub-headline { font-size: 1.2rem; margin-top: 0; margin-bottom: 0.5rem; font-style: italic; }
        .article-meta {  margin-top: 1rem; margin-bottom: 1rem; }
        .article-meta .author { font-weight: bold; color: #444; display: inline-block; }
        .article-meta .published-dt { display: inline-block; margin-left: 0.5rem; }
        .article-meta .modified-dt { display: block; margin-top: 0.2rem; font-style: italic; }
        .responsive-asset img, .cust-lightbox-img img { max-width: 100%; height: auto; display: block; }
        .cust-lightbox-img .caption { display: block; margin-top: 0.3rem; }
        h3 { margin-bottom: 6px; }
        .caption { font-size: 0.8rem; font-weight: normal; }
    """
    keep_only_tags = [
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
        prefixed_classes(
            "ResponsiveCartoonLinkButtonWrapper- IframeEmbedWrapper- GenericCalloutWrapper-"
        ),
        dict(childtypes="iframe"),
        dict(name=["button"]),
    ]
    remove_attributes = ["style", "sizes", "data-event-click"]

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)

        preload_state = {}
        preload_script_eles = [
            script
            for script in soup.find_all(name="script", type="text/javascript")
            if script.contents
            and script.contents[0].strip().startswith("window.__PRELOADED_STATE__ = ")
        ]
        if preload_script_eles:
            preload_state_js = re.sub(
                r"window.__PRELOADED_STATE__\s*=\s*",
                "",
                preload_script_eles[0].contents[0].strip(),
            )
            if preload_state_js.endswith(";"):
                preload_state_js = preload_state_js[:-1]
            try:
                preload_state = json.loads(preload_state_js)
            except json.JSONDecodeError:
                self.log.exception("Unable to parse window.__PRELOADED_STATE__")

        images = []
        if preload_state:
            images = (
                preload_state.get("transformed", {})
                .get("article", {})
                .get("lightboxImages", [])
            )
        # grab interactive images
        for body_ele in (
            preload_state.get("transformed", {}).get("article", {}).get("body", [])
        ):
            try:
                if not type(body_ele) is list:
                    continue
                if not body_ele[0] == "inline-embed":
                    continue
                interactive_img = body_ele[2][1].get("props", {}).get("image", {})
                if interactive_img:
                    images.append(interactive_img)
            except Exception as err:
                self.log.warning(f"Unable to get interactive elements: {err}")
        for script in soup.find_all(name="script", type="application/ld+json"):
            info = json.loads(script.contents[0])
            if not info.get("headline"):
                continue
            interactive_container = soup.body.find(id="___gatsby")
            try:
                if interactive_container:
                    interactive_container.clear()
                    md = Markdown()
                    article_body = info["articleBody"]
                    # replace line breaks
                    article_body = re.sub(r"\\\n", "<br/>", article_body)
                    # replace +++ md
                    article_body = re.sub(r"\+\+\+.*?\n", "", article_body)
                    article_body = re.sub(r"{: .+}\n", "", article_body)
                    # replace image markdown with image markup
                    if images:
                        image_markdowns = re.findall(
                            r"\[#(?P<md_type>[a-z]+): /(?P<md_path>[a-z]+)/(?P<image_id>[a-f0-9]+)\]",
                            info["articleBody"],
                        )
                        for md_type, md_path, image_id in image_markdowns:
                            image_source = [
                                img for img in images if img.get("id", "") == image_id
                            ]
                            if image_source:
                                image_source = image_source[0]
                                image_url = (
                                    image_source.get("sources", {})
                                    .get(
                                        "md", {}
                                    )  # other sizes as well, e.g. "sm" or "lg"
                                    .get("url", "")
                                )
                                if image_url:
                                    caption_html = '<span class="caption">'
                                    if image_source.get("dangerousCaption"):
                                        caption_html += image_source["dangerousCaption"]
                                    if image_source.get("dangerousCredit"):
                                        caption_html += (
                                            f' {image_source["dangerousCredit"]}'
                                        )
                                    caption_html += "</span>"
                                    image_html = f'<p class="cust-lightbox-img"><img src="{image_url}">{caption_html}</p>'
                                    article_body = article_body.replace(
                                        f"[#{md_type}: /{md_path}/{image_id}]",
                                        image_html,
                                    )

                    interactive_container.append(
                        BeautifulSoup(md.convert(article_body))
                    )
                    interactive_container["class"] = "og"
            except Exception as e:
                self.log.warning(f"Unable to convert interactive article: {e}")

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

            if info.get("image"):
                lede_img_container = soup.new_tag(
                    "div", attrs={"class": "og responsive-asset"}
                )
                lede_image = soup.new_tag("img", attrs={"src": info["image"][-1]})
                lede_img_container.append(lede_image)
                meta.insert_after(lede_img_container)

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
                    # the src original resolution w_280 was too low, replace w_280 with w_960
                    self.cover_url = re.sub(r"\bw_\d+\b", "w_960", self.cover_url)
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
