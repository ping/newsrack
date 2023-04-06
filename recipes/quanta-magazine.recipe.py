# Original at https://raw.githubusercontent.com/kovidgoyal/calibre/1ca6887e6c9f83a05cafe1fba8bae6de9bd2773c/recipes/quanta_magazine.recipe

import os
import sys
from datetime import timezone, timedelta

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds import Feed
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Quanta Magazine"


class QuantaMagazine(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "lui1"
    description = (
        "Quanta Magazine is committed to in-depth, accurate journalism that "
        "serves the public interest. Each article braids the complexities of "
        "science with the malleable art of storytelling and is meticulously "
        "reported, edited and fact-checked. https://www.quantamagazine.org/"
    )
    publication_type = "magazine"
    language = "en"
    encoding = "UTF-8"
    masthead_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Quanta_Magazine_Logo_05.2022.svg/320px-Quanta_Magazine_Logo_05.2022.svg.png"
    auto_cleanup = False
    use_embedded_content = False

    oldest_article = 30
    max_articles_per_feed = 100

    keep_only_tags = [
        dict(name="div", attrs={"id": "postBody"}),
    ]
    remove_tags = [
        dict(name=["script", "noscript", "style", "svg", "form", "button"]),
        dict(class_=["post__title__actions", "post__sidebar__content", "video"]),
    ]

    extra_css = """
    .component-img img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    .caption, .attribution { font-size: 0.8rem; margin: 0; }
    """

    feeds = [
        (_name, "https://api.quantamagazine.org/feed/"),
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
