"""
spectator.co.uk
"""
import os
import sys
from urllib.parse import urlparse, urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
try:
    from recipes_shared import BasicNewsrackRecipe
except ImportError:
    # just for Pycharm to pick up for auto-complete
    from includes.recipes_shared import BasicNewsrackRecipe

from calibre.utils.date import parse_date
from calibre.web.feeds.news import BasicNewsRecipe

_name = "The Spectator"


class SpectatorMagazine(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = (
        "The Spectator is a weekly British magazine on politics, culture, and current affairs. "
        "It was first published in July 1828, making it the oldest surviving weekly magazine in "
        "the world. https://www.spectator.co.uk/magazine"
    )
    __author__ = "ping"
    language = "en"
    encoding = "utf-8"
    publication_type = "magazine"
    masthead_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/The_Spectator_logo.svg/1024px-The_Spectator_logo.svg.png"
    auto_cleanup = False
    compress_news_images_auto_size = 8

    keep_only_tags = [
        dict(class_=["entry-header", "entry-content__wrapper", "author-bio__content"])
    ]
    remove_tags = [
        dict(name=["script", "noscript", "style", "svg"]),
        dict(
            class_=[
                "breadcrumbs",
                "writers-link__avatar",
                "entry-header__meta",
                "entry-meta",
                "subscription-banner",
                "subscribe-ribbon",
                "author-bio__title",
                "entry-header__issue",
            ]
        ),
        dict(id=["most-popular"]),
    ]
    remove_attributes = ["style", "font", "width", "height", "align"]

    extra_css = """
    h1.entry-header__title { font-size: 1.8rem; margin-bottom: 0.4rem; }
    h2.entry-header__headline { font-size: 1.2rem; font-style: italic; font-weight: normal; margin-bottom: 0.5rem; }
    .article-meta { padding-bottom: 0.5rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .entry-header__thumbnail-wrapper img, .wp-block-image img { display: block; max-width: 100%; height: auto; }
    .entry-header__thumbnail div, .wp-element-caption { display: block; font-size: 0.8rem; margin-top: 0.2rem; }
    .wp-block-pullquote blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    .author-bio__content { font-style: italic; border-top: 1px solid black; padding-top: 0.5rem; padding-bottom: 0.5rem }
    """

    def preprocess_html(self, soup):
        paywall_ele = soup.find(name="meta", content="hard-paywall")
        if paywall_ele:
            err_msg = f'Article is paywalled: "{self.tag_to_string(soup.find("h1"))}"'
            self.log.warn(err_msg)
            self.abort_article(err_msg)

        # inject article meta element
        meta_ele = soup.new_tag("div", attrs={"class": "article-meta"})
        author_ele = soup.find(class_="writers-link")
        if author_ele:
            author_new_ele = soup.new_tag("span", attrs={"class": "author"})
            author_new_ele.append(self.tag_to_string(author_ele))
            meta_ele.append(author_new_ele)
            author_ele.decompose()

        cartoon_author_ele = soup.find(name="h2", class_="entry-header__author")
        if cartoon_author_ele:
            author_new_ele = soup.new_tag("span", attrs={"class": "author"})
            author_new_ele.append(self.tag_to_string(cartoon_author_ele))
            meta_ele.append(author_new_ele)
            cartoon_author_ele.decompose()

        pub_meta_ele = soup.find(name="meta", property="article:published_time")
        if pub_meta_ele:
            pub_date = parse_date(pub_meta_ele["content"])
            if (not self.pub_date) or pub_date > self.pub_date:
                self.pub_date = pub_date
            pub_date_ele = soup.new_tag("span", attrs={"class": "published-dt"})
            pub_date_ele.append(f"{pub_date:%-I:%M%p, %-d %b, %Y}")
            meta_ele.append(pub_date_ele)
        headline = soup.find(name="h2", class_="entry-header__headline") or soup.find(
            "h1"
        )
        headline.insert_after(meta_ele)
        mod_meta_ele = soup.find(name="meta", property="article:modified_time")
        if mod_meta_ele:
            mod_date = parse_date(mod_meta_ele["content"])
            if (not self.pub_date) or mod_date > self.pub_date:
                self.pub_date = mod_date
        return soup

    def parse_index(self):
        soup = self.index_to_soup("https://www.spectator.co.uk/magazine")
        cover_ele = soup.find("img", class_="magazine-header__image")
        if cover_ele:
            cover_url = cover_ele["src"]
            self.cover_url = urljoin(cover_url, urlparse(cover_url).path)
        issue_date_ele = soup.find(name="time", class_="magazine-header__date")
        if issue_date_ele:
            self.title = f"{_name}: {self.tag_to_string(issue_date_ele)}"

        feed = {}
        for sect_link in soup.select(
            "aside.magazine-issue__nav nav a.archive-entry__nav-link"
        ):
            sect_name = self.tag_to_string(sect_link)
            sect_soup = self.index_to_soup(sect_link["href"])
            feed[sect_name] = []
            for article_ele in sect_soup.select(".magazine-issue__group article"):
                feed[sect_name].append(
                    {
                        "title": self.tag_to_string(
                            article_ele.find(class_="article__title")
                        ),
                        "url": article_ele.find(name="a", class_="article__title-link")[
                            "href"
                        ],
                        "description": self.tag_to_string(
                            article_ele.find(class_="article__excerpt-text")
                        ),
                        "author": self.tag_to_string(
                            article_ele.find(class_="article__author")
                        ),
                    }
                )
        return feed.items()
