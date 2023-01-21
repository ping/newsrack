"""
smh.com.au
"""
__license__ = "GPL v3"
__copyright__ = "2010-2011, Darko Miletic <darko.miletic at gmail.com>"

import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
try:
    from recipes_shared import BasicNewsrackRecipe, format_title
except ImportError:
    # just for Pycharm to pick up for auto-complete
    from includes.recipes_shared import BasicNewsrackRecipe, format_title

from calibre.ebooks.BeautifulSoup import BeautifulSoup

# Original at https://github.com/kovidgoyal/calibre/blob/8bc3d757f4bb78ee002caf2766d7285497349097/recipes/smh.recipe
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Sydney Morning Herald"


class SydneyMorningHerald(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "Darko Miletic"
    description = "Breaking news from Sydney, Australia and the world. Features the latest business, sport, entertainment, travel, lifestyle, and technology news. https://www.smh.com.au/"  # noqa
    publisher = "Fairfax Digital"
    category = "news, politics, Australia, Sydney"
    oldest_article = 1
    max_articles_per_feed = 50
    ignore_duplicate_articles = {"title", "url"}
    use_embedded_content = False
    encoding = "utf-8"

    language = "en_AU"
    remove_empty_feeds = True
    masthead_url = "https://upload.wikimedia.org/wikipedia/en/thumb/8/86/Sydney_Morning_Herald_logo.svg/1024px-Sydney_Morning_Herald_logo.svg.png"
    publication_type = "newspaper"

    compress_news_images_auto_size = 10

    remove_attributes = ["style", "font", "width", "height"]
    keep_only_tags = [dict(name="article")]
    remove_tags = [
        dict(name=["button", "svg"]),
        dict(id=["saveTooltip"]),
        dict(attrs={"class": "noPrint"}),
    ]

    extra_css = """
    h1[itemprop="headline"] { font-size: 1.8rem; margin-bottom: 0.5rem; }
    .bylines, span[data-testid="byline"] a { font-weight: bold; color: #444; }
    div[data-testid="category"], div[data-testid="tag-name"] { display: inline-block; margin-right: 0.2rem; }
    div[data-testid="image"] p { font-size: 0.8rem; margin-top: 0.2rem; }
    div[data-testid="image"] img { max-width: 100%; height: auto; }
    cite, cite span { margin-left: 0.2rem; }
    """

    # https://www.smh.com.au/rssheadlines
    feeds = [
        ("Latest News", "https://www.smh.com.au/rss/feed.xml"),
        ("Federal Politics", "https://www.smh.com.au/rss/politics/federal.xml"),
        ("NSW News", "https://www.smh.com.au/rss/national/nsw.xml"),
        ("World", "https://www.smh.com.au/rss/world.xml"),
        ("National", "https://www.smh.com.au/rss/national.xml"),
        ("Business", "https://www.smh.com.au/rss/business.xml"),
        ("Culture", "https://www.smh.com.au/rss/culture.xml"),
        ("Technology", "https://www.smh.com.au/rss/technology.xml"),
        ("Environment", "https://www.smh.com.au/rss/environment.xml"),
        # ("Lifestyle", "https://www.smh.com.au/rss/lifestyle.xml"),
        # ("Property", "https://www.smh.com.au/rss/property.xml"),
        # ("Sport", "https://www.smh.com.au/rss/sport.xml"),
        # ("Ruby League", "https://www.smh.com.au/rss/sport/nrl.xml"),
        # ("AFL", "https://www.smh.com.au/rss/sport/afl.xml"),
    ]

    def populate_article_metadata(self, article, _, __):
        if not self.pub_date or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, self.pub_date)

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        vid_player = soup.find(
            "div", attrs={"data-testid": "video-player", "class": "noPrint"}
        )
        if vid_player:
            self.abort_article("Video article")

        ul_eles = soup.find_all("ul") or []
        for ul in ul_eles:
            if not ul.find_all("li", attrs={"data-testid": ["category", "tag-name"]}):
                continue
            for i, li in enumerate(ul.find_all("li")):
                live_ticker = li.find("h5")
                if live_ticker:
                    live_ticker.name = "span"
                a_link = li.find("a")
                if a_link:
                    li.string = self.tag_to_string(a_link)
                    if i > 0:
                        li.string = " • " + li.string
                li.name = "div"
            ul.name = "div"
            break

        h5_eles = soup.find_all("h5") or []
        for h5 in h5_eles:
            if not h5.find_all("span", attrs={"data-testid": ["byline"]}):
                continue
            h5.name = "div"
            h5["class"] = "bylines"
            break

        for picture in soup.find_all("picture"):
            sources = picture.find_all("source", attrs={"srcset": True})
            if not sources:
                continue
            picture.img["src"] = sources[0]["srcset"].split(",")[0].split(" ")[0]
            for s in sources:
                s.decompose()
        return str(soup)
