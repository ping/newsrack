from calibre.web.feeds.news import BasicNewsRecipe


class NYTimesBooks(BasicNewsRecipe):
    title = "NY Times Books"
    language = "en"
    description = "The latest book reviews, best sellers, news and features from The NY TImes critics and reporters."
    __author__ = "ping"
    publication_type = "newspaper"
    oldest_article = 7  # days
    max_articles_per_feed = 25
    use_embedded_content = False
    timefmt = "%-d, %b %Y"
    pub_date = None  # custom publication date

    remove_javascript = True
    no_stylesheets = True
    auto_cleanup = False
    compress_news_images = True
    scale_news_images = (600, 600)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images

    remove_attributes = ["style", "font"]
    remove_tags_before = [dict(id="story")]
    remove_tags_after = [dict(id="story")]
    remove_tags = [
        dict(
            id=["in-story-masthead", "sponsor-wrapper", "top-wrapper", "bottom-wrapper"]
        ),
        dict(class_=["NYTAppHideMasthead"]),
        dict(role=["toolbar", "navigation"]),
        dict(name=["script", "noscript", "style"]),
        dict(name="div", attrs={"data-testid": "photoviewer-children"}),
    ]

    extra_css = """time > span { margin-right: 0.5rem; }"""

    feeds = [
        ("NYTimes Books", "https://rss.nytimes.com/services/xml/rss/nyt/Books.xml"),
    ]

    # overwrite
    def get_browser(self, *a, **kw):
        kw[
            "user_agent"
        ] = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        br = BasicNewsRecipe.get_browser(self, *a, **kw)
        return br

    # overwrite
    def populate_article_metadata(self, article, __, _):
        if (not self.pub_date) or article.utctime > self.pub_date:
            self.pub_date = article.utctime
            self.title = f"NY Times Books: {article.utctime:%-d %b, %Y}"

    # overwrite
    def publication_date(self):
        return self.pub_date
