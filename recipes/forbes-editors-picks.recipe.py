import json
from datetime import datetime, timezone
from calibre.web.feeds.news import BasicNewsRecipe
from calibre.ebooks.BeautifulSoup import BeautifulSoup


_name = "Forbes - Editor's Picks"


class ForbesEditorsPicks(BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "Forbe's Editors' Picks https://www.forbes.com/editors-picks/"
    language = "en"
    encoding = "utf-8"

    no_javascript = True
    no_stylesheets = True
    compress_news_images = True
    scale_news_images = (800, 1200)
    timeout = 20
    timefmt = ""
    pub_date = None  # custom publication date

    keep_only_tags = [dict(name="article")]
    remove_attributes = ["style", "height", "width"]

    remove_tags = [
        dict(
            attrs={
                "class": [
                    "story-package__nav-wrapper",
                    "container__subnav--outer",
                    "edit-story-container",
                    "article-sharing",
                    "vert-pipe",
                    "short-bio",
                    "bottom-contrib-block",
                    "article-footer",
                    "sigfile",
                    "hidden",
                    "link-embed",
                    "subhead3-embed",
                    "recirc-module",
                    "seo",
                    "top-ad-container",
                ]
            }
        ),
        dict(name=["fbs-cordial", "fbs-ad", "svg"]),
    ]

    extra_css = """
    .top-label-wrapper a { margin-right: 0.5rem; color: #444; }
    .issue { font-weight: bold; margin-bottom: 0.2rem; }
    h1 { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .sub-headline { font-size: 1.2rem; font-style: italic; font-weight: normal; margin-bottom: 0.5rem; }
    .top-contrib-block { margin-top: 0.5rem; font-weight: bold; color: #444; }
    .content-data { margin-bottom: 1rem; font-weight: normal; color: unset; }
    .image-embed p { font-size: 0.8rem; margin-top: 0.2rem; margin-bottom: 0.5rem; }
    .image-embed img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    blockquote .text-align { font-size: 1rem; }
    """

    def publication_date(self):
        return self.pub_date

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        article = soup.find("article")
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            meta = json.loads(script.contents[0])
            if not (meta.get("@type") and meta["@type"] == "NewsArticle"):
                continue
            modified_date = meta.get("dateModified") or meta.get("datePublished")
            article["data-og-modified-date"] = modified_date
            article["data-og-description"] = meta.get("description", "")
            break
        for img in soup.find_all("progressive-image"):
            img.name = "img"
        return str(soup)

    def populate_article_metadata(self, article, soup, first):
        article_summary = soup.find(attrs={"data-og-description": True})
        if article_summary:
            article.text_summary = article_summary["data-og-description"]

        article_date = soup.find(attrs={"data-og-modified-date": True})
        if article_date:
            modified_date = datetime.fromisoformat(
                article_date["data-og-modified-date"]
            ).replace(tzinfo=timezone.utc)
            if (not self.pub_date) or modified_date > self.pub_date:
                self.pub_date = modified_date
                self.title = f"{_name}: {self.pub_date:%-d %b, %Y}"
            article.utctime = modified_date
            article.localtime = modified_date

    def parse_index(self):
        soup = self.index_to_soup("https://www.forbes.com/editors-picks/")
        pick_links = soup.select("section.channel h2 a") + soup.select(
            "section.channel h3 a"
        )
        articles = []
        for link in pick_links:
            articles.append({"title": self.tag_to_string(link), "url": link["href"]})
        return [(_name, articles)]
