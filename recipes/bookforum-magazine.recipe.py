import os
import sys
from urllib.parse import urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from mechanize import Request
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Bookforum"
_issue_url = ""


class BookforumMagazine(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = (
        "Bookforum is an American book review magazine devoted to books and "
        "the discussion of literature. https://www.bookforum.com/print"
    )
    language = "en"
    __author__ = "ping"
    publication_type = "magazine"
    compress_news_images_auto_size = 8

    keep_only_tags = [dict(class_="blog-article")]
    remove_tags = [dict(name=["af-share-toggle", "af-related-articles"])]

    extra_css = """
    .blog-article__header { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .blog-article__subtitle { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .blog-article__writer { font-size: 1rem; font-weight: bold; color: #444; }
    .blog-article__book-info { margin: 1rem 0; }
    .article-image-container img, .blog-article__publication-media img {
        display: block; max-width: 100%; height: auto;
    }
    .blog-article__caption { font-size: 0.8rem; display: block; margin-top: 0.2rem; }
    """

    def preprocess_html(self, soup):
        # strip away links that's not needed
        for ele in soup.select(".blog-article__header a"):
            ele.unwrap()
        return soup

    def parse_index(self):
        soup = self.index_to_soup(
            _issue_url if _issue_url else "https://www.bookforum.com/print"
        )
        meta_ele = soup.find("meta", property="og:title")
        if meta_ele:
            self.title = f'{_name}: {meta_ele["content"]}'

        cover_ele = soup.find("img", class_="toc-issue__cover")
        if cover_ele:
            self.cover_url = urljoin(
                "https://www.bookforum.com",
                soup.find("img", class_="toc-issue__cover")["src"],
            )
            # use cover image to get a published date
            br = self.get_browser()
            cover_res = br.open_novisit(
                Request(self.cover_url, timeout=self.timeout, method="HEAD")
            )
            cover_res_lastupdated = cover_res.get("last-modified", default=None)
            if cover_res_lastupdated:
                self.pub_date = self.parse_date(cover_res_lastupdated)

        articles = {}
        for sect_ele in soup.find_all("div", class_="toc-articles__section"):
            section_name = self.tag_to_string(
                sect_ele.find("a", class_="toc__anchor-links__link")
            )
            for article_ele in sect_ele.find_all("article"):
                title_ele = article_ele.find("h1")
                sub_title_ele = article_ele.find(class_="toc-article__subtitle")
                articles.setdefault(section_name, []).append(
                    {
                        "title": self.tag_to_string(title_ele),
                        "url": article_ele.find("a", class_="toc-article__link")[
                            "href"
                        ],
                        "description": self.tag_to_string(sub_title_ele)
                        if sub_title_ele
                        else "",
                    }
                )
        return articles.items()
