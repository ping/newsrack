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
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Korea Herald"


class KoreaHerald(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    language = "en"
    description = "Korea Herald News articles https://koreaherald.com/"
    __author__ = "Seongkyoun Yoo"
    publication_type = "newspaper"
    masthead_url = "https://res.heraldm.com/new_201209/images/common/logo.gif"

    oldest_article = 1
    max_articles_per_feed = 25

    keep_only_tags = [dict(class_="news_content")]
    remove_attributes = ["style", "align"]
    remove_tags = [
        dict(name=["script", "style"]),
        dict(class_=["news_btn_wrap", "news_journalist_area"]),
    ]

    extra_css = """
    h1.news_title { font-size: 1.8rem; margin-bottom: 0.4rem; }
    h2.news_title { font-size: 1.2rem; font-style: italic; font-weight: normal; margin-bottom: 0.8rem; }
    p.news_date { margin-top: 0.2rem; }
    .img_caption { font-size: 0.8rem; margin-top: 0.2rem; display: block; }
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

    def print_version(self, url):
        # Patch messed up url from rss
        # Example: https://www.koreaherald.com/view.php?ud=/view.php?ud=20230814000600
        return url.replace("?ud=/view.php", "")
