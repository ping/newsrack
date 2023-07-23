# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
nytimes.com
"""
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title
from nyt import NYTRecipe

from calibre.web.feeds.news import BasicNewsRecipe

_name = "New York Times"


class NYTimesGlobal(NYTRecipe, BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    language = "en"
    __author__ = "ping"
    publication_type = "newspaper"
    description = "News from the New York Times https://www.nytimes.com/"
    masthead_url = "https://mwcm.nyt.com/.resources/mkt-wcm/dist/libs/assets/img/logo-nyt-header.svg"

    oldest_article = 1  # days
    max_articles_per_feed = 20

    remove_attributes = ["style", "font"]
    remove_tags_before = [dict(id="story")]
    remove_tags_after = [dict(id="story")]

    remove_tags = [
        dict(
            id=["in-story-masthead", "sponsor-wrapper", "top-wrapper", "bottom-wrapper"]
        ),
        dict(
            class_=[
                "NYTAppHideMasthead",
                "live-blog-meta",
                "css-13xl2ke",  # nyt logo in live-blog-byline
                "css-8r08w0",  # after storyline-context-container
            ]
        ),
        dict(role=["toolbar", "navigation", "contentinfo"]),
        dict(name=["script", "noscript", "style", "button", "svg"]),
    ]

    extra_css = """
    .live-blog-reporter-update {
        font-size: 0.8rem;
        padding: 0.2rem;
        margin-bottom: 0.5rem;
    }
    [data-testid="live-blog-byline"] {
        color: #444;
        font-style: italic;
    }
    [datetime] > span {
        margin-right: 0.6rem;
    }
    picture img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    [aria-label="media"] {
        font-size: 0.8rem;
        display: block;
        margin-bottom: 1rem;
    }
    [role="complementary"] {
        font-size: 0.8rem;
        padding: 0.2rem;
    }
    [role="complementary"] h2 {
        font-size: 0.85rem;
        margin-bottom: 0.2rem;
     }

    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .sub-headline { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .article-meta { margin-bottom: 1rem; }
    .author { font-weight: bold; color: #444; display: inline-block; }
    .published-dt { margin-left: 0.5rem; }
    .article-img { margin-bottom: 0.8rem; max-width: 100%; }
    .article-img img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box; }
    .article-img .caption { font-size: 0.8rem; }
    div.summary { font-size: 1.2rem; margin: 1rem 0; }
    """

    feeds = [
        ("Home", "https://www.nytimes.com/services/xml/rss/nyt/HomePage.xml"),
        # (
        #     "Global Home",
        #     "https://www.nytimes.com/services/xml/rss/nyt/GlobalHome.xml",
        # ),
        ("World", "https://www.nytimes.com/services/xml/rss/nyt/World.xml"),
        ("US", "https://www.nytimes.com/services/xml/rss/nyt/US.xml"),
        ("Business", "https://feeds.nytimes.com/nyt/rss/Business"),
        # ("Sports", "https://www.nytimes.com/services/xml/rss/nyt/Sports.xml"),
        ("Technology", "https://feeds.nytimes.com/nyt/rss/Technology"),
    ]

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, article.utctime)
