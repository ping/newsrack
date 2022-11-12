# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
restofworld.org
"""
from datetime import timezone, timedelta

from calibre.web.feeds import Feed
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Rest of World"


class RestOfWorld(BasicNewsRecipe):
    title = _name
    description = "Reporting Global Tech Stories https://restofworld.org/"
    language = "en"
    __author__ = "ping"
    publication_type = "blog"
    oldest_article = 30  # days
    max_articles_per_feed = 25
    use_embedded_content = False
    no_stylesheets = True
    remove_javascript = True
    encoding = "utf-8"
    compress_news_images = True
    masthead_url = "https://restofworld.org/style-guide/images/Variation_3.svg"
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    auto_cleanup = False
    timeout = 60
    timefmt = ""
    pub_date = None  # custom publication date

    keep_only_tags = [dict(id="content")]

    remove_tags = [
        dict(class_=["reading-header", "footer-recirc"]),
        dict(attrs={"aria-hidden": "true"}),
    ]
    extra_css = """
    h1.post-header__text__title { font-size: 1.8rem; margin-bottom: 0.4rem; }
    h3.post-header__text__dek { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; font-weight: normal; }
    .post-subheader { margin-bottom: 1rem; }
    .post-subheader .post-subheader__byline { font-weight: bold; color: #444; }
    .post-header__image { margin-top: 0.5rem; margin-bottom: 0.8rem; }
    .image__wrapper img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    .figcaption { font-size: 0.8rem; }
    blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    .post-footer { margin: 1rem 0; padding-top: 0.5rem; border-top: 1px solid #444; }
    .post-footer .post-footer__authors { font-size: 0.85rem; color: #444; font-style: italic; }
    """

    feeds = [
        ("Rest of World", "https://restofworld.org/feed/latest/"),
    ]

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = f"{_name}: {article.utctime:%-d %b, %Y}"

    def publication_date(self):
        return self.pub_date

    def preprocess_html(self, soup):
        for img in soup.find_all("img", attrs={"data-srcset": True}):
            sources = [s.strip() for s in img["data-srcset"].split(",") if s.strip()]
            img["src"] = sources[-1].split(" ")[0].strip()
        for picture in soup.find_all("picture"):
            sources = picture.find_all("source", attrs={"srcset": True})
            if not sources:
                continue
            if picture.find("img", attrs={"src": True}):
                for s in sources:
                    s.decompose()
        return soup

    def parse_feeds(self):
        # convert single parsed feed into date-sectioned feed
        # use this only if there is just 1 feed
        parsed_feeds = super().parse_feeds()
        if len(parsed_feeds or []) != 1:
            return parsed_feeds

        articles = []
        for feed in parsed_feeds:
            articles.extend(feed.articles)
        articles = sorted(articles, key=lambda a: a.utctime, reverse=True)
        new_feeds = []
        curr_feed = None
        parsed_feed = parsed_feeds[0]
        for i, a in enumerate(articles, start=1):
            date_published = a.utctime.replace(tzinfo=timezone.utc)
            date_published_loc = date_published.astimezone(
                timezone(offset=timedelta(hours=9))  # Seoul time
            )
            article_index = f"{date_published_loc:%-d %B, %Y}"
            if i == 1:
                curr_feed = Feed(log=parsed_feed.logger)
                curr_feed.title = article_index
                curr_feed.description = parsed_feed.description
                curr_feed.image_url = parsed_feed.image_url
                curr_feed.image_height = parsed_feed.image_height
                curr_feed.image_alt = parsed_feed.image_alt
                curr_feed.oldest_article = parsed_feed.oldest_article
                curr_feed.articles = []
                curr_feed.articles.append(a)
                continue
            if curr_feed.title == article_index:
                curr_feed.articles.append(a)
            else:
                new_feeds.append(curr_feed)
                curr_feed = Feed(log=parsed_feed.logger)
                curr_feed.title = article_index
                curr_feed.description = parsed_feed.description
                curr_feed.image_url = parsed_feed.image_url
                curr_feed.image_height = parsed_feed.image_height
                curr_feed.image_alt = parsed_feed.image_alt
                curr_feed.oldest_article = parsed_feed.oldest_article
                curr_feed.articles = []
                curr_feed.articles.append(a)
            if i == len(articles):
                # last article
                new_feeds.append(curr_feed)

        return new_feeds
