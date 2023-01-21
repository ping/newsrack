#!/usr/bin/env python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
"""
asianreviewofbooks.com
"""

# Original from https://github.com/kovidgoyal/calibre/blob/29cd8d64ea71595da8afdaec9b44e7100bff829a/recipes/asianreviewofbooks.recipe

__license__ = "GPL v3"
__copyright__ = "2012-2017, Darko Miletic <darko.miletic at gmail.com>"

import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
try:
    from recipes_shared import BasicNewsrackRecipe, format_title
except ImportError:
    # just for Pycharm to pick up for auto-complete
    from includes.recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Asian Review of Books"


class AsianReviewOfBooks(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "Darko Miletic"
    description = "In addition to reviewing books about or of relevance to Asia, the Asian Review of Books also features long-format essays by leading Asian writers and thinkers, to providing an unparalleled forum for discussion of key contemporary issues by Asians for Asia and a vehicle of intellectual depth and breadth where leading thinkers can write on the books, arts and ideas of the day. Widely quoted and referenced, with an archive of more than one thousand book reviews, it is the only web resource dedicated to Asian books. And now, with the addition of the new premium content, the Asian Review of Books, is a must-read publication. https://asianreviewofbooks.com/"  # noqa
    publisher = "The Asian Review of Books"
    category = "literature, books, reviews, Asia"
    use_embedded_content = False
    encoding = "utf-8"
    language = "en"
    publication_type = "magazine"
    auto_cleanup = False
    masthead_url = "https://i2.wp.com/asianreviewofbooks.com/content/wp-content/uploads/2016/09/ARBwidelogo.png"

    oldest_article = 30
    max_articles_per_feed = 30

    conversion_options = {
        "comment": description,
        "tags": category,
        "publisher": publisher,
        "language": language,
    }

    remove_attributes = ["width", "height"]
    keep_only_tags = [
        dict(name="main"),
    ]
    remove_tags = [
        dict(class_=["entry-meta", "sharedaddy", "jp-relatedposts", "entry-footer"])
    ]

    extra_css = """
    blockquote { font-size: 1.2rem; margin-left: 0; font-style: italic; }
    .wp-caption-text, .entry-featured__caption { display: block; font-size: 0.8rem; margin-top: 0.2rem; }
    """

    feeds = [("Articles", "http://asianreviewofbooks.com/content/feed/")]

    def populate_article_metadata(self, article, soup, _):
        if not self.pub_date or self.pub_date < article.utctime:
            self.pub_date = article.utctime
            self.title = format_title(_name, self.pub_date)

    def preprocess_html(self, soup):
        # find empty <p>
        paras = soup.find_all("p")
        for p in paras:
            if not p.text.strip():
                p.decompose()

        quotes = soup.find_all("h5")
        for q in quotes:
            q.name = "blockquote"

        bio = soup.find_all("h6")
        for b in bio:
            b.name = "div"

        return soup
