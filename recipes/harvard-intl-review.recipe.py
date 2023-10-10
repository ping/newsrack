# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
hir.harvard.edu
"""
import os
import sys
from datetime import timezone

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import (
    BasicNewsrackRecipe,
    format_title,
    get_date_format,
    get_datetime_format,
)

from calibre.web.feeds import Feed
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Harvard International Review"


class HarvardInternationalReview(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = "The Harvard International Review is a quarterly magazine offering insight on international affairs from the perspectives of scholars, leaders, and policymakers. https://hir.harvard.edu/"
    language = "en"
    __author__ = "ping"
    publication_type = "magazine"
    oldest_article = 30  # days
    max_articles_per_feed = 30
    use_embedded_content = True
    masthead_url = (
        "https://hir.harvard.edu/content/images/2020/12/HIRlogo_crimson-4.png"
    )
    compress_news_images_auto_size = 7
    auto_cleanup = True
    timeout = 60

    extra_css = """
    .article-meta { margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; }
    .article-meta .published-dt { margin-left: 0.5rem; }
    """

    feeds = [
        (_name, "https://hir.harvard.edu/rss/"),
    ]

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, article.utctime)

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
            article_index = f"{date_published:{get_date_format()}}"
            # add author and pub date
            soup = self.soup(a.content)
            header = None
            if soup.body.contents[0].name in ["h1", "h2", "h3"]:
                header = soup.body.contents[0]
            meta = soup.new_tag("div", attrs={"class": "article-meta"})
            if a.author:
                author_ele = soup.new_tag("span", attrs={"class": "author"})
                author_ele.append(a.author)
                meta.append(author_ele)
            pub_ele = soup.new_tag("span", attrs={"class": "published-dt"})
            pub_ele.append(f"{date_published:{get_datetime_format()}}")
            meta.append(pub_ele)
            if header:
                header.insert_after(meta)
            else:
                soup.body.insert(0, meta)
            a.content = soup.body.decode_contents()
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
