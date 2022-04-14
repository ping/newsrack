# Original from https://github.com/kovidgoyal/calibre/blob/master/recipes/iht.recipe
from calibre.web.feeds.news import BasicNewsRecipe


class NYTimesGlobal(BasicNewsRecipe):
    title = "NY Times"
    language = "en"
    __author__ = "Krittika Goyal"
    publication_type = "newspaper"
    masthead_url = "https://mwcm.nyt.com/.resources/mkt-wcm/dist/libs/assets/img/logo-nyt-header.svg"

    oldest_article = 1  # days
    max_articles_per_feed = 25
    use_embedded_content = False
    timefmt = "%-d, %b %Y"
    pub_date = None  # custom publication date

    remove_javascript = True
    no_stylesheets = True
    auto_cleanup = False
    compress_news_images = True
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images

    ignore_duplicate_articles = {"title", "url"}

    remove_attributes = ["style", "font"]
    remove_tags_before = [dict(id="story")]
    remove_tags_after = [dict(id="story")]

    remove_tags = [
        dict(
            id=["in-story-masthead", "sponsor-wrapper", "top-wrapper", "bottom-wrapper"]
        ),
        dict(
            class_=[
                "NYTAppHideMasthead",
                "live-blog-meta",
                "css-13xl2ke",  # nyt logo in live-blog-byline
                "css-8r08w0",  # after storyline-context-container
            ]
        ),
        dict(role=["toolbar", "navigation", "contentinfo"]),
        dict(name=["script", "noscript", "style", "button"]),
    ]

    extra_css = """
    .live-blog-reporter-update {
        font-size: 0.8rem;
        padding: 0.2rem;
        margin-bottom: 0.5rem;
    }
    [data-testid="live-blog-byline"] {
        color: #444;
        font-style: italic;
    }
    [datetime] > span {
        margin-right: 0.6rem;
    }
    picture img {
        display: block; margin-bottom: 0.3rem; max-width: 100%; height: auto;
        box-sizing: border-box;
    }
    [aria-label="media"] {
        font-size: 0.8rem;
        display: block;
        margin-bottom: 1rem;
    }
    [role="complementary"] {
        font-size: 0.8rem;
        padding: 0.2rem;
    }
    [role="complementary"] h2 {
        font-size: 0.85rem;
        margin-bottom: 0.2rem;
     }
    """

    feeds = [
        ("Home", "https://www.nytimes.com/services/xml/rss/nyt/HomePage.xml"),
        # (
        #     "Global Home",
        #     "https://www.nytimes.com/services/xml/rss/nyt/GlobalHome.xml",
        # ),
        ("World", "https://www.nytimes.com/services/xml/rss/nyt/World.xml"),
        ("US", "https://www.nytimes.com/services/xml/rss/nyt/US.xml"),
        ("Business", "https://feeds.nytimes.com/nyt/rss/Business"),
        # ("Sports", "https://www.nytimes.com/services/xml/rss/nyt/Sports.xml"),
        ("Technology", "https://feeds.nytimes.com/nyt/rss/Technology"),
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
            self.title = f"NY Times: {article.utctime:%-d %b, %Y}"

    # overwrite
    def publication_date(self):
        return self.pub_date
