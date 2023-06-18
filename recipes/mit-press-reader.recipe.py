# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0
import os
import sys

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe, format_title, get_datetime_format

from calibre.utils.date import parse_date
from calibre.web.feeds.news import BasicNewsRecipe

_name = "The MIT Press Reader"


class MITPressReader(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "Thought-provoking excerpts, interviews and essays backed by academic rigor written by MIT Press authors. https://thereader.mitpress.mit.edu/"
    language = "en"
    publication_type = "blog"
    oldest_article = 30  # days
    use_embedded_content = False
    encoding = "utf-8"
    compress_news_images = False
    masthead_url = "https://thereader.mitpress.mit.edu/wp-content/themes/ta/img/log.png"
    auto_cleanup = False
    reverse_article_order = False

    keep_only_tags = [dict(class_=["article-entry"])]
    remove_tags = [
        dict(name=["script", "noscript", "style"]),
        dict(
            class_=[
                "ma-top-shares-right",
                "ma-txt-customizer-cont",
                "social-cont",
                "ma-related-posts",
                "tags-cont",
            ]
        ),
    ]

    extra_css = """
    h1 { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .ma-subheading { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    .ma-authors { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    .wp-block-image { margin-bottom: 0.5rem; }
    .wp-block-image img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    .wp-block-image div, .image-credit { font-size: 0.8rem; }
    .wp-block-pullquote blockquote { font-size: 1.25rem; margin-left: 0; text-align: center; }
    .wp-block-pullquote blockquote cite { font-size: 1rem; margin-left: 0; text-align: center; }
    """

    feeds = [
        (_name, "https://thereader.mitpress.mit.edu/feed/"),
    ]

    def postprocess_html(self, soup, _):
        time_ele = soup.find(name="time", attrs={"datetime": True})
        post_date = parse_date(time_ele["datetime"])
        if (not self.pub_date) or post_date > self.pub_date:
            self.pub_date = post_date
            self.title = format_title(_name, post_date)
        athor_ele = soup.find(class_="ma-top-shares-left")
        if athor_ele:
            post_date_ele = soup.new_tag("div")
            post_date_ele.append(f"{post_date:{get_datetime_format()}}")
            athor_ele.append(post_date_ele)
            time_parent_ele = soup.find("div", class_="author-post-cont")
            if time_parent_ele:
                time_parent_ele.decompose()
        return soup
