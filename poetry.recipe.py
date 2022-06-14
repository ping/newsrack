from collections import OrderedDict
from datetime import datetime, timezone
from calibre.web.feeds.news import BasicNewsRecipe


_name = "Poetry"


class Nature(BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "Founded in Chicago by Harriet Monroe in 1912, Poetry is the oldest monthly "
        "devoted to verse in the English-speaking world."
    )
    publication_type = "magazine"
    language = "en"
    encoding = "utf-8"

    ignore_duplicate_articles = {"url"}
    no_javascript = True
    no_stylesheets = True
    # compress_news_images = True
    scale_news_images = (800, 1200)
    timeout = 20
    timefmt = ""
    pub_date = None  # custom publication date

    remove_attributes = ["style", "font"]
    keep_only_tags = [dict(name="article")]

    remove_tags = [
        dict(
            attrs={
                "class": ["c-socialBlocks", "c-index", "o-stereo", "u-hideAboveSmall"]
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

    def publication_date(self):
        return self.pub_date

    def preprocess_html(self, soup):
        for img in soup.select("div.o-mediaEnclosure img"):
            if not img.get("srcset"):
                continue
            img["src"] = img["srcset"].split(",")[-1].strip().split(" ")[0]
        return soup

    def parse_index(self):
        soup = self.index_to_soup("https://www.poetryfoundation.org/poetrymagazine")
        current_issue = soup.select("div.c-cover-media a")
        if not current_issue:
            self.abort_recipe_processing("Unable to find latest issue")

        current_issue = current_issue[0]
        cover_image = current_issue.find("img")
        self.cover_url = cover_image["srcset"].split(",")[-1].strip().split(" ")[0]

        soup = self.index_to_soup(current_issue["href"])
        issue_edition = self.tag_to_string(soup.find("h1"))
        self.pub_date = datetime.strptime(issue_edition, "%B %Y").replace(
            tzinfo=timezone.utc
        )
        self.title = f"{_name}: {issue_edition}"

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
