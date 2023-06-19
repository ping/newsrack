"""
www.wired.com
"""
# Original at https://github.com/kovidgoyal/calibre/blob/b27ac9936f1ba2f0ada94ef729e41f1262958f87/recipes/wired.recipe
__license__ = "GPL v3"
__copyright__ = "2014, Darko Miletic <darko.miletic at gmail.com>"

import os
import sys

from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicCookielessNewsrackRecipe, format_title

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe, classes

_name = "Wired Magazine"


class WiredMagazine(BasicCookielessNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = (
        "Darko Miletic, update by Howard Cornett, Zach Lapidus, Michael Marotta"
    )
    description = (
        "Wired is a full-color monthly American magazine, "
        "published in both print and online editions, that "
        "reports on how emerging technologies affect culture, "
        "the economy and politics. "
        "Monthly edition, best run at the start of every month."
        " https://www.wired.com/magazine/"
    )
    publisher = "Conde Nast"
    category = "news, IT, computers, technology"
    encoding = "utf-8"
    language = "en"
    masthead_url = "https://www.wired.com/verso/static/wired/assets/logo-header.a7598835a549cb7d5ce024ef0710935927a034f9.svg"

    oldest_article = 45
    max_articles_per_feed = 200

    use_embedded_content = False
    remove_empty_feeds = True
    ignore_duplicate_articles = {"url"}

    BASE_URL = "https://www.wired.com"

    extra_css = """
    [data-testid="ContentHeaderRubricDateBlock"] > div { display: inline-block; margin-right: 0.5rem; }
    [data-testid="BylinesWrapper"], [data-testid="ContentHeaderRubricDateBlock"] {
        display: inline-block; margin-right: 0.5rem;
    }
    h1[data-testid="ContentHeaderHed"] { font-size: 1.8rem; margin-bottom: 0.5rem; }
    [data-testid="ContentHeaderAccreditation"] { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .article-meta {  margin-top: 1rem; margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; display: inline-block; }
    .article-meta .published-dt { display: inline-block; margin-left: 0.5rem; }
    .category { text-transform: uppercase; font-size: 0.85rem; font-weight: bold; color: #444; display: block; }
    picture img { max-width: 100%; height: auto; }
    div.caption { font-size: 0.8rem; margin-top: 0.2rem; }
    .custom-aside { margin-left: 0.5rem; margin-right: 0.5rem; font-size: 1.25rem; color: #444; text-align: center; }
    """

    keep_only_tags = [
        classes("article__content-header content-header lead-asset article__body"),
    ]
    remove_tags = [
        classes(
            "related-cne-video-component tags-component callout--related-list iframe-embed podcast_storyboard"
            " inset-left-component ad consumer-marketing-component social-icons lead-asset__content__clip"
        ),
        dict(name=["meta", "link"]),
        dict(id=["sharing", "social", "article-tags", "sidebar"]),
        dict(attrs={"data-testid": ["ContentHeaderRubric", "GenericCallout"]}),
    ]

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        pub_date_meta = soup.find(
            name="meta", attrs={"property": "article:published_time"}
        )
        # "%Y-%m-%dT%H:%M:%S.%fZ"
        post_date = self.parse_date(pub_date_meta["content"])
        if not self.pub_date or post_date > self.pub_date:
            self.pub_date = post_date
            self.title = format_title(_name, post_date)

        authors = [b.text for b in soup.find_all(attrs={"class": "byline__name-link"})]
        category = soup.find(attrs={"class": "rubric"}).text
        authors_div = soup.new_tag("div", attrs={"class": "author"})
        authors_div.append(", ".join(authors))
        category_div = soup.new_tag("div", attrs={"class": "category"})
        category_div.append(category)
        pub_div = soup.new_tag("div", attrs={"class": "published-dt"})
        pub_div.append(f"{post_date:%B %d, %Y %H:%M %p}")
        meta_div = soup.new_tag("div", attrs={"class": "article-meta"})
        meta_div.append(authors_div)
        meta_div.append(pub_div)
        header = soup.find(
            attrs={"data-testid": "ContentHeaderAccreditation"}
        ) or soup.find("h1")
        header.insert_after(meta_div)
        soup.find("h1").insert_before(category_div)
        return str(soup)

    def preprocess_html(self, soup):
        for picture in soup.find_all("picture"):
            # take <img> tag out of <noscript> into <picture>
            noscript = picture.find(name="noscript")
            if not noscript:
                continue
            img = noscript.find(name="img")
            if not img:
                continue
            picture.append(img.extract())
            noscript.decompose()
        for aside in soup.find_all("aside"):
            # tag aside with custom css class
            aside["class"] = aside.get("class", []) + ["custom-aside"]
        return soup

    def parse_wired_index_page(self, current_url, seen):
        self.log("Parsing index page", current_url)
        soup = self.index_to_soup(current_url)
        for a in soup.find("div", {"class": "multi-packages"}).findAll("a", href=True):
            url = a["href"]
            if url.startswith("/story") and url.endswith("/"):
                title = self.tag_to_string(a.parent.find("h3"))
                description = None
                summary = a.parent.find(attrs={"class": "summary-item__dek"})
                if summary:
                    description = self.tag_to_string(summary)
                if title.lower() != "read more" and title and url not in seen:
                    seen.add(url)
                    self.log("Found article:", title)
                    yield {
                        "title": title,
                        "url": urljoin(self.BASE_URL, url),
                        "description": description,
                    }

    def parse_index(self):
        articles = []
        seen = set()
        for pagenum in range(1, 2):
            articles.extend(
                self.parse_wired_index_page(
                    f"{self.BASE_URL}/magazine/?page={pagenum}", seen
                )
            )
        return [(_name, articles)]
