# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import json
from urllib.parse import urljoin

from calibre import browser
from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.utils.date import parse_date
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Bloomberg Businessweek"
issue_url = ""  # ex: https://www.bloomberg.com/magazine/businessweek/22_44


class BloombergBusinessweek(BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Bloomberg delivers business and markets news, data, analysis, and video "
        "to the world, featuring stories from Businessweek. https://www.bloomberg.com/businessweek"
    )
    language = "en"
    masthead_url = "https://assets.bwbx.io/s3/javelin/public/hub/images/BW-Logo-Black-cc9035fbb3.svg"
    ignore_duplicate_articles = {"url"}
    no_stylesheets = True
    remove_javascript = True
    auto_cleanup = False
    timeout = 20

    # NOTES: Bot detection kicks in really easily so either:
    # - limit the number of feeds
    # - or max_articles_per_feed
    # - or increase delay
    delay = 3
    oldest_article = 7
    max_articles_per_feed = 25

    compress_news_images = True
    compress_news_images_auto_size = 8
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    timefmt = ""  # suppress date output
    pub_date = None  # custom publication date
    bot_blocked = False

    remove_attributes = ["style", "height", "width", "align"]
    remove_tags = [
        dict(
            class_=[
                "terminal-news-story",
                "inline-newsletter-top",
                "inline-newsletter-middle",
                "inline-newsletter-bottom",
                "for-you__wrapper",
                "video-player__overlay",
            ]
        ),
        dict(name=["aside"], class_=["postr-recirc"]),
        dict(attrs={"data-tout-type": True}),
        dict(attrs={"data-ad-placeholder": True}),
    ]

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .sub-headline { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .article-meta { padding-bottom: 0.5rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    .image img { display: block; max-width: 100%; height: auto; }
    .news-figure-caption-text, .news-figure-credit { display: block; font-size: 0.8rem; margin-top: 0.2rem; }
    .trashline { font-style: italic; }
    """

    def publication_date(self):
        return self.pub_date

    # We send no cookies to avoid triggering bot detection
    def get_browser(self, *args, **kwargs):
        return self

    def clone_browser(self, *args, **kwargs):
        return self.get_browser()

    def open_novisit(self, *args, **kwargs):
        if self.bot_blocked:
            self.log.warn(f"Block detected. Skipping {args[0]}")
            # Abort article without making actual request
            self.abort_article(f"Block detected. Skipped {args[0]}")
        br = browser()
        br.set_handle_redirect(False)
        try:
            return br.open_novisit(*args, **kwargs)
        except Exception as e:
            if hasattr(e, "code") and e.code == 307:
                self.bot_blocked = True
                err_msg = f"Blocked by bot detection: {args[0]}"
                self.log.warn(err_msg)
                self.abort_recipe_processing(err_msg)
                self.abort_article(err_msg)
            raise

    open = open_novisit

    def _downsize_image_url(self, img_url):
        return img_url.replace("/-1x-1.", "/800x-1.")

    def preprocess_raw_html(self, raw_html, url):
        article = None
        soup = BeautifulSoup(raw_html)
        for script in soup.find_all(
            "script",
            attrs={
                "type": "application/json",
                "data-component-props": ["ArticleBody", "FeatureBody"],
            },
        ):
            article = json.loads(script.contents[0])
            if not article.get("story"):
                continue
            break
        if not (article and article.get("story")):
            err_msg = f"Unable to find article json: {url}"
            self.log.warn(err_msg)
            self.abort_article(err_msg)

        article = article["story"]
        date_published = parse_date(article["publishedAt"], assume_utc=True)
        soup = BeautifulSoup(
            f"""<html>
        <head><title></title></head>
        <body>
            <article>
            <h1 class="headline"></h1>
            <div class="article-meta">
                <span class="published-dt"></span>
            </div>
            </article>
        </body></html>"""
        )
        if (not self.pub_date) or date_published > self.pub_date:
            self.pub_date = date_published
        published_at = soup.find(class_="published-dt")
        published_at.append(f"{date_published:%-I:%M%p, %-d %b, %Y}")
        if article.get("updatedAt"):
            date_updated = parse_date(article["updatedAt"], assume_utc=True)
            published_at.append(f", Updated {date_updated:%-I:%M%p, %-d %b, %Y}")
            if (not self.pub_date) or date_updated > self.pub_date:
                self.pub_date = date_updated

        soup.head.title.append(article.get("headlineText") or article["headline"])
        h1_title = soup.find("h1")
        h1_title.append(article.get("headlineText") or article["headline"])
        if article.get("summaryText") or article.get("abstract"):
            sub_headline = soup.new_tag("div", attrs={"class": "sub-headline"})
            if article.get("summaryText"):
                sub_headline.append(article["summaryText"])
            elif article.get("abstract"):
                for i, abstract in enumerate(article["abstract"]):
                    if i > 0:
                        sub_headline.append(soup.new_tag("br"))
                    sub_headline.append(f"• {abstract}")
            h1_title.insert_after(sub_headline)
        # inject authors
        if article.get("byline"):
            soup.find(class_="article-meta").insert(
                0,
                BeautifulSoup(f'<span class="author">{article["byline"]}</span>'),
            )
        else:
            try:
                post_authors = [a["name"] for a in article.get("authors", [])]
                if post_authors:
                    soup.find(class_="article-meta").insert(
                        0,
                        BeautifulSoup(
                            f'<span class="author">{", ".join(post_authors)}</span>'
                        ),
                    )
            except (KeyError, TypeError):
                pass
        # inject categories
        categories = [cat.title() for cat in article.get("categories", [])]
        if categories:
            soup.body.article.insert(
                0,
                BeautifulSoup(
                    f'<span class="article-section">{" / ".join(categories)}</span>'
                ),
            )
        # inject lede image
        if article.get("ledeImageUrl"):
            lede_img_url = article["ledeImageUrl"]
            lede_img_caption_html = article.get("ledeCaption", "")
            img_container = soup.new_tag("div", attrs={"class": "image"})
            img_ele = soup.new_tag(
                "img", attrs={"src": self._downsize_image_url(lede_img_url)}
            )
            img_container.append(img_ele)
            if lede_img_caption_html:
                caption_ele = soup.new_tag(
                    "div", attrs={"class": "news-figure-caption-text"}
                )
                caption_ele.append(BeautifulSoup(lede_img_caption_html))
                img_container.append(caption_ele)
            soup.body.article.append(img_container)

        body_soup = BeautifulSoup(article["body"])
        for img_div in body_soup.find_all(name="figure", attrs={"data-type": "image"}):
            for img in img_div.find_all("img", attrs={"data-native-src": True}):
                img["src"] = img["data-native-src"]
        for img in body_soup.find_all(name="img", attrs={"src": True}):
            img["src"] = self._downsize_image_url(img["src"])
        soup.body.article.append(body_soup)
        return str(soup)

    def parse_index(self):
        if not issue_url:
            soup = self.index_to_soup("https://www.bloomberg.com/businessweek")
            latest_issue_article = soup.select(
                "#magazines_carousel article div[data-component='headline']"
            )[0]
            edition_url = urljoin(
                "https://www.bloomberg.com", latest_issue_article.a["href"]
            )
        else:
            edition_url = issue_url
        soup = self.index_to_soup(edition_url)
        edition = self.tag_to_string(soup.find("h1")).replace(" Issue", "")
        self.title = f"{_name}: {edition}"
        cover_img = soup.find("img", class_="story-list-module__image")
        self.cover_url = cover_img["src"].replace("/280x-1.jpg", "/800x-1.jpg")
        feeds = []
        for section in soup.find_all("div", class_="story-list-module__info"):
            section_name = self.tag_to_string(section.find("h3"))
            section_articles = []
            for article in section.find_all(
                class_="story-list-story__info__headline-link"
            ):
                section_articles.append(
                    {
                        "title": self.tag_to_string(article),
                        "url": urljoin("https://www.bloomberg.com", article["href"]),
                    }
                )
            if section_articles:
                feeds.append((section_name, section_articles))
        return feeds
