#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: GPLv3 Copyright: 2019, Kovid Goyal <kovid at kovidgoyal.net>

# Original at: https://github.com/kovidgoyal/calibre/blob/640ca33197ea2c7772278183b3f77701009bb733/recipes/lrb.recipe
from datetime import datetime, timezone
import json
from calibre.web.feeds.news import BasicNewsRecipe, classes


def absolutize(href):
    if href.startswith("/"):
        href = "https://www.lrb.co.uk" + href
    return href


_name = "London Review of Books"


class LondonReviewOfBooksPayed(BasicNewsRecipe):
    title = _name
    __author__ = "Kovid Goyal"
    description = "Literary review publishing essay-length book reviews and topical articles on politics, literature, history, philosophy, science and the arts by leading writers and thinkers https://www.lrb.co.uk/"  # noqa
    category = "news, literature, UK"
    publisher = "LRB Ltd."
    language = "en_GB"
    no_stylesheets = True
    remove_javascript = True
    # delay = 1
    encoding = "utf-8"
    INDEX = "https://www.lrb.co.uk"
    publication_type = "magazine"
    needs_subscription = False
    requires_version = (3, 0, 0)

    # masthead_url = "https://www.lrb.co.uk/assets/icons/apple-touch-icon.png"
    masthead_url = (
        "https://www.pw.org/files/small_press_images/london_review_of_books.png"
    )
    compress_news_images = True
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    timeout = 20
    timefmt = ""
    pub_date = None

    keep_only_tags = [
        classes(
            "article-header--title paperArticle-reviewsHeader article-content letters"
        ),
    ]
    remove_tags = [
        classes(
            "social-button article-mask lrb-readmorelink article-send-letter article-share lettersnav prev-next-buttons"
        ),
        dict(id=["letters-aside"]),
    ]
    remove_attributes = ["width", "height"]

    extra_css = """
    .embedded-image-caption { font-size: 0.8rem; }
    .article-reviewed-item { margin-bottom: 1rem; margin-left: 0.5rem; }
    .article-reviewed-item .article-reviewed-item-title { font-weight: bold; }
    """

    def publication_date(self):
        return self.pub_date

    def get_browser(self, *a, **kw):
        kw[
            "user_agent"
        ] = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        br = BasicNewsRecipe.get_browser(self, *a, **kw)
        return br

    def preprocess_html(self, soup):
        info_ele = soup.find(
            name="script",
            attrs={"data-schema": "Article", "type": "application/ld+json"},
        )
        if info_ele:
            info = json.loads(info_ele.contents[0])
            soup.body["data-og-summary"] = info.get("description", "")
            # example: 2022-08-04T00:00:00+00:00
            published_date = datetime.strptime(
                info["datePublished"][:19], "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=timezone.utc)
            # example: 2022-07-28T12:07:08+00:00
            modified_date = datetime.strptime(
                info["dateModified"][:19], "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=timezone.utc)
            soup.body["data-og-date"] = f"{modified_date:%Y-%m-%d %H:%M:%S}"
            if not self.pub_date or modified_date > self.pub_date:
                self.pub_date = modified_date
                self.title = f"{_name}: {published_date:%-d %b, %Y}"
        else:
            letter_ele = soup.find(attrs={"class": "letters-titles--date"})
            if letter_ele:
                published_date = datetime.strptime(letter_ele.text, "%d %B %Y").replace(
                    tzinfo=timezone.utc
                )
                soup.body["data-og-date"] = f"{published_date:%Y-%m-%d %H:%M:%S}"
            for letter in soup.find_all(attrs={"class": "letter"}):
                letter.insert_before(soup.new_tag("hr"))

        for img in soup.findAll("img", attrs={"data-srcset": True}):
            for x in img["data-srcset"].split():
                if "/" in x:
                    img["src"] = x
        return soup

    def populate_article_metadata(self, article, soup, _):
        article_summary = soup.find(attrs={"data-og-summary": True})
        if article_summary:
            article.text_summary = article_summary["data-og-summary"]

        article_date = soup.find(attrs={"data-og-date": True})
        if article_date:
            modified_date = datetime.strptime(
                article_date["data-og-date"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)
            article.utctime = modified_date
            article.localtime = modified_date

    def parse_index(self):
        soup = self.index_to_soup(self.INDEX)
        container = soup.find(attrs={"class": "issue-grid"})
        img = container.find("img")
        self.cover_url = img["data-srcset"].split()[-2]
        a = img.findParent("a")
        soup = self.index_to_soup(absolutize(a["href"]))
        grid = soup.find(attrs={"class": "toc-grid-items"})
        articles = []
        for a in grid.findAll(**classes("toc-item")):
            url = absolutize(a["href"])
            h3 = a.find("h3")
            h4 = a.find("h4")
            review_items = h4.find_all(
                name="div", attrs={"class": "article-reviewed-item"}
            )
            if not review_items:
                if self.tag_to_string(h3) == "Letters":
                    title = self.tag_to_string(h3)
                else:
                    title = "{} - {}".format(
                        self.tag_to_string(h3), self.tag_to_string(h4)
                    )
            else:
                item_descriptions = []
                for item in review_items:
                    desc = ""
                    for c in [
                        "article-reviewed-item-title",
                        "article-reviewed-item-subtitle",
                    ]:
                        s = item.find(name="span", attrs={"class": c})
                        if s:
                            desc += s.contents[0]
                    if desc:
                        item_descriptions.append(desc)

                title = "{} - {}".format(
                    self.tag_to_string(h3), " / ".join(item_descriptions)
                )
            articles.append({"title": title, "url": url})

        return [("Articles", articles)]
