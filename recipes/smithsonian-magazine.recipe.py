import json
import os
import sys
from urllib.parse import urljoin, urlparse

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
try:
    from recipes_shared import BasicNewsrackRecipe
except ImportError:
    # just for Pycharm to pick up for auto-complete
    from includes.recipes_shared import BasicNewsrackRecipe

from calibre.web.feeds.news import BasicNewsRecipe, classes, prefixed_classes
from calibre.utils.date import parse_date

_name = "Smithsonian Magazine"


class SmithsonianMagazine(BasicNewsrackRecipe, BasicNewsRecipe):

    title = _name
    __author__ = "ping"

    description = "This magazine chronicles the arts, environment, sciences and popular culture of the times. It is edited for modern, well-rounded individuals with diverse, general interests. https://www.smithsonianmag.com/"  # noqa
    masthead_url = "https://www.smithsonianmag.com/static/smithsonianmag/img/smithsonian_magazine_logo_black.46435ad4efd4.svg"
    language = "en"
    category = "news"
    encoding = "UTF-8"
    BASE = "https://www.smithsonianmag.com/"

    compress_news_images_auto_size = 10

    keep_only_tags = [classes("main-hero main-content")]
    remove_tags = [
        classes(
            "tag-list recommended-videos comments amazon-associated-product affiliateLink "
            "mobile-heading author-headshot binding-box"
        ),
        prefixed_classes("widget-"),
    ]
    extra_css = """
    .category-label h2 { font-size: 1rem; }
    h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
    p.subtitle { font-size: 1.2rem; font-style: italic; font-weight: normal; margin-bottom: 0.5rem; margin-top: 0; }
    .author-text { color: #444; margin-top: 1rem; margin-bottom: 1rem; }
    .author-text p.author { font-weight: bold; display: inline-block; margin-top: 0; margin-bottom: 0; }
    .author-text p.author-short-bio { display: inline-block; }
    .author-text time { display: inline-block;  margin-left: 1rem; }
    .caption { font-size: 0.8rem; margin-top: 0.2rem; margin-bottom: 0.5rem; }
    img { max-width: 100%; height: auto; }
    """

    def preprocess_html(self, soup):
        for hr in soup.select(".category-label hr") + soup.select(".article-line hr"):
            hr.decompose()
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            article = json.loads(script.contents[0])
            date_modified = parse_date(article["dateModified"])
            if (not self.pub_date) or date_modified > self.pub_date:
                self.pub_date = date_modified
        return soup

    def populate_article_metadata(self, article, soup, first):
        h1 = soup.find("h1")
        if h1:
            # we update the title from the article because
            # the issue page often uses an alternative title
            article.title = self.tag_to_string(h1)

    def parse_index(self):
        soup = self.index_to_soup(self.BASE)
        curr_issue_ele = soup.find("div", class_="current-issue")
        self.title = f'{_name}: {self.tag_to_string(curr_issue_ele.find("time"))}'
        issue_url = urljoin(
            self.BASE, curr_issue_ele.select(".issue-left a")[0]["href"]
        )
        soup = self.index_to_soup(issue_url)
        try:
            # ultra high-res cover
            cover_url_parsed = urlparse(soup.select(".issue-cover img")[0]["src"])
            cover_url = cover_url_parsed.path[cover_url_parsed.path.index("https://") :]
            self.log(f"Cover url: {cover_url}")
        except:  # noqa
            cover_url = soup.select(".issue-cover img")[0]["src"]
        self.cover_url = cover_url

        articles = []
        for article in soup.select(".article-list .article-wrapper"):
            article_link = article.select_one(".headline a")
            description = ""
            summary = article.find("p", class_="summary")
            if summary:
                description = self.tag_to_string(summary)
            articles.append(
                {
                    "title": self.tag_to_string(article_link),
                    "url": urljoin(self.BASE, article_link["href"]),
                    "description": description,
                }
            )
        return [(_name, articles)]
