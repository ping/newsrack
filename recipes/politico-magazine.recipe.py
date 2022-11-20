# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
politico.com
"""
from datetime import timezone

from calibre.web.feeds import Feed
from calibre.web.feeds.news import BasicNewsRecipe

_name = "POLITICO Magazine"


class PoliticoMagazine(BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "News, Analysis and Opinion from POLITICO https://www.politico.com/"
    publisher = "Capitol News Company, LLC"
    category = "news, politics, USA"
    publication_type = "magazine"
    encoding = "utf-8"
    language = "en"
    masthead_url = "https://www.politico.com/dims4/default/bbb0fd2/2147483647/resize/1160x%3E/quality/90/?url=https%3A%2F%2Fstatic.politico.com%2F0e%2F5b%2F3cf3e0f04ca58370112ab667c255%2Fpolitico-logo.png"
    no_stylesheets = True
    remove_javascript = True
    use_embedded_content = False

    oldest_article = 7
    max_articles_per_feed = 25

    compress_news_images = True
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    timeout = 20
    pub_date = None  # custom publication date

    keep_only_tags = [dict(name=["main"])]
    remove_tags = [
        dict(
            class_=[
                "story-section",
                "social-tools",
                "below-article-section",
                "pop-up-bar",
            ]
        )
    ]

    extra_css = """
    .media-item__summary h2.headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .media-item__summary p.dek { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; margin-top: 0; }
    .fig-graphic img { max-width: 100%; height: auto; }
    .story-meta__credit, .story-photo__caption { font-size: 0.8rem; margin-top: 0.2rem; }
    """

    feeds = [("Magazine", "https://rss.politico.com/magazine.xml")]

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = f"{_name}: {article.utctime:%-d %b, %Y}"

    def publication_date(self):
        return self.pub_date

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
            article_index = f"{date_published:%-d %B, %Y}"
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
