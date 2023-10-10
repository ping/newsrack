__license__ = "GPL v3"
__copyright__ = "2015 Michael Marotta <mikefm at gmail.net>"
# Written April 2015
# Last edited 08/2022

# Original at: https://github.com/kovidgoyal/calibre/blob/401c92737ff4e72947a112f7440955b10efb0a9b/recipes/mit_technology_review.recipe
"""
technologyreview.com
"""
import json
import os
import re
import sys
from collections import OrderedDict
from datetime import timezone

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import WordPressNewsrackRecipe, get_date_format

from calibre.web.feeds.news import BasicNewsRecipe


def absurl(x):
    if x.startswith("//"):
        x = "http:" + x
    elif not x.startswith("http"):
        x = "http://www.technologyreview.com" + x
    return x


_name = "MIT Technology Review Magazine"
_issue_url = ""


class MitTechnologyReviewMagazine(WordPressNewsrackRecipe, BasicNewsRecipe):

    title = _name
    __author__ = "Michael Marotta, revised by unkn0wn"
    description = "Bi-monthly magazine version of MIT Technology Review. https://www.technologyreview.com/magazine/"
    INDEX = "https://www.technologyreview.com/magazine/"
    language = "en"
    publication_type = "magazine"
    tags = "news, technology, science"
    masthead_url = "https://wp-preprod.technologyreview.com/wp-content/uploads/2021/08/Screen-Shot-2021-08-20-at-11.11.12-AM-e1629473232355.png"

    compress_news_images_auto_size = 10

    remove_attributes = ["height", "width", "style", "padding", "padding-top"]

    extra_css = """
        .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
        .article-meta { padding-bottom: 0.5rem; }
        .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
        .article-section { display: block; font-weight: bold; color: #444; }
        .wp-block-image img {
            display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
            box-sizing: border-box;
        }
        .wp-block-image div, .image-credit { font-size: 0.8rem; }
        blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
        blockquote cite { font-size: 1rem; margin-left: 0; text-align: center; }
    """

    def _extract_featured_media(self, post):
        """
        Include featured media with post content.

        :param post: post dict
        :param post_content: Extracted post content
        :return:
        """
        post_content = post["content"]["rendered"]
        if not post.get("featured_media"):
            return post_content

        feature_media_css = f"wp-image-{post['featured_media']}"
        if feature_media_css in post_content:
            return post_content

        for feature_info in post.get("_embedded", {}).get("wp:featuredmedia", []):
            # put feature media at the start of the post
            if feature_info.get("source_url"):
                caption = feature_info.get("caption", {}).get("rendered", "")
                # higher-res
                image_src = f"""
                <div class="wp-block-image">
                    <img src="{feature_info["source_url"]}">
                    <div class="image-credit">{caption}</div>
                </div>"""
                post_content = image_src + post_content
            else:
                post_content = (
                    feature_info.get("description", {}).get("rendered", "")
                    + post_content
                )
        return post_content

    def preprocess_raw_html(self, raw_html, url):
        # formulate the api response into html
        post = json.loads(raw_html)
        post_update_dt = self.parse_date(post["modified_gmt"], tz_info=timezone.utc)
        if not self.pub_date or post_update_dt > self.pub_date:
            self.pub_date = post_update_dt

        date_published_loc = self.parse_date(post["date"], tz_info=None, as_utc=False)
        post_authors = self.extract_authors(post)
        categories = self.extract_categories(post)

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
                    {date_published_loc:{get_date_format()}}
                </span>
            </div>
            {self._extract_featured_media(post)}
            </article>
        </body></html>"""
        )
        for bq in soup.find_all("blockquote"):
            for strong in bq.find_all("strong"):
                strong.name = "span"
        for img in soup.find_all(srcset=True):
            img["src"] = absurl(img["srcset"].split()[0])
            del img["srcset"]
        for img in soup.find_all("img", attrs={"src": True}):
            img["src"] = img["src"].split("?")[0] + "?w=800"
        return str(soup)

    def parse_index(self):
        soup = self.index_to_soup(_issue_url if _issue_url else self.INDEX)
        index = {}
        for script in soup.find_all(name="script"):
            if not script.contents:
                continue
            if not script.contents[0].strip().startswith("window.__PRELOADED_STATE__"):
                continue
            index_js = re.sub(
                r"window.__PRELOADED_STATE__\s*=\s*", "", script.contents[0].strip()
            )
            if index_js.endswith(";"):
                index_js = index_js[:-1]
            try:
                index = json.loads(index_js)
                break
            except json.JSONDecodeError:
                self.log.exception("Unable to parse window.__PRELOADED_STATE__")

        feeds = OrderedDict()
        for comp in list(index["components"]["page"].values())[0]:
            if comp["name"] != "body":
                continue
            for info in comp["children"]:
                if info["name"] == "magazine-hero":
                    config = info["config"]
                    self.title = f'{_name}: {config["issueDate"] or config["title"]}'
                    for c in info["children"]:
                        if c["name"] == "image":
                            self.cover_url = c["config"]["src"]
                            break
                elif info["name"] == "column-area":
                    for section in info["children"]:
                        # post-list, sidebar
                        post_list = []
                        if section["name"] == "post-list":
                            post_list = section["children"]
                        else:
                            for c in section["children"]:
                                if c["name"] == "post-list":
                                    post_list = c["children"]
                                    break
                        for post in post_list:
                            mobj = re.match(
                                r"https://www.technologyreview.com/\d{4}/\d{2}/\d{2}/(?P<post_id>\d+)/",
                                post.get("config", {}).get("permalink", ""),
                            )
                            if not mobj:
                                self.log.warning(
                                    f'Unable to extract post ID for {post.get("config", {}).get("permalink", "")}'
                                )
                                continue
                            post_config = post["config"]
                            topic = post_config.get("topic", "Articles")
                            feeds.setdefault(topic, []).append(
                                {
                                    "title": post_config["title"],
                                    "description": post_config["excerpt"],
                                    "url": f'https://www.technologyreview.com/wp-json/wp/v2/posts/{mobj.group("post_id")}/?_embed=',
                                }
                            )

        return feeds.items()
