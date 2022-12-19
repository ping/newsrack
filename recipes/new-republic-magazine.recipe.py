"""
newrepublic.com
"""
import json
from datetime import datetime
from functools import cmp_to_key
from urllib.parse import urljoin, urlencode, urlsplit

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe

_name = "The New Republic Magazine"


def sort_section(a, b, sections_sort):
    try:
        a_index = sections_sort.index(a["section"])
    except ValueError:
        a_index = 999
    try:
        b_index = sections_sort.index(b["section"])
    except ValueError:
        b_index = 999

    if a_index < b_index:
        return -1
    if a_index > b_index:
        return 1
    if a_index == b_index:
        if a["section"] == b["section"]:
            return -1 if a["date"] < b["date"] else 1
        return -1 if a["section"] < b["section"] else 1


class NewRepublicMagazine(BasicNewsRecipe):
    title = _name
    language = "en"
    __author__ = "ping"
    oldest_article = 62  # days
    max_articles_per_feed = 30
    description = (
        "Founded in 1914, The New Republic is a media organization dedicated to addressing "
        "today’s most critical issues. https://newrepublic.com/magazine"
    )
    publication_type = "magazine"
    no_stylesheets = True
    use_embedded_content = False
    masthead_url = "https://images.newrepublic.com/f5acdc0030e3212e601040dd24d5c2c0c684b15f.png?w=1024&q=65&dpi=1&fit=crop&crop=faces&h=512"
    remove_attributes = ["height", "width"]
    ignore_duplicate_articles = {"title", "url"}
    remove_empty_feeds = True

    compress_news_images = True
    compress_news_images_auto_size = 6
    scale_news_images = (800, 1200)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    timeout = 20
    timefmt = ""
    pub_date = None  # custom publication date

    BASE_URL = "https://newrepublic.com"

    extra_css = """
    h1.headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    h2.subheadline { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .article-meta {  margin-bottom: 1rem; }
    .article-meta span { display: inline-block; font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-meta span:last-child { font-weight: normal; }
    div.pullquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    .lede-media img, .article-embed img, img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    .lede-media .caption, .article-embed .caption { font-size: 0.8rem; }
    div.author-bios { margin-top: 2rem; font-style: italic; color: #444; border-top: solid 1px #444; }
    """

    def publication_date(self):
        return self.pub_date

    def _urlize(self, url_string, base_url=None):
        if url_string.startswith("//"):
            url_string = "https:" + url_string
        if url_string.startswith("/"):
            url_string = urljoin(base_url or self.BASE_URL, url_string)
        return url_string

    def _article_endpoint(self, nid):
        query = """
query ($id: ID, $nid: ID) {
  Article(id: $id, nid: $nid) {
    ...ArticlePageFields
  }
}
fragment ArticlePageFields on Article {
  id
  nid
  slug
  title
  cleanTitle
  badge
  frontPage {
    id
    slug
    title
  }
  LinkedSeriesId
  authors {
    id
    name
    slug
    blurb
    meta {
      twitter
    }
  }
  body
  publishedAt
  displayAt
  publicPublishedDate
  status
  ledeImage {
    id
    src
    format
    width
    height
    alt
  }
  ledeAltImage {
    id
    src
    format
    width
    height
    alt
  }
  url
  urlFull
  meta {
    wordCount
    template
    navigationTheme
    bigLede
    hideLede
    cropModeFronts
    ledeOverrideSource
    disableAds
  }
  ledeImageCredit
  ledeImageCreditBottom
  ledeImageRealCaption
  bylines
  deck
  type
  galleries {
    id
    galleryData {
      captionText
      creditText
      image {
        id
        src
        width
        height
      }
    }
  }
  tags {
    id
    slug
    label
  }
}"""
        variables = {"nid": str(nid)}
        params = {"query": query, "variables": json.dumps(variables)}
        return f"https://newrepublic.com/graphql?{urlencode(params)}"

    def _resize_image(self, image_url, width, height):
        max_width = 800
        crop_params = {
            "auto": "compress",
            "ar": f"{width}:{height}",
            "fm": "jpg",
            "fit": "crop",
            "crop": "faces",
            "ixlib": "react-9.0.2",
            "dpr": 1,
            "q": 65,
            "w": max_width,
        }
        url_tuple = urlsplit(image_url)
        return f"{url_tuple.scheme}://{url_tuple.netloc}{url_tuple.path}?{urlencode(crop_params)}"

    def populate_article_metadata(self, article, soup, first):
        # pick up the og link from preprocess_raw_html() and set it as url instead of the api endpoint
        og_link = soup.select("[data-og-link]")
        if og_link:
            article.url = og_link[0]["data-og-link"]

    def preprocess_raw_html(self, raw_html, url):
        # formulate the api response into html
        article = json.loads(raw_html)["data"]["Article"]
        # Example: 2022-08-12T10:00:00.000Z
        date_published_loc = datetime.strptime(
            article["publishedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        # authors
        author_bios_html = ""
        post_authors = []
        try:
            post_authors = [a["name"] for a in article.get("authors", [])]
            if post_authors:
                author_bios_html = f'<div class="author-bios">{"".join([a.get("blurb", "") for a in article.get("authors", [])])}</div>'
        except (KeyError, TypeError):
            pass

        # lede image
        lede_image_html = ""
        if article.get("ledeImage"):
            img = article["ledeImage"]
            lede_img_url = self._resize_image(
                self._urlize(img["src"]), img["width"], img["height"]
            )
            lede_image_html = f"""<p class="lede-media">
                <img src="{lede_img_url}">
                {f'<span class="caption">{article["ledeImageRealCaption"]}</span>' if article.get("ledeImageRealCaption") else ""}
            </p>"""

        return f"""<html>
        <head><title>{article["cleanTitle"]}</title></head>
        <body>
            <article data-og-link="{article["urlFull"]}">
            <h1 class="headline">{article["cleanTitle"]}</h1>
            {('<h2 class="subheadline">' + article["deck"] + "</h2>") if article.get("deck") else ""}
            <div class="article-meta">
                {f'<span class="author">{", ".join(post_authors)}</span>' if post_authors else ""}
                <span class="published-dt">
                    {date_published_loc:%-d %b, %Y}
                </span>
            </div>
            {lede_image_html}
            {article["body"]}
            {author_bios_html}
            </article>
        </body></html>"""

    def parse_index(self):
        br = self.get_browser()
        res = br.open_novisit("https://newrepublic.com/api/content/magazine")
        magazine = json.loads(res.read().decode("utf-8"))["data"]
        self.pub_date = datetime.fromisoformat(magazine["metaData"]["publishedAt"])
        self.log.debug(f'Found issue: {magazine["metaData"]["issueTag"]["text"]}')
        self.title = f'{_name}: {magazine["metaData"]["issueTag"]["text"]}'
        self.cover_url = self._urlize(magazine["metaData"]["image"]["src"])

        feed_articles = []
        for k, articles in magazine.items():
            if not k.startswith("magazine"):
                continue
            if not articles:
                continue
            try:
                for article in articles:
                    self.log.debug(f'Found article: {article["title"]}')
                    feed_articles.append(
                        {
                            "url": self._article_endpoint(article["nid"]),
                            "title": article["title"].replace("\n", " "),
                            "description": article.get("deck", ""),
                            "date": article["publishedAt"],
                            "section": k[len("magazine") :],
                        }
                    )
            except TypeError:
                # not iterable
                pass

        sort_sections = [
            "Cover",
            "Editorsnote",
            "Features",
            "StateOfTheNation",
            "ResPublica",
            "Columns",
            "Upfront",
            "Backstory",
            "SignsAndWonders",
            "Usandtheworld",
            "Exposure",
        ]
        sort_category_key = cmp_to_key(lambda a, b: sort_section(a, b, sort_sections))
        return [(_name, sorted(feed_articles, key=sort_category_key))]
