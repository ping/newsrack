# Copyright (c) 2023 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0
import json
import os
import sys
from collections import OrderedDict
from datetime import timezone
from urllib.parse import urlparse, urlencode

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import WordPressNewsrackRecipe, get_datetime_format

from calibre.web.feeds.news import BasicNewsRecipe

_name = "Foreign Policy Magazine"
_issue_url = ""


class ForeignPolicyMagazine(WordPressNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Foreign Policy is an American news publication, founded in 1970 and "
        "focused on global affairs, current events, and domestic and international "
        "policy. It produces content daily on its website and app, and in four "
        "print issues annually. https://foreignpolicy.com/the-magazine/"
    )
    language = "en"
    publication_type = "magazine"
    oldest_article = 30  # days
    masthead_url = "https://foreignpolicy.com/wp-content/themes/foreign-policy-2017/assets/src/images/logos/favicon-256.png"
    reverse_article_order = False
    compress_news_images_auto_size = 12
    resolve_internal_links = True

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .article-meta {  margin-top: 1rem; margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    .article-img img, img.attachment-full, .image-attachment  img { display: block; max-width: 100%; height: auto; }
    .article-img p, .wp-caption-text {
        font-size: 0.8rem; display: block; margin-top: 0.2rem;
    }
    .pull-quote-sidebar {
        display: block; text-align: center;
        margin-left: 0; margin-bottom: 0.4rem; font-size: 1.25rem;
    }
    """

    remove_tags = [
        dict(
            class_=[
                "Apple-converted-space",
                "graphic-chatter",
                "fp_choose_placement_related_posts",
                "sidebar-box_right",
                "newsletter-unit-signup",
                "newsletter-unit-signup--shortcode-fallback",
                "related-articles-carousel",
                "featured_related_content",
            ]
        ),
        dict(style="height:0;opacity:0;"),
        dict(name=["noscript"]),
    ]
    remove_attributes = ["width", "height", "style"]

    def preprocess_raw_html(self, raw_html, url):
        # formulate the api response into html
        post = next(iter(json.loads(raw_html)), {})
        if not post:
            self.abort_article()
        date_published_loc = self.parse_date(post["date"], tz_info=None, as_utc=False)
        post_authors = self.extract_authors(post)
        categories = self.extract_categories(post)

        date_published_gmt = self.parse_date(post["date_gmt"], tz_info=timezone.utc)
        if not self.pub_date or date_published_gmt > self.pub_date:
            self.pub_date = date_published_gmt

        soup = self.soup(
            f"""<html>
        <head><title>{post["title"]["rendered"]}</title></head>
        <body>
            <article data-og-link="{post["link"]}">
            {f'<span class="article-section">{" / ".join(categories)}</span>' if categories else ''}
            <h1 class="headline">{post["title"]["rendered"]}</h1>
            <div class="article-meta">
                {f'<span class="author">{", ".join(post_authors)}</span>' if post_authors else ''}
                <span class="published-dt">
                    {date_published_loc:{get_datetime_format()}}
                </span>
            </div>
            </article>
        </body></html>"""
        )

        content = self.soup(post["content"]["rendered"])
        # FP doesn't use featuremedia, the first attachment is the lede image
        attachment_endpoint = (
            post.get("_links", {}).get("wp:attachment", [{}])[0].get("href")
        )
        if attachment_endpoint:
            attachment = next(
                iter(json.loads(self.index_to_soup(attachment_endpoint, raw=True))), {}
            )
            if attachment:
                lede = soup.new_tag("div", attrs={"class": "image-attachment"})
                img = soup.new_tag("img", attrs={"src": attachment["source_url"]})
                lede.append(img)
                if attachment.get("caption", {}).get("rendered"):
                    caption = soup.new_tag("div", attrs={"class": "wp-caption-text"})
                    caption.append(self.soup(attachment["caption"]["rendered"]))
                    lede.append(caption)
                soup.body.article.append(lede)

        soup.body.article.append(content)

        for img in soup.find_all("img", attrs={"data-lazy-src": True}):
            img["src"] = img["data-lazy-src"]
            # also cleanup a little
            for attribute in (
                "data-lazy-src",
                "data-lazy-srcset",
                "data-lazy-sizes",
                "data-src",
                "loading",
            ):
                if img.get(attribute):
                    del img[attribute]

        return str(soup)

    def _post_endpoint(self, link):
        return "https://foreignpolicy.com/wp-json/wp/v2/posts/?" + urlencode(
            {
                "slug": [f for f in urlparse(link).path.split("/") if f][-1],
                "_embed": "1",
            }
        )

    def parse_index(self):
        soup = self.index_to_soup(
            "https://foreignpolicy.com/the-magazine" if not _issue_url else _issue_url
        )
        img = soup.find("img", attrs={"data-lazy-src": lambda x: x and "-cover" in x})
        self.cover_url = img["data-lazy-src"].split("?")[0]

        meta = next(iter(soup.select(".issue-list span")), None)
        if meta:
            self.title = f"{_name}: {self.tag_to_string(meta).strip()}"

        articles = OrderedDict()
        editors_note = next(iter(soup.select(".issue-list a")), None)
        if editors_note:
            ed_note_title = self.tag_to_string(editors_note).strip()
            articles.setdefault(ed_note_title, []).append(
                {
                    "title": ed_note_title,
                    "url": self._post_endpoint(editors_note["href"]),
                }
            )

        current_section = None
        for h in soup.find_all(name=["h2", "h3"]):
            if h.name == "h2":
                current_section = self.tag_to_string(h)
                if current_section.lower() == "recent issues":
                    break
            else:
                title = self.tag_to_string(h)
                articles.setdefault(current_section, []).append(
                    {"title": title, "url": self._post_endpoint(h.parent["href"])}
                )
        if "latest" in articles:
            del articles["latest"]
        for k in list(articles.keys()):
            if not articles[k]:
                # remove empty sections
                del articles[k]
        return articles.items()
