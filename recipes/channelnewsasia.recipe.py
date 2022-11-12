# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

"""
channelnewsasia.com
"""
from calibre.web.feeds.news import BasicNewsRecipe

_name = "ChannelNewsAsia"


class ChannelNewsAsia(BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = "CNA: Breaking News, Singapore News, World and Asia https://www.channelnewsasia.com/"
    publisher = "Mediacorp"
    category = "news, Singapore"
    publication_type = "newspaper"
    use_embedded_content = False
    no_stylesheets = True
    auto_cleanup = False
    remove_javascript = True
    encoding = "utf-8"
    language = "en"
    masthead_url = "https://www.channelnewsasia.com/sites/default/themes/mc_cna_theme/images/logo.png"

    oldest_article = 1
    max_articles_per_feed = 25
    compress_news_images = True
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    timeout = 20
    pub_date = None  # custom publication date

    remove_tags_before = [dict(class_=["h1--page-title"])]
    remove_tags_after = [dict(class_=["content"])]
    remove_attributes = ["style"]
    remove_tags = [
        dict(
            class_=[
                "js-popup-content",
                "referenced-card",
                "block--related-topics",
                "block-ad-entity",
                "block-block-content",
                "from-library",
                "block-field-blocknodearticlefield-author",  # author bio
                "mobile_author_card",  # author bio
            ]
        ),
        dict(name="div", attrs={"data-ad-entity": True}),
        dict(name="div", attrs={"data-js-options": True}),
        dict(name=["script", "noscript", "style", "svg"]),
    ]

    extra_css = """
    .figure__caption { font-size: 0.8rem; }
    .figure__caption p { margin-top: 0.2rem; margin-bottom: 1rem; }
    """

    feeds = [
        (
            "Latest News",
            "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
        ),
        (
            "Asia",
            "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",
        ),
        (
            "Business",
            "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936",
        ),
        (
            "Singapore",
            "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10416",
        ),
        (
            "Sport",
            "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10296",
        ),
        (
            "World",
            "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6311",
        ),
    ]

    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = f"{_name}: {article.utctime:%-d %b, %Y}"

    def publication_date(self):
        return self.pub_date
