# Modified from https://github.com/kovidgoyal/calibre/blob/1f9c67ce02acfd69b5934bba3d74ce6875b9809e/recipes/economist.recipe

import json
import os
import random
import sys
import time
from datetime import timezone, datetime, timedelta
from http.cookiejar import Cookie
from os.path import splitext
from urllib.parse import urlparse

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre import replace_entities
from calibre.ebooks.BeautifulSoup import NavigableString, Tag
from calibre.utils.cleantext import clean_ascii_chars
from calibre.web.feeds.news import BasicNewsRecipe, classes
from html5_parser import parse
from lxml import etree


def E(parent, name, text="", **attrs):
    ans = parent.makeelement(name, **attrs)
    ans.text = text
    parent.append(ans)
    return ans


def process_node(node, html_parent):
    ntype = node.get("type")
    if ntype == "tag":
        c = html_parent.makeelement(node["name"])
        c.attrib.update({k: v or "" for k, v in node.get("attribs", {}).items()})
        html_parent.append(c)
        for nc in node.get("children", ()):
            process_node(nc, c)
    elif ntype == "text":
        text = node.get("data")
        if text:
            text = replace_entities(text)
            if len(html_parent):
                t = html_parent[-1]
                t.tail = (t.tail or "") + text
            else:
                html_parent.text = (html_parent.text or "") + text


def safe_dict(data, *names):
    ans = data
    for x in names:
        ans = ans.get(x) or {}
    return ans


class JSONHasNoContent(ValueError):
    pass


def load_article_from_json(raw, root):
    try:
        data = json.loads(raw)["props"]["pageProps"]["content"]
    except KeyError as e:
        raise JSONHasNoContent(e)

    # open('/t/raw.json', 'w').write(json.dumps(data, indent=2, sort_keys=True))
    if isinstance(data, list):
        data = data[0]

    body = root.xpath("//body")[0]
    for child in tuple(body):
        body.remove(child)
    article = E(body, "article")
    E(article, "h4", data["subheadline"], style="color: red; margin: 0")
    E(article, "h1", data["headline"], style="font-size: x-large")
    E(
        article,
        "div",
        data["description"] or data["subheadline"],
        style="font-style: italic; font-size: large; margin-bottom: 1rem;",
        id="subheadline",
    )
    E(
        article,
        "div",
        (data["datePublishedString"] or "")
        + (" | " if data["dateline"] else "")
        + (data["dateline"] or ""),
        style="margin-bottom: 1rem; ",
        datecreated=data["dateModified"],
    )
    main_image_url = safe_dict(data, "image", "main", "url").get("canonical")
    if main_image_url:
        div = E(article, "div")
        try:
            E(div, "img", src=main_image_url)
        except Exception:
            pass
    for node in data["text"]:
        process_node(node, article)


def cleanup_html_article(root):
    main = root.xpath("//main")[0]
    body = root.xpath("//body")[0]
    for child in tuple(body):
        body.remove(child)
    body.append(main)
    main.set("id", "")
    main.tag = "article"
    for x in root.xpath("//*[@style]"):
        x.set("style", "")
    for x in root.xpath("//button"):
        x.getparent().remove(x)


def new_tag(soup, name, attrs=()):
    impl = getattr(soup, "new_tag", None)
    if impl is not None:
        return impl(name, attrs=dict(attrs))
    return Tag(soup, name, attrs=attrs or None)


class NoArticles(Exception):
    pass


def process_url(url):
    if url.startswith("/"):
        url = "https://www.economist.com" + url
    return url


_name = "1843 Magazine"


class EighteenFortyThree(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Published since September 1843 to take part in “a severe contest between intelligence, "
        "which presses forward, and an unworthy, timid ignorance obstructing our progress.” "
        "1843 is a sister magazine of The Economist. https://www.economist.com/1843"
    )
    language = "en"
    encoding = "utf-8"

    masthead_url = "https://www.economist.com/cdn-cgi/image/width=480,quality=80,format=auto/sites/default/files/images/2021/04/articles/main/1843-master-logo-2019-black.png"
    needs_subscription = False

    extra_css = """
        .headline {font-size: x-large;}
        h2 { font-size: medium; font-weight: bold;  }
        h1 { font-size: large; font-weight: bold; }
        em.Bold {font-weight:bold;font-style:normal;}
        em.Italic {font-style:italic;}
        p.xhead {font-weight:bold;}
        .pullquote {
            float: right;
            font-size: larger;
            font-weight: bold;
            font-style: italic;
            page-break-inside:avoid;
            border-bottom: 3px solid black;
            border-top: 3px solid black;
            width: 228px;
            margin: 0px 0px 10px 15px;
            padding: 7px 0px 9px;
        }
        .flytitle-and-title__flytitle {
            display: block;
            font-size: smaller;
            color: red;
        }
        p span[data-caps="initial"], p small {
            font-size: 1rem;
            text-transform: uppercase;
        }
        #script-microapp .article-text {
            margin: 1rem 0;
        }
        div[itemtype="https://schema.org/ImageGallery"] div { font-size: 0.8rem; margin-top: 0.2rem; margin-bottom: 0.5rem; }
        div[itemtype="https://schema.org/ImageGallery"] img,
        div[itemtype="https://schema.org/ImageObject"] img
        { display: block; max-width: 100%; height: auto; }
        p cite { font-size: 1.25rem; margin-left: 0; text-align: center; display: block; }
        """
    oldest_article = 14
    resolve_internal_links = True
    remove_tags = [
        dict(
            name=[
                "script",
                "noscript",
                "title",
                "iframe",
                "cf_floatingcontent",
                "aside",
                "footer",
            ]
        ),
        dict(attrs={"aria-label": "Article Teaser"}),
        dict(
            attrs={
                "class": [
                    "dblClkTrk",
                    "ec-article-info",
                    "share_inline_header",
                    "related-items",
                    "main-content-container",
                    "ec-topic-widget",
                    "teaser",
                    "blog-post__bottom-panel-bottom",
                    "blog-post__comments-label",
                    "blog-post__foot-note",
                    "blog-post__sharebar",
                    "blog-post__bottom-panel",
                    "newsletter-form",
                    "share-links-header",
                    "teaser--wrapped",
                    "latest-updates-panel__container",
                    "latest-updates-panel__article-link",
                    "blog-post__section",
                    "related-content",
                    "scroller",  # interactive stuff that we can't render anyway
                    "ai2html-chart",  # interactive stuff that we can't render anyway
                ]
            }
        ),
        dict(
            attrs={
                "class": lambda x: x and "blog-post__siblings-list-aside" in x.split()
            }
        ),
        classes(
            "share-links-header teaser--wrapped latest-updates-panel__container"
            " latest-updates-panel__article-link blog-post__section newsletter-form blog-post__bottom-panel"
        ),
    ]
    keep_only_tags = [dict(name="article", id=lambda x: not x)]
    remove_attributes = ["data-reactid", "width", "height"]
    # economist.com has started throttling with HTTP 429
    delay = 0
    simultaneous_downloads = 1

    def __init__(self, *args, **kwargs):
        BasicNewsRecipe.__init__(self, *args, **kwargs)
        if self.output_profile.short_name.startswith("kindle"):
            # Reduce image sizes to get file size below amazon's email
            # sending threshold
            self.web2disk_options.compress_news_images = True
            self.web2disk_options.compress_news_images_auto_size = 5
            self.log.warn(
                "Kindle Output profile being used, reducing image quality to keep file size below amazon email threshold"
            )
        br = BasicNewsRecipe.get_browser(self)
        # Add a cookie indicating we have accepted Economist's cookie
        # policy (needed when running from some European countries)
        ck = Cookie(
            version=0,
            name="notice_preferences",
            value="2:",
            port=None,
            port_specified=False,
            domain=".economist.com",
            domain_specified=False,
            domain_initial_dot=True,
            path="/",
            path_specified=False,
            secure=False,
            expires=None,
            discard=False,
            comment=None,
            comment_url=None,
            rest={"HttpOnly": None},
            rfc2109=False,
        )
        br.cookiejar.set_cookie(ck)
        br.set_handle_gzip(True)
        self._br = br

    # We send no cookies to avoid triggering bot detection
    def get_browser(self, *args, **kwargs):
        return self

    def clone_browser(self, *args, **kwargs):
        return self.get_browser()

    def open_novisit(self, *args, **kwargs):
        target_url = args[0]
        p, ext = splitext(urlparse(target_url).path)
        if not ext:
            # not an asset, e.g. .png .jpg
            time.sleep(random.choice([r for r in range(1, 3)]))

        return self._br.open_novisit(*args, **kwargs)

    open = open_novisit

    def preprocess_raw_html(self, raw, _):
        root = parse(raw)
        script = root.xpath('//script[@id="__NEXT_DATA__"]')
        if script:
            if script:
                try:
                    load_article_from_json(script[0].text, root)
                except JSONHasNoContent:
                    cleanup_html_article(root)
        for div in root.xpath('//div[@class="lazy-image"]'):
            noscript = list(div.iter("noscript"))
            if noscript and noscript[0].text:
                img = list(parse(noscript[0].text).iter("img"))
                if img:
                    p = noscript[0].getparent()
                    idx = p.index(noscript[0])
                    p.insert(idx, p.makeelement("img", src=img[0].get("src")))
                    p.remove(noscript[0])
        for x in root.xpath(
            '//*[name()="script" or name()="style" or name()="source" or name()="meta"]'
        ):
            x.getparent().remove(x)
        raw = etree.tostring(root, encoding="unicode")
        return raw

    def populate_article_metadata(self, article, soup, first):
        els = soup.findAll(
            name=["span", "p"],
            attrs={"class": ["flytitle-and-title__title", "blog-post__rubric"]},
        )
        result = []
        for el in els[0:2]:
            if el is not None and el.contents:
                for descendant in el.contents:
                    if isinstance(descendant, NavigableString):
                        result.append(type("")(descendant))
        article.summary = ". ".join(result) + ("." if result else "")
        if not article.summary:
            # try another method
            sub = soup.find(id="subheadline")
            if sub:
                article.summary = sub.string
        article.text_summary = clean_ascii_chars(article.summary)
        div_date = soup.find(attrs={"datecreated": True})
        if div_date:
            # "%Y-%m-%dT%H:%M:%SZ"
            date_published = self.parse_date(div_date["datecreated"])
            if not self.pub_date or date_published > self.pub_date:
                self.pub_date = date_published
                self.title = format_title(_name, date_published)

    def parse_index(self):
        soup = self.index_to_soup("https://www.economist.com/1843")
        ans = self.economist_parse_index(soup)
        if not ans:
            raise NoArticles(
                "Could not find any articles, either the "
                "economist.com server is having trouble and you should "
                "try later or the website format has changed and the "
                "recipe needs to be updated."
            )
        return ans

    def economist_parse_index(self, soup):
        cutoff_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=self.oldest_article)

        data = self.get_ld_json(soup, lambda d: d.get("@type", "") == "itemList")
        articles = []
        for i in data.get("itemListElement", []):
            item = i["item"]
            article_dt = self.parse_date(item["datePublished"])
            if article_dt < cutoff_date:
                continue
            articles.append({"url": item["url"], "title": item["headline"]})
        return [(data["@name"], articles)]

    def eco_find_image_tables(self, soup):
        for x in soup.findAll("table", align=["right", "center"]):
            if len(x.findAll("font")) in (1, 2) and len(x.findAll("img")) == 1:
                yield x

    def postprocess_html(self, soup, first):
        for img in soup.findAll("img", srcset=True):
            del img["srcset"]
        for table in list(self.eco_find_image_tables(soup)):
            caption = table.find("font")
            img = table.find("img")
            div = new_tag(soup, "div")
            div["style"] = "text-align:left;font-size:70%"
            ns = NavigableString(self.tag_to_string(caption))
            div.insert(0, ns)
            div.insert(1, new_tag(soup, "br"))
            del img["width"]
            del img["height"]
            img.extract()
            div.insert(2, img)
            table.replaceWith(div)
        return soup

    def canonicalize_internal_url(self, url, is_link=True):
        if url.endswith("/print"):
            url = url.rpartition("/")[0]
        return BasicNewsRecipe.canonicalize_internal_url(self, url, is_link=is_link)
