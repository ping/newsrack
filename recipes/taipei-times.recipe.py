# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0
import os
import sys
from datetime import timezone, timedelta

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import format_title

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Taipei Times"


class TaipeiTimes(BasicNewsRecipe):
    title = _name
    language = "en"
    __author__ = "ping"
    publication_type = "newspaper"
    description = "News from the Taipei Times https://www.taipeitimes.com/"
    masthead_url = "https://www.taipeitimes.com/assets/images/logo.gif"

    oldest_article = 1  # days
    max_articles_per_feed = 50
    use_embedded_content = False
    timeout = 20
    timefmt = ""
    pub_date = None  # custom publication date

    remove_javascript = True
    no_stylesheets = True
    auto_cleanup = True
    compress_news_images = True
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images

    ignore_duplicate_articles = {"title", "url"}

    keep_only_tags = [dict(name="div", class_="archives")]
    remove_tags = [dict(attrs={"class": ["ad_mg_t", "ad_mg_b", "sh"]})]

    extra_css = """
    .archives h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
    .archives h2 { font-size: 1.2rem; margin-bottom: 0.5rem; font-weight: normal; font-style: italic; }
    p.byline { font-weight: bold; color: #444; display: block; margin-top: 1rem; }
    .imgboxa img { max-width: 100%; height: auto; }
    .imgboxa p { font-size: 0.8rem; margin-top: 0.2rem; display: inline-block; font-weight: normal; }
    """

    feeds = [(_name, "https://www.taipeitimes.com/xml/index.rss")]

    def publication_date(self):
        return self.pub_date

    def populate_article_metadata(self, article, _, __):
        if not self.pub_date or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            post_date_local = article.utctime.astimezone(timezone(timedelta(hours=8)))
            self.title = format_title(_name, post_date_local)

    def preprocess_raw_html(self, raw_html, _):
        soup = BeautifulSoup(raw_html)

        # replace byline <ul> with actual byline element
        byline = soup.select_one("ul.as")
        if byline:
            byline_name = byline.find(attrs={"class": "name"})
            if byline_name:
                byline_name["class"] = "byline"
                byline.replace_with(byline_name)

        # replace with image caption's <h1> with <p> .... wtf
        img_h1_captions = soup.select(".imgboxa h1")
        for h1 in img_h1_captions:
            h1.name = "p"

        return str(soup)
