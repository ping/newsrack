#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Original at https://github.com/kovidgoyal/calibre/blob/0f2e921ff1d71cb9b8d29fc5393771861a465f13/recipes/asahi_shimbun_en.recipe
"""
https://www.asahi.com/ajw/
"""


__license__ = "GPL v3"
__copyright__ = "2022, Albert Aparicio Isarn <aaparicio at posteo.net>"

import os
import sys

from datetime import datetime, timezone, timedelta

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Asahi Shimbun"


class AsahiShimbunEnglishNews(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "Albert Aparicio Isarn"

    description = (
        "The Asahi Shimbun is widely regarded for its journalism as the most respected daily newspaper in Japan."
        " The English version offers selected articles from the vernacular Asahi Shimbun, as well as extensive"
        " coverage of cool Japan,focusing on manga, travel and other timely news. https://www.asahi.com/ajw/"
    )
    publisher = "The Asahi Shimbun Company"
    publication_type = "newspaper"
    category = "news, japan"
    language = "en_JP"

    index = "https://www.asahi.com"
    masthead_url = "https://p.potaufeu.asahi.com/ajw/css/images/en_logo@2x.png"

    oldest_article = 1
    max_articles_per_feed = 25
    ignore_duplicate_articles = {"url"}

    compress_news_images_auto_size = 10
    timeout = 90

    cutoff_date_utc = datetime.today().replace(tzinfo=timezone.utc) - timedelta(
        days=oldest_article
    )
    cutoff_date_jst = cutoff_date_utc.astimezone(timezone(timedelta(hours=9))).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    remove_tags_before = {"id": "MainInner"}
    remove_tags_after = {"class": "ArticleText"}
    remove_tags = [{"name": "div", "class": "SnsUtilityArea"}]

    extra_css = """
    .ArticleTitle p.EnArticleName {
        font-weight: bold; color: #444; display: block;
        margin-top: 0.5rem; margin-bottom: 0.25rem;
    }
    .ArticleTitle p.EnLastUpdated { margin-top: 0; margin-bottom: 0.5rem; }
    div.Image img, div.insert_image_full img { max-width: 100%; height: auto; }
    div.Image .Caption, div.insert_image_full div > div { display: block; font-size: 0.8rem; margin-top: 0.2rem; }
    """

    def populate_article_metadata(self, article, soup, _):
        last_update_ele = soup.find(name="p", attrs={"class": "EnLastUpdated"})
        if last_update_ele:
            post_date = datetime.strptime(
                self.tag_to_string(last_update_ele), "%B %d, %Y at %H:%M JST"
            ).replace(tzinfo=timezone(timedelta(hours=9)))
            post_date_utc = post_date.astimezone(timezone.utc)
            if (
                not self.pub_date or post_date_utc > self.pub_date
            ) and post_date_utc < datetime.utcnow().replace(
                tzinfo=timezone.utc
            ):  # because asahi has wrongly dated articles far into the future
                self.pub_date = post_date_utc
                self.title = format_title(_name, post_date)

    def preprocess_html(self, soup):
        gallery = soup.find(name="ul", attrs={"class": "Thum"})
        if gallery:
            for img in gallery.find_all(name="img"):
                img_container = soup.new_tag("p")
                img_container.append(img)
                gallery.parent.append(img_container)
            gallery.decompose()
        return soup

    def get_whats_new(self):
        soup = self.index_to_soup(self.index + "/ajw/new")
        news_section = soup.find("div", attrs={"class": "specialList"})

        new_news = []

        for item in news_section.findAll("li"):
            date_string = item.find("p", attrs={"class": "date"}).next
            post_date_jst = datetime.strptime(date_string.strip(), "%B %d, %Y").replace(
                tzinfo=timezone(timedelta(hours=9))
            )
            if post_date_jst < self.cutoff_date_jst:
                continue

            title = item.find("p", attrs={"class": "title"}).string
            url = self.index + item.find("a")["href"]

            new_news.append(
                {
                    "title": title,
                    "date": post_date_jst.strftime("%Y/%m/%d"),
                    "url": url,
                    "description": "",
                }
            )

        return new_news

    def get_top6(self, soup):
        top = soup.find("ul", attrs={"class": "top6"})

        top6_news = []

        for item in top.findAll("li"):
            date_string = item.find("p", attrs={"class": "date"}).next
            post_date_jst = datetime.strptime(date_string.strip(), "%B %d, %Y").replace(
                tzinfo=timezone(timedelta(hours=9))
            )
            if post_date_jst < self.cutoff_date_jst:
                continue

            title = item.find("p", attrs={"class": "title"}).string
            url = self.index + item.find("a")["href"]

            top6_news.append(
                {
                    "title": title,
                    "date": post_date_jst.strftime("%Y/%m/%d"),
                    "url": url,
                    "description": "",
                }
            )

        return top6_news

    def get_section_news(self, soup):
        news_grid = soup.find("ul", attrs={"class": "default"})

        news = []

        for item in news_grid.findAll("li"):
            date_string = item.find("p", attrs={"class": "date"}).next
            post_date_jst = datetime.strptime(date_string.strip(), "%B %d, %Y").replace(
                tzinfo=timezone(timedelta(hours=9))
            )
            if post_date_jst < self.cutoff_date_jst:
                continue

            title = item.find("p", attrs={"class": "title"}).string
            url = self.index + item.find("a")["href"]

            news.append(
                {
                    "title": title,
                    "date": post_date_jst.strftime("%Y/%m/%d"),
                    "url": url,
                    "description": "",
                }
            )

        return news

    def get_section(self, section):
        soup = self.index_to_soup(self.index + "/ajw/" + section)

        section_news_items = self.get_top6(soup)
        section_news_items.extend(self.get_section_news(soup))

        return section_news_items

    def get_special_section(self, section):
        soup = self.index_to_soup(self.index + "/ajw/" + section)
        top = soup.find("div", attrs={"class": "Section"})

        special_news = []

        for item in top.findAll("li"):
            item_a = item.find("a")

            text_split = item_a.text.strip().split("\n")
            title = text_split[0]
            description = text_split[1].strip()

            url = self.index + item_a["href"]

            special_news.append(
                {
                    "title": title,
                    "date": "",
                    "url": url,
                    "description": description,
                }
            )

        return special_news

    def parse_index(self):
        # soup = self.index_to_soup(self.index)

        feeds = [
            # ("What's New", self.get_whats_new()),
            ("National Report", self.get_section("national_report")),
            ("Politics", self.get_section("politics")),
            ("Business", self.get_section("business")),
            ("Asia & World - China", self.get_section("asia_world/china")),
            (
                "Asia & World - Korean Peninsula",
                self.get_section("asia_world/korean_peninsula"),
            ),
            ("Asia & World - Around Asia", self.get_section("asia_world/around_asia")),
            ("Asia & World - World", self.get_section("asia_world/world")),
            ("Sci & Tech", self.get_section("sci_tech")),
            ("Culture - Style", self.get_section("culture/style")),
            ("Culture - Cooking", self.get_section("culture/cooking")),
            ("Culture - Movies", self.get_section("culture/movies")),
            ("Culture - Manga & Anime", self.get_section("culture/manga_anime")),
            ("Travel", self.get_section("travel")),
            # ("Sports", self.get_section("sports")),
            ("Opinion - Editorial", self.get_section("opinion/editorial")),
            ("Opinion - Vox Populi", self.get_section("opinion/vox")),
            ("Opinion - Views", self.get_section("opinion/views")),
        ]

        return feeds
