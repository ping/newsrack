"""
ft.com
"""
# Original from https://github.com/kovidgoyal/calibre/blob/902e80ec173bc40037efb164031043994044ec6c/recipes/financial_times_print_edition.recipe

import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import format_title

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe, classes

_name = "Financial Times (Print)"


class FinancialTimesPrint(BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Today's Financial Times https://www.ft.com/todaysnewspaper/international"
    )
    publisher = "The Financial Times Ltd."
    language = "en_GB"
    category = "news, finance, politics, UK, World"
    publication_type = "newspaper"
    oldest_article = 1  # days
    use_embedded_content = False
    encoding = "utf-8"
    remove_javascript = True
    no_stylesheets = True
    auto_cleanup = False
    masthead_url = "https://www.ft.com/partnercontent/content-hub/static/media/ft-horiz-new-black.215c1169.png"
    ignore_duplicate_articles = {"url"}

    compress_news_images = True
    compress_news_images_auto_size = 6
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images

    timeout = 20
    timefmt = ""
    pub_date = None  # custom publication date

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.5rem; }
    .sub-headline { margin-bottom: 0.4rem;  font-size: 1.2rem; font-style: italic; }
    .article-meta { margin-top: 1rem; padding-bottom: 0.2rem; }
    .article-meta .author { font-weight: bold; color: #444; }
    .article-meta .published-dt { margin-left: 0.5rem; }
    .article-img { margin-bottom: 0.8rem; }
    .article-img img { display: block; margin-bottom: 0.3rem; max-width: 100%; }
    .article-img .caption { font-size: 0.8rem; }
    """

    def parse_index(self):
        soup = self.index_to_soup("https://www.ft.com/todaysnewspaper/international")
        # UK edition: https://www.ft.com/todaysnewspaper/uk
        # International edition: https://www.ft.com/todaysnewspaper/international
        ans = self.ft_parse_index(soup)
        if not ans:
            is_sunday = datetime.now(timezone.utc).weekday() == 6
            if is_sunday:
                err_msg = "The Financial Times Newspaper is not published on Sundays."
                self.log.warn(err_msg)
                raise ValueError(err_msg)
            else:
                err_msg = "The Financial Times Newspaper is not published today."
                self.log.warn(err_msg)
                raise ValueError(err_msg)
        return ans

    def ft_parse_index(self, soup):
        feeds = []
        for section in soup.findAll(**classes("o-teaser-collection")):
            h2 = section.find("h2")
            secname = self.tag_to_string(h2)
            self.log(secname)
            articles = []
            for a in section.findAll(
                "a", href=True, **classes("js-teaser-heading-link")
            ):
                url = urljoin("https://www.ft.com", a["href"])
                title = self.tag_to_string(a)
                desc_parent = a.findParent("div")
                div = desc_parent.find_previous_sibling(
                    "div", **classes("o-teaser__meta")
                )
                if div is not None:
                    desc = div.find("a", **classes("o-teaser__tag"))
                    desc = self.tag_to_string(desc)
                    prefix = div.find("span", **classes("o-teaser__tag-prefix"))
                    if prefix is not None:
                        prefix = self.tag_to_string(prefix)
                        desc = prefix + " " + desc
                    articles.append({"title": title, "url": url, "description": desc})
                    self.log("\t", desc)
                    self.log("\t", title)
                    self.log("\t\t", url)
            if articles:
                feeds.append((secname, articles))
        return feeds

    def preprocess_raw_html(self, raw_html, url):
        article = None
        soup = BeautifulSoup(raw_html)
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            article = json.loads(script.contents[0])
            if not (article.get("@type") and article["@type"] == "NewsArticle"):
                continue
            break
        if not (article and article.get("articleBody")):
            err_msg = f"Unable to find article: {url}"
            self.log.warn(err_msg)
            self.abort_article(err_msg)

        try:
            author = article.get("author", {}).get("name", "")
        except AttributeError:
            author = ", ".join([a["name"] for a in article.get("author", [])])

        date_published = article.get("datePublished", None)
        if date_published:
            # Example: 2022-03-29T04:00:05.154Z
            date_published = datetime.strptime(
                date_published, "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=timezone.utc)
            if (not self.pub_date) or date_published > self.pub_date:
                self.pub_date = date_published
                self.title = format_title(_name, date_published)

        paragraphs = []
        lede_image_url = article.get("image", {}).get("url")
        if lede_image_url:
            paragraphs.append(
                f'<p class="article-img"><img src="{lede_image_url}"></p>'
            )
        for para in article["articleBody"].split("\n\n"):
            if para.startswith("RECOMMENDED"):  # skip recommended inserts
                continue
            if "NEWSLETTER" in para:
                continue
            para = para.replace("\n", " ")
            mobj = re.findall(
                r"^(?P<caption>.*)\[(?P<img_url>https://.+\.(jpg|png))\]",
                para,
            )
            if mobj:
                for caption, img_url, _ in mobj:
                    # reduced image size
                    new_img_url = f"https://www.ft.com/__origami/service/image/v2/images/raw/{quote_plus(img_url)}?fit=scale-down&source=next&width=700"
                    # replace the image tag
                    para = para.replace(
                        f"{caption}[{img_url}]",
                        f"""<div class="article-img">
                            <img src="{new_img_url}" title="{caption}">
                            <span class="caption">{caption}</span>
                            </div>""",
                    )
            para = f"<p>{para}</p>"
            paragraphs.append(para)
        article_body = "\n".join(paragraphs)

        html_output = f"""<html><head><title>{article["headline"]}</title></head>
        <body>
            <article data-og-link="{url}">
            <h1 class="headline">{article["headline"]}</h1>
            {"" if not article.get("description") else '<div class="sub-headline">' + article.get("description", "") + '</div>'}
            <div class="article-meta">
                <span class="author">{author}</span>
                <span class="published-dt">{date_published:%-d %B, %Y}</span>
            </div>
            {article_body}
            </article>
        </body></html>
        """
        return html_output

    def publication_date(self):
        return self.pub_date

    def get_browser(self, *a, **kw):
        kw[
            "user_agent"
        ] = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        br = BasicNewsRecipe.get_browser(self, *a, **kw)
        br.addheaders = [("referer", "https://www.google.com/")]
        return br
