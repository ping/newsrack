"""
koreaherald.com
"""
__license__ = "GPL v3"
__copyright__ = "2011, Seongkyoun Yoo <Seongkyoun.yoo at gmail.com>"

import os
import re
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import format_title

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Korea Herald"


class KoreaHerald(BasicNewsRecipe):
    title = _name
    language = "en"
    description = "Korea Herald News articles https://koreaherald.com/"
    __author__ = "Seongkyoun Yoo"
    no_stylesheets = True
    remove_javascript = True
    use_embedded_content = False
    encoding = "utf-8"
    publication_type = "newspaper"
    masthead_url = "https://res.heraldm.com/new_201209/images/common/logo.gif"

    oldest_article = 1
    max_articles_per_feed = 25

    compress_news_images = True
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    auto_cleanup = False
    timeout = 20
    timefmt = ""
    pub_date = None  # custom publication date

    remove_attributes = ["style", "align"]
    remove_tags_before = [dict(class_="main")]
    remove_tags_after = [dict(class_="main")]
    remove_tags = [
        dict(name=["script", "style"]),
        dict(id=["thumimage"]),
        dict(
            class_=[
                "view_tit_icon",
                "main_r_tit",
                "view_main_c_li",
                "spot_li",
                "khadv_bg",
                "main_r",
            ]
        ),
    ]

    extra_css = """
    h1.view_tit { font-size: 1.8rem; margin-bottom: 0.5rem; }
    h2.view_tit_sub { font-size: 1.4rem; font-weight: normal; margin-top: 0; margin-bottom: 0.5rem; }
    .view_tit_byline { margin-top: 1rem; margin-bottom: 1rem; }
    .view_tit_byline_l, .view_tit_byline_l a { font-weight: bold; color: #444; }
    .view_tit_byline_r span { margin-right: 0.6rem; }
    td img { max-width: 100%; height: auto; }
    .view_con_caption { font-size: 0.8rem; margin-top: 0.2rem; }
    """

    feeds = [
        ("National", "http://www.koreaherald.com/common/rss_xml.php?ct=102"),
        ("Business", "http://www.koreaherald.com/common/rss_xml.php?ct=103"),
        ("Finance", "http://www.koreaherald.com/common/rss_xml.php?ct=305"),
        ("Life & Style", "http://www.koreaherald.com/common/rss_xml.php?ct=104"),
        ("Entertainment", "http://www.koreaherald.com/common/rss_xml.php?ct=105"),
        # ("Sports", "http://www.koreaherald.com/common/rss_xml.php?ct=106"),
        ("World", "http://www.koreaherald.com/common/rss_xml.php?ct=107"),
        ("Opinion", "http://www.koreaherald.com/common/rss_xml.php?ct=108"),
    ]

    def publication_date(self):
        return self.pub_date

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, article.utctime)

    def preprocess_html(self, soup):
        byline_date = soup.find(attrs={"class": "view_tit_byline_r"})
        if byline_date:
            # format the published/updated date properly
            date_elements = []
            # Published : Apr 18, 2022 - 16:41       Updated : Apr 18, 2022 - 16:41
            date_re = r"(Published|Updated).+?\:.+?(?P<date>[a-z]{3}\s\d+),.+?(?P<time>\d+\:\d+)"
            for m in re.findall(date_re, byline_date.text, re.IGNORECASE):
                date_ele = soup.new_tag("span")
                date_ele.append(" ".join(m))
                date_elements.append(date_ele)
            byline_date.clear()
            for e in date_elements:
                byline_date.append(e)
        return soup
