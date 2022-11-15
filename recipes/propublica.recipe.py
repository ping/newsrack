# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
propublica.org
"""
from calibre.web.feeds.news import BasicNewsRecipe

_name = "ProPublica"


class ProPublica(BasicNewsRecipe):
    title = _name
    description = (
        "ProPublica is an independent, nonprofit newsroom that produces investigative "
        "journalism with moral force. https://www.propublica.org/"
    )
    language = "en"
    __author__ = "ping"
    publication_type = "newspaper"
    oldest_article = 30  # days
    max_articles_per_feed = 25
    use_embedded_content = False
    no_stylesheets = True
    remove_javascript = True
    encoding = "utf-8"
    masthead_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/ProPublica_text_logo.svg/1280px-ProPublica_text_logo.svg.png"

    compress_news_images = True
    scale_news_images = (800, 1200)
    compress_news_images_auto_size = 10
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    auto_cleanup = False
    timeout = 60
    timefmt = ""
    pub_date = None  # custom publication date

    keep_only_tags = [dict(name="article")]
    remove_attributes = ["width", "height"]
    remove_tags = [
        dict(id=["newsletter-txt-note"]),
        dict(
            attrs={
                "class": [
                    "article-meta-1__section-actions",
                    "share-tools",
                    "story-tools",
                    "promo-newsletter-signup-2",
                    "promo-newsletter-see-all-2",
                    "promo-donate-2",
                    "bb-promo-story",
                    "bb-callout",
                    "promo-series",
                    "rich-byline__headshot",
                    "rich-byline__name",
                    "rich-byline__contact-list",
                ]
            }
        ),
        dict(name=["script", "noscript", "style", "svg", "form"]),
    ]

    extra_css = """
    h1 { font-size: 1.8rem; margin-bottom: 0.4rem; }
    h2 { font-size: 1.2rem; font-style: italic; margin-bottom: 1rem; font-weight: normal; }
    .article-meta-1__byline { font-weight: bold; color: #444; }
    .article-meta-1 { margin-bottom: 1rem; }
    .article img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box; }
    .article .attribution { font-size: 0.8rem; }
    .article .article-body__note { font-style: italic; }
    .topics-list {
        border-top: 1px solid #444;
        color: #444; margin-top: 1.5rem;
    }
    .rich-byline__info { color: #444; margin-top: 2rem; }
    """

    feeds = [
        ("ProPublica", "https://www.propublica.org/feeds/propublica/main"),
    ]

    def publication_date(self):
        return self.pub_date

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = f"{_name}: {article.utctime:%-d %b, %Y}"

    def preprocess_html(self, soup):
        for img in soup.select(".bb-image img.lazyload[data-srcset]"):
            img["src"] = img["data-srcset"].split(",")[-1].strip().split(" ")[0]
        lead_img = soup.find(class_="opener__art-wrapper")
        if lead_img:
            soup.find(class_="article-body").insert_before(lead_img)
        return soup
