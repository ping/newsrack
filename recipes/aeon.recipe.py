# No longer working becauses css classes are dynamically generated
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title, get_date_format

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Aeon"


class Aeon(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    language = "en"
    description = (
        "A unique digital magazine, publishing some of the most profound and "
        "provocative thinking on the web. We ask the big questions and find "
        "the freshest, most original answers, provided by leading thinkers on "
        "science, philosophy, society and the arts. https://aeon.co/"
    )
    encoding = "utf-8"
    publication_type = "blog"
    masthead_url = "https://aeon.co/logo.png"
    oldest_article = 30
    max_articles_per_feed = 30
    compress_news_images_auto_size = 10

    remove_tags = [
        dict(
            class_=[
                "sc-8c8cfef8-0",
                "sc-114c07c9-0",
                "sc-50e6fb3a-1",
                "sc-c3e98e6e-0",
                "sc-fd74dcf9-14",
                "sc-50e6fb3a-1",
                "sc-fd74dcf9-24",
                "sc-a70232b9-5",
            ]
        ),
        dict(attrs={"data-test": "footer"}),
    ]
    remove_attributes = ["align", "style", "width", "height"]

    extra_css = """
    p .sc-2e8621ab-1 { margin-left: 0.5rem; }
    .sc-fd74dcf9-18 { margin-right: 0.6rem; }
    img.ld-image-block, img.lede-img, .sc-358cfb18-0 img { display: block; max-width: 100%; height: auto; }
    .ld-image-caption { font-size: 0.8rem; }
    """
    feeds = [(_name, "https://aeon.co/feed.rss")]

    def _find_article(self, data):
        if isinstance(data, dict):
            return data.get("@type", "") == "Article"
        return False

    def preprocess_raw_html_(self, raw_html, url):
        soup = self.soup(raw_html)
        article = self.get_ld_json(soup, filter_fn=self._find_article)
        if not (article and article.get("articleBody")):
            err_msg = f"Unable to find article: {url}"
            self.log.warning(err_msg)
            self.abort_article(err_msg)

        # "%Y-%m-%d"
        published_date = self.parse_date(article["datePublished"])
        if (not self.pub_date) or published_date > self.pub_date:
            self.pub_date = published_date
            self.title = format_title(_name, published_date)

        # display article date
        header = soup.find("h1") or soup.find("h2")
        if header:
            date_ele = soup.new_tag("div", attrs={"class": "custom-date-published"})
            date_ele.append(f"{published_date:{get_date_format()}}")
            header.insert_after(date_ele)

        # re-position header image
        essay_header = soup.find("div", class_="sc-fd74dcf9-26")
        if essay_header:
            header_img = essay_header.find("img")
            attribution = essay_header.find("div", class_="sc-b78f3ea9-3")
            if header_img and attribution:
                header_img["class"] = "lede-img"
                attribution.insert_before(header_img.extract())
            clean_up_ele = essay_header.find(class_="sc-358cfb18-6")
            if clean_up_ele:
                clean_up_ele.decompose()

        byline = soup.find("div", class_="rah-static")
        if byline:
            for br in byline.find_all("br"):  # extraneous br
                br.decompose()

        for link_class in (
            "a.sc-2e8621ab-1",  # author link
            "a.sc-fd74dcf9-18",  # article cat
        ):
            for a in soup.select(link_class):  # tags
                a.name = "span"
        return str(soup)

    def parse_feeds(self):
        return self.group_feeds_by_date(
            filter_article=lambda a: "/videos/" not in a.url
        )
