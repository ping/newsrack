# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Vox"


class Vox(BasicNewsRecipe):
    title = _name
    language = "en"
    description = "General interest news site https://www.vox.com/"
    __author__ = "ping"
    publication_type = "magazine"
    masthead_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Vox_logo.svg/300px-Vox_logo.svg.png"
    oldest_article = 7  # days
    ignore_duplicate_articles = {"url"}

    max_articles_per_feed = 25
    use_embedded_content = True
    timeout = 20
    timefmt = ""
    pub_date = None  # custom publication date

    remove_javascript = True
    no_stylesheets = True
    auto_cleanup = False
    compress_news_images = True
    scale_news_images = (600, 600)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images

    remove_attributes = ["style", "font"]

    feeds = [
        ("Font Page", "https://www.vox.com/rss/front-page/index.xml"),
        ("All", "https://www.vox.com/rss/index.xml"),
    ]

    def publication_date(self):
        return self.pub_date

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = f"{_name}: {article.utctime:%-d %b, %Y}"
