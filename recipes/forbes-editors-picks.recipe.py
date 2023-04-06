import json
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe

_name = "Forbes - Editor's Picks"


class ForbesEditorsPicks(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "Forbe's Editors' Picks https://www.forbes.com/editors-picks/"
    language = "en"
    encoding = "utf-8"

    oldest_article = 7
    max_articles_per_feed = 15

    scale_news_images = (800, 1200)
    timeout = 10
    simultaneous_downloads = 1

    keep_only_tags = [dict(name="article")]
    remove_attributes = ["style", "height", "width"]

    remove_tags = [
        dict(
            class_=[
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
                "speakr-wrapper",
            ]
        ),
        dict(name=["fbs-cordial", "fbs-ad", "svg"]),
    ]

    extra_css = """
    .top-label-wrapper a { margin-right: 0.5rem; color: #444; }
    .issue { font-weight: bold; margin-bottom: 0.2rem; }
    h1 { font-size: 1.8rem; margin-bottom: 0.4rem; }
    h2.subhead-embed { font-size: 1.2rem; font-style: italic; font-weight: normal; margin-bottom: 0.5rem; }
    h2.subhead-embed strong { font-weight: normal; }
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

    def preprocess_raw_html(self, raw_html, url):
        soup = BeautifulSoup(raw_html)
        article = soup.find("article")
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            meta = json.loads(script.contents[0])
            if not (meta.get("@type") and meta["@type"] == "NewsArticle"):
                continue
            modified_date = meta.get("dateModified") or meta.get("datePublished")
            article["data-og-modified-date"] = modified_date
            break
        for img in soup.find_all("progressive-image"):
            img.name = "img"
        return str(soup)

    def populate_article_metadata(self, article, soup, first):
        article_date = soup.find(attrs={"data-og-modified-date": True})
        if article_date:
            modified_date = datetime.fromisoformat(
                article_date["data-og-modified-date"]
            ).replace(tzinfo=timezone.utc)
            if (not self.pub_date) or modified_date > self.pub_date:
                self.pub_date = modified_date
                self.title = format_title(_name, self.pub_date)
            article.utctime = modified_date
            article.localtime = modified_date

    def parse_index(self):
        br = self.get_browser()
        cutoff_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(
            days=self.oldest_article
        )
        articles = []

        date_param = 0
        content_ids = None
        end_feed = False
        while not end_feed:
            query = {
                "limit": 25,
                "sourceValue": "editors-pick",
                "streamSourceType": "badge",
            }
            if content_ids:
                query["ids"] = content_ids
            if date_param:
                query["date"] = date_param

            endpoint = (
                f"https://www.forbes.com/simple-data/chansec/stream/?{urlencode(query)}"
            )

            res = br.open_novisit(endpoint)
            res_obj = json.loads(res.read().decode("utf-8"))
            items = res_obj.get("blocks", {}).get("items", [])
            if not items:
                break

            for item in items:
                item_date = datetime.utcfromtimestamp(item["date"] / 1000.0).replace(
                    tzinfo=timezone.utc
                )
                if item_date < cutoff_date:
                    end_feed = True
                    break

                if (not self.pub_date) or item_date > self.pub_date:
                    self.pub_date = item_date
                    self.title = format_title(_name, self.pub_date)

                articles.append(
                    {
                        "title": item["title"],
                        "url": item["url"],
                        "description": item["description"],
                        "date": item_date,
                    }
                )
                date_param = item["date"]
                content_ids = item["id"]
                if len(articles) >= self.max_articles_per_feed:
                    end_feed = True
                    break

        return [(_name, articles)]
