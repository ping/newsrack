# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
guardian.com
"""
import json
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Guardian"


class Guardian(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    description = "Latest international news, sport and comment from the Guardian https://www.theguardian.com/international"
    language = "en_GB"
    __author__ = "ping"
    publication_type = "newspaper"
    oldest_article = 1  # days
    max_articles_per_feed = 60
    use_embedded_content = False
    encoding = "utf-8"
    masthead_url = "https://assets.guim.co.uk/images/guardian-logo-rss.c45beb1bafa34b347ac333af2e6fe23f.png"
    auto_cleanup = False

    remove_attributes = ["style", "width", "height"]
    keep_only_tags = [dict(name=["header", "article"])]
    remove_tags = [
        dict(name=["svg", "input", "button", "label"]),
        dict(id=["bannerandheader", "the-caption", "liveblog-navigation"]),
        dict(
            class_=[
                "skip",
                "meta__social",
                "live-blog__filter-switch",
                "ad-slot",
                "l-footer",
                "is-hidden",
                "js-most-popular-footer",
                "submeta",
                "block-share",
                "content-footer",
            ]
        ),
        dict(name="div", attrs={"data-print-layout": "hide"}),
        dict(attrs={"name": "FilterKeyEventsToggle"}),
        dict(attrs={"aria-hidden": "true"}),
        dict(
            name="time", attrs={"data-relativeformat": "med"}
        ),  # remove the relative timestamp, e.g. 8h ago
        dict(attrs={"data-component": ["podcast-help", "nav2", "SupportTheG"]}),
        dict(
            attrs={
                "data-spacefinder-type": "model.dotcomrendering.pageElements.NewsletterSignupBlockElement"
            }
        ),
        dict(
            name="gu-island",
            attrs={"name": ["HeaderTopBar", "Carousel", "GuideAtomWrapper"]},
        ),
        dict(attrs={"data-link-name": "nav3 : logo"}),
    ]

    extra_css = """
    [data-gu-name="headline"] h1 { font-size: 1.8rem; margin-bottom: 0.4rem; }
    [data-gu-name="standfirst"] p { font-size: 1.2rem; font-style: italic; margin-top: 0; margin-bottom: 1rem; }
    [data-component="series"], [data-component="section"] { margin-right: 0.5rem; }
    [data-gu-name="meta"] { margin-bottom: 1.5rem; }
    [data-component="meta-byline"] {
        margin-top: 1rem; margin-bottom: 1rem;
        font-weight: bold; color: #444; font-style: normal;
    }
    [data-component="meta-byline"] div { display: inline-block; margin-right: 0.5rem; }
    [data-component="meta-byline"] a { color: #444; }
    *[data-gu-name="media"] span, *[item-prop="description"],
    div[data-spacefinder-type$=".ImageBlockElement"] > div,
    div.caption { font-size: 0.8rem; margin-bottom: 0.5rem; }
    img { max-width: 100%; height: auto; margin-bottom: 0.2rem; }
    [data-name="placeholder"] { color: #444; font-style: italic; }
    [data-name="placeholder"] a { color: #444; }
    blockquote { font-size: 1.2rem; color: #222; margin-left: 0; text-align: center; }
    time { margin-right: 0.5rem; }
    .embed { color: #444; font-size: 0.8rem; }
    """

    feeds = [
        (_name, "https://www.theguardian.com/international/rss"),
    ]

    def preprocess_html(self, soup):
        live_blog = self.get_ld_json(
            soup, lambda d: d[0].get("@type", "") == "LiveBlogPosting"
        )
        if live_blog:
            self.abort_article("Do not include live postings")

        meta = soup.find(attrs={"data-gu-name": "meta"})
        if meta:
            # remove author image
            for img in meta.find_all("img"):
                img.decompose()

            # reformat the displayed date
            details = meta.find_all("details")
            for detail in details:
                summary = detail.find("summary")
                update_date = None
                if len(detail.contents) > 1:
                    update_date = detail.contents[1]
                published = soup.new_tag("div", attrs={"class": "published-date"})
                published.append(summary.string)
                detail.clear()
                detail.append(published)
                if update_date:
                    update = soup.new_tag("div", attrs={"class": "last-updated-date"})
                    update.append(update_date)
                    detail.append(update)
                detail.name = "div"
                detail["class"] = "meta-date"

        # re-position lede image
        media = soup.find(attrs={"data-gu-name": "media"})
        if media and meta:
            meta.insert_after(media.extract())

        # search for highest resolution image
        for picture in soup.find_all("picture"):
            source = picture.find("source")  # use first one
            if not source:
                continue
            max_img_url = source["srcset"]
            for source in picture.find_all("source"):
                source.decompose()
            img = picture.find("img")
            if not img:
                img = soup.new_tag("img", attrs={"class": "custom-added"})
                picture.append(img)
            img["src"] = max_img_url

        # remove share on social media links for live articles
        for unordered_list in soup.find_all("ul"):
            is_social_media = False
            for list_item in unordered_list.find_all("li"):
                a_link = list_item.find("a", attrs={"aria-label": True})
                if a_link and a_link["aria-label"] in [
                    "Share on Facebook",
                    "Share on Twitter",
                ]:
                    is_social_media = True
                    break
            if is_social_media:
                unordered_list.decompose()

        # Patch Key Events ul in live articles
        # The div forces a linebreak in the li > a looks bad in the Kindle
        for unordered_list in soup.find_all("ul"):
            for link_item in unordered_list.find_all("a"):
                if link_item["href"].startswith("?filterKeyEvents"):
                    link_text = self.tag_to_string(link_item)
                    link_item.parent.string = link_text

        # embed YT blocks
        for yt in soup.find_all(
            attrs={
                "data-spacefinder-type": "model.dotcomrendering.pageElements.YoutubeBlockElement"
            }
        ):
            info_ele = yt.find(name="gu-island")
            if not info_ele:
                continue
            info = json.loads(info_ele["props"])
            link = f'https://www.youtube.com/watch?v={info["assetId"]}'
            yt.clear()
            yt["class"] = "embed"
            yt.append(f'{info["mediaTitle"]} ')
            a_link = soup.new_tag("a", href=link)
            a_link.append(link)
            yt.append(a_link)

        return soup

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = format_title(_name, article.utctime)

    def parse_feeds(self):
        return self.group_feeds_by_date(timezone_offset_hours=1)  # UK time
