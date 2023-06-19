import os
import sys
from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Kirkus"


class Kirkus(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = "Kirkus Reviews is an American book review magazine founded in 1933 by Virginia Kirkus. The magazine is headquartered in New York City. https://www.kirkusreviews.com/magazine/current/"
    language = "en"
    __author__ = "ping"
    publication_type = "magazine"
    encoding = "utf-8"
    masthead_url = (
        "https://d1fd687oe6a92y.cloudfront.net/img/kir_images/logo/kirkus-nav-logo.svg"
    )
    max_articles_per_feed = 99
    use_embedded_content = False
    compress_news_images_auto_size = 6
    auto_cleanup = False
    keep_only_tags = [
        dict(
            class_=[
                "article-author",
                "article-author-img-start",
                "article-author-description-start",
                "single-review",
            ]
        )
    ]
    remove_tags = [
        dict(
            class_=[
                "sidebar-content",
                "article-social-share-desktop-first",
                "article-social-share-desktop-pagination",
                "article-social-share-mobile",
                "share-review-text",
                "like-dislike-article",
                "rate-this-book-text",
                "input-group",
                "user-comments",
                "show-all-response-text",
                "button-row",
                "hide-on-mobile",
                "related-article",
            ]
        )
    ]
    remove_tags_after = [dict(class_="single-review")]

    extra_css = """
    .image-container img { max-width: 100%; height: auto; margin-bottom: 0.2rem; }
    .photo-caption { font-size: 0.8rem; margin-bottom: 0.5rem; display: block; }
    .book-review-img .image-container { text-align: center; }
    .book-rating-module .description-title { font-size: 1.25rem; margin-left: 0; text-align: center; }
    """

    def preprocess_html(self, soup):
        h1 = soup.find(class_="article-title")
        book_cover = soup.find("ul", class_="book-review-img")
        if book_cover:
            for li in book_cover.find_all("li"):
                li.name = "div"
            book_cover.name = "div"
            if h1:
                book_cover.insert_before(h1.extract())

        return soup

    def parse_index(self):
        issue_url = "https://www.kirkusreviews.com/magazine/current/"
        soup = self.index_to_soup(issue_url)
        issue = soup.find(name="article", class_="issue-container")
        cover_img = issue.select(".issue-header .cover-image img")
        if cover_img:
            self.cover_url = cover_img[0]["src"]

        h1 = issue.find("h1")
        if h1:
            edition = self.tag_to_string(h1)
            self.title = f"{_name}: {edition}"
            # Example: April 1, 2023 "%B %d, %Y"
            self.pub_date = self.parse_date(edition)

        articles = {}
        for book_ele in soup.find_all(name="div", class_="issue-featured-book"):
            link = book_ele.find("a")
            if not link:
                continue
            section = self.tag_to_string(book_ele.find("h3")).upper()
            if section not in articles:
                articles[section] = []
            articles[section].append(
                {"url": urljoin(issue_url, link["href"]), "title": link["title"]}
            )
        for post_ele in issue.select("div.issue-more-posts ul li div.lead-text"):
            link = post_ele.find("a")
            if not link:
                continue
            section = self.tag_to_string(post_ele.find(class_="lead-text-type")).upper()
            if section not in articles:
                articles[section] = []
            articles[section].append(
                {
                    "url": urljoin(issue_url, link["href"]),
                    "title": self.tag_to_string(link),
                }
            )

        for section_ele in issue.select("section.reviews-section"):
            section_articles = []
            for review in section_ele.select("ul li.starred"):
                link = review.select("h4 a")
                if not link:
                    continue
                description = review.find("p")
                section_articles.append(
                    {
                        "url": urljoin(issue_url, link[0]["href"]),
                        "title": self.tag_to_string(link[0]),
                        "description": ""
                        if not description
                        else self.tag_to_string(description),
                    }
                )
            if not section_articles:
                continue
            section = self.tag_to_string(section_ele.find("h3")).upper()
            if section not in articles:
                articles[section] = []
            articles[section].extend(section_articles)

        return articles.items()
