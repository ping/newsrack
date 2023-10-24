# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0
import os
import re
import sys
from collections import OrderedDict
from urllib.parse import urlparse

# custom include to share code between recipes
sys.path.append(os.environ["recipes_includes"])
from recipes_shared import BasicNewsrackRecipe

from calibre.web.feeds.news import BasicNewsRecipe

_issue_url = ""
_name = "Poetry"


class Poetry(BasicNewsrackRecipe, BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Founded in Chicago by Harriet Monroe in 1912, Poetry is the oldest monthly "
        "devoted to verse in the English-speaking world. https://www.poetryfoundation.org/poetrymagazine"
    )
    publication_type = "magazine"
    language = "en"
    compress_news_images = False
    scale_news_images = (800, 1200)

    remove_attributes = ["style", "font"]
    keep_only_tags = [dict(name="article")]

    remove_tags = [
        dict(name="button"),
        dict(
            attrs={
                "class": [
                    "c-socialBlocks",
                    "c-index",
                    "o-stereo",
                    "u-hideAboveSmall",
                    "c-slideTrigger",
                    "js-slideshow",
                ]
            }
        ),
    ]

    extra_css = """
    h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
    .o-titleBar-summary { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; }
    div.o-titleBar-meta, div.c-feature-sub { font-weight: bold; color: #444; margin-bottom: 1.5rem; }
    div.pcms_media img, div.o-mediaEnclosure img { max-width: 100%; height: auto; }
    div.o-mediaEnclosure .o-mediaEnclosure-metadata { font-size: 0.8rem; margin-top: 0.2rem; }
    div.c-feature-bd { margin-bottom: 2rem; }
    div.c-auxContent { color: #222; font-size: 0.85rem; margin-top: 2rem; }
    """

    def preprocess_html(self, soup):
        for img in soup.select("div.o-mediaEnclosure img"):
            if not img.get("srcset"):
                continue
            img["src"] = self.extract_from_img_srcset(img["srcset"], max_width=1000)
        return soup

    def parse_index(self):
        if _issue_url:
            soup = self.index_to_soup(_issue_url)
        else:
            soup = self.index_to_soup("https://www.poetryfoundation.org/poetrymagazine")
            current_issue = soup.select("div.c-cover-media a")
            if not current_issue:
                self.abort_recipe_processing("Unable to find latest issue")
            current_issue = current_issue[0]
            soup = self.index_to_soup(current_issue["href"])

        issue_edition = self.tag_to_string(soup.find("h1"))
        self.title = f"{_name}: {issue_edition}"
        try:
            # "%B %Y"
            self.pub_date = self.parse_date(issue_edition)
        except ValueError:
            # 2-month issue e.g. "July/August 2021"
            mobj = re.match(
                r"(?P<mth>\w+)/\w+ (?P<yr>\d{4})", issue_edition, re.IGNORECASE
            )
            if not mobj:
                self.abort_recipe_processing("Unable to parse issue date")
            self.pub_date = self.parse_date(f'{mobj.group("mth")} {mobj.group("yr")}')

        cover_image = soup.select("div.c-issueBillboard-cover-media img")[0]
        parsed_cover_url = urlparse(
            cover_image["srcset"].split(",")[-1].strip().split(" ")[0]
        )
        self.cover_url = f"{parsed_cover_url.scheme}://{parsed_cover_url.netloc}{parsed_cover_url.path}"

        sectioned_feeds = OrderedDict()

        tabs = soup.find_all("div", attrs={"class": "c-tier_tabbed"})
        for tab in tabs:
            tab_title = tab.find("div", attrs={"class": "c-tier-tab"})
            tab_content = tab.find("div", attrs={"class": "c-tier-content"})
            if not (tab_title and tab_content):
                continue
            tab_title = self.tag_to_string(tab_title)
            sectioned_feeds[tab_title] = []
            for li in tab_content.select("ul.o-blocks > li"):
                author = self.tag_to_string(
                    li.find("span", attrs={"class": "c-txt_attribution"})
                )
                for link in li.find_all("a", attrs={"class": "c-txt_abstract"}):
                    self.log("Found article:", self.tag_to_string(link))
                    sectioned_feeds[tab_title].append(
                        {
                            "title": self.tag_to_string(link),
                            "url": link["href"],
                            "author": author,
                            "description": author,
                        }
                    )

        return sectioned_feeds.items()
