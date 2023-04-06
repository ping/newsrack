"""
scmp.com
"""
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.web.feeds.news import BasicNewsRecipe

_name = "South China Morning Post"


class SCMP(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "llam"
    description = "SCMP.com, Hong Kong's premier online English daily provides exclusive up-to-date news, audio video news, podcasts, RSS Feeds, Blogs, breaking news, top stories, award winning news and analysis on Hong Kong and China. https://www.scmp.com/"  # noqa
    publisher = "South China Morning Post Publishers Ltd."
    publication_type = "newspaper"
    oldest_article = 1
    max_articles_per_feed = 25
    encoding = "utf-8"
    use_embedded_content = False
    language = "en"
    remove_empty_feeds = True
    auto_cleanup = False
    ignore_duplicate_articles = {"title", "url"}

    masthead_url = (
        "https://cdn.shopify.com/s/files/1/0280/0258/2595/files/SCMP_Logo_2018_540x.png"
    )
    timeout = 30

    # used when unable to extract article from <script>, particularly in the Sports section
    remove_tags = [
        dict(
            class_=[
                "sticky-wrap",
                "relative",
                "social-media",
                "social-media--extended__shares",
                "article-body-comment",
                "scmp_button_comment_wrapper",
                "social-media--extended__in-site",
                "footer",
                "scmp-advert-tile",
                "sidebar-col",
                "related-article",
                "topic__add",
                "head__main-images",
                "share-widget",
                "trust-label",
                "follow-topic",
                "article-author__follow-button",
                "piano-metering__paywall-container",
                "read-more--hide",
            ]
        ),
        dict(attrs={"addthis_title": True}),
        dict(name=["script", "style", "svg"]),
    ]
    remove_attributes = ["style", "font"]

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .sub-headline { font-size: 1rem; margin-bottom: 1.5rem; }
    .sub-headline ul { padding-left: 1rem; }
    .sub-headline ul li { fmargin-bottom: 0.8rem; }
    .article-meta, .article-header__publish { padding-bottom: 0.5rem; }
    .article-meta .author { font-weight: bold; color: #444; }
    .article-meta .published-dt { margin-left: 0.5rem; }
    .article-img { margin-bottom: 0.8rem; max-width: 100%; }
    .article-img img, .carousel__slide img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box; }
    .article-img .caption, .article-caption { font-size: 0.8rem; }
    """

    # https://www.scmp.com/rss
    feeds = [
        ("Hong Kong", "https://www.scmp.com/rss/2/feed"),
        ("China", "https://www.scmp.com/rss/4/feed"),
        ("Asia", "https://www.scmp.com/rss/3/feed"),
        ("World", "https://www.scmp.com/rss/5/feed"),
        ("Business", "https://www.scmp.com/rss/92/feed"),
        ("Tech", "https://www.scmp.com/rss/36/feed"),
        ("Life", "https://www.scmp.com/rss/94/feed"),
        ("Culture", "https://www.scmp.com/rss/322296/feed"),
        # ("Sport", "https://www.scmp.com/rss/95/feed"),
        # ("Post Mag", "https://www.scmp.com/rss/71/feed"),
        ("Style", "https://www.scmp.com/rss/72/feed"),
    ]

    def _extract_child_nodes(self, children, ele, soup, level=1):
        if not children:
            return

        child_html = ""
        for child in children:
            if child.get("type", "") == "text":
                child_html += child["data"]
            else:
                if child["type"] == "iframe":
                    # change iframe to <span> with the src linked
                    new_ele = soup.new_tag("span")
                    new_ele["class"] = f'embed-{child["type"]}'
                    iframe_src = child.get("attribs", {}).get("src")
                    a_tag = soup.new_tag("a")
                    a_tag["href"] = iframe_src
                    a_tag.string = f"[Embed: {iframe_src}]"
                    new_ele.append(a_tag)
                else:
                    new_ele = soup.new_tag(child["type"])
                    for k, v in child.get("attribs", {}).items():
                        if k.startswith("data-"):
                            continue
                        new_ele[k] = v
                    if child.get("children"):
                        self._extract_child_nodes(
                            child["children"], new_ele, soup, level + 1
                        )
                child_html += str(new_ele)
                if child["type"] == "img":
                    # generate a caption <span> tag for <img>
                    caption_text = child.get("attribs", {}).get("alt") or child.get(
                        "attribs", {}
                    ).get("title")
                    if caption_text:
                        new_ele = soup.new_tag("span")
                        new_ele.append(caption_text)
                        new_ele["class"] = "caption"
                        child_html += str(new_ele)
                    ele["class"] = "article-img"
        ele.append(BeautifulSoup(child_html))

    def preprocess_raw_html(self, raw_html, url):
        article = None
        soup = BeautifulSoup(raw_html)

        for script in soup.find_all("script"):
            if not script.contents:
                continue
            if not script.contents[0].startswith("window.__APOLLO_STATE__"):
                continue
            article_js = re.sub(
                r"window.__APOLLO_STATE__\s*=\s*", "", script.contents[0].strip()
            )
            if article_js.endswith(";"):
                article_js = article_js[:-1]
            try:
                article = json.loads(article_js)
                break
            except json.JSONDecodeError:
                # sometimes this borks because of a stray '\n'
                try:
                    article = json.loads(article_js.replace("\n", " "))
                except json.JSONDecodeError:
                    self.log.exception("Unable to parse __APOLLO_STATE__")

        if not article:
            if os.environ.get("recipe_debug_folder", ""):
                recipe_folder = os.path.join(os.environ["recipe_debug_folder"], "scmp")
                if not os.path.exists(recipe_folder):
                    os.makedirs(recipe_folder)
                debug_output_file = os.path.join(
                    recipe_folder, os.path.basename(urlparse(url).path)
                )
                if not debug_output_file.endswith(".html"):
                    debug_output_file += ".html"
                self.log(f'Writing debug raw html to "{debug_output_file}" for {url}')
                with open(debug_output_file, "w", encoding="utf-8") as f:
                    f.write(raw_html)
            self.log(f"Unable to find article from script in {url}")
            return raw_html

        if not (article and article.get("contentService")):
            # Sometimes the page does not have article content in the <script>
            # particularly in the Sports section, so we fallback to
            # raw_html and rely on remove_tags to clean it up
            self.log(f"Unable to find article from script in {url}")
            return raw_html

        content_service = article.get("contentService")
        content_node_id = None
        for k, v in content_service["ROOT_QUERY"].items():
            if not k.startswith("content"):
                continue
            content_node_id = v["id"]
            break
        content = content_service.get(content_node_id)

        if content.get("sponsorType"):
            # skip sponsored articles
            self.abort_article(f"Sponsored article: {url}")

        body = None
        for k, v in content.items():
            if (not k.startswith("body(")) or v.get("type", "") != "json":
                continue
            body = v

        authors = [content_service[a["id"]]["name"] for a in content["authors"]]
        date_published = datetime.utcfromtimestamp(
            content["publishedDate"] / 1000
        ).replace(tzinfo=timezone.utc)
        date_published_loc = date_published.astimezone(
            timezone(offset=timedelta(hours=8))  # HK time
        )

        html_output = f"""<html><head><title>{content["headline"]}</title></head>
        <body>
            <article>
            <h1 class="headline">{content["headline"]}</h1>
            <div class="sub-headline"></div>
            <div class="article-meta">
                <span class="author">{", ".join(authors)}</span>
                <span class="published-dt">
                    {date_published_loc:%-I:%M%p, %-d %b, %Y}
                </span>
            </div>
            </article>
        </body></html>
        """

        new_soup = BeautifulSoup(html_output, "html.parser")
        # sub headline
        for c in content.get("subHeadline", {}).get("json", []):
            ele = new_soup.new_tag(c["type"])
            self._extract_child_nodes(c.get("children", []), ele, new_soup)
            new_soup.find(class_="sub-headline").append(ele)

        # article content
        for node in body["json"]:
            if node["type"] not in ["p", "div"]:
                continue
            new_ele = new_soup.new_tag(node["type"])
            new_ele.string = ""
            if node.get("children"):
                self._extract_child_nodes(node["children"], new_ele, new_soup)
            new_soup.article.append(new_ele)

        return str(new_soup)

    def populate_article_metadata(self, article, soup, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, article.utctime)
