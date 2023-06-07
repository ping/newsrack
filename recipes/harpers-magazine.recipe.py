import os
import sys
from datetime import datetime
from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre import browser
from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Harper's Magazine"
_issue_url = ""


class HarpersMagazine(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "The oldest general-interest monthly in America, explores the "
        "issues that drive our national conversation, through long-form "
        "narrative journalism and essays, and such celebrated features "
        "as the iconic Harper’s Index. https://harpers.org/issues/"
    )
    language = "en"
    encoding = "utf-8"
    masthead_url = "https://harpers.org/wp-content/themes/timber/assets/img/logo.svg"
    publication_type = "magazine"
    use_embedded_content = False
    auto_cleanup = False
    base_url = "https://harpers.org"
    compress_news_images_auto_size = 8

    keep_only_tags = [dict(class_=["article-content"])]
    remove_tags = [
        dict(
            class_=[
                "component-newsletter-signup",
                "sidebar",
                "header-meta",
                "component-from-author",
                "from-issue",
                "d-none",
                "COA_roles_fix_space",
                "section-tags",
            ]
        )
    ]
    remove_attributes = ["style", "width", "height"]

    extra_css = """
    h1.article-title { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .subheading, .post-subtitle { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .byline { margin-bottom: 1rem; color: #444; }
    .article-hero-img img, .flex-section-image img, .wp-caption img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    .wp-caption-text { font-size: 0.8rem; margin-top: 0.3rem; }
    blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    .author-bio { margin-top: 2.5rem; font-style: italic; }
    .author-bio em { font-weight: bold; }
    """

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        soup.find("meta", attrs={"property": "article:modified_time"})
        print("*" * 10, soup.find("meta", attrs={"property": "article:modified_time"}))

        # Example: 2023-05-16T16:43:24+00:00
        post_date = datetime.strptime(
            (
                soup.find("meta", attrs={"property": "article:modified_time"})
                or soup.find("meta", attrs={"property": "article:published_time"})
            )["content"],
            "%Y-%m-%dT%H:%M:%S%z",
        )
        if (not self.pub_date) or post_date > self.pub_date:
            self.pub_date = post_date

        return str(soup)

    def preprocess_html(self, soup):
        # tweak ui elements
        subheading_ele = soup.find(class_="subheading")
        byline_ele = soup.find(class_="byline")
        if byline_ele and subheading_ele:
            byline_ele.insert_before(subheading_ele.extract())

        for bio in soup.find_all(class_="author-bio"):
            for dec_ele in bio.find_all("br"):
                dec_ele.decompose()
            for unwrap_ele in bio.find_all("p") + bio.find_all("a"):
                unwrap_ele.unwrap()

        return soup

    def parse_index(self):
        if not _issue_url:
            issues_soup = self.index_to_soup("https://harpers.org/issues/")
            curr_issue_a_ele = issues_soup.select_one("div.issue-card a")
            curr_issue_url = urljoin(self.base_url, curr_issue_a_ele["href"])
        else:
            curr_issue_url = _issue_url

        soup = self.index_to_soup(curr_issue_url)
        self.title = f'{_name}: {self.tag_to_string(soup.find("h1", class_="issue-heading")).strip()}'
        self.cover_url = soup.find("img", class_="cover-img")["src"]

        articles = []
        for card in soup.find_all("div", class_="article-card"):
            title_ele = card.find(class_="ac-title")
            if not title_ele:
                continue
            article_url = card.find("a")["href"]
            article_title = self.tag_to_string(title_ele)
            article_description = (
                f'{self.tag_to_string(card.find(class_="ac-tax"))} '
                f'{self.tag_to_string(card.find(class_="ac-subtitle"))}'
            ).strip()
            articles.append(
                {
                    "url": article_url,
                    "title": article_title,
                    "description": article_description,
                }
            )
        return [(_name, articles)]

    # Harper's changes the content it delivers based on cookies, so the
    # following ensures that we send no cookies
    def get_browser(self, *args, **kwargs):
        return self

    def clone_browser(self, *args, **kwargs):
        return self.get_browser()

    def open_novisit(self, *args, **kwargs):
        br = browser()
        return br.open_novisit(*args, **kwargs)

    open = open_novisit
