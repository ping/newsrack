from calibre.web.feeds.news import BasicNewsRecipe, classes

_name = "દિવ્ય ભાસ્કર"


class DivyaBhaskar(BasicNewsRecipe):
    title = _name
    description = "Divya Bhaskar is an Indian Gujarati-language daily newspaper owned by the Dainik Bhaskar Group. It is ranked 4th in the world by circulation and is the largest newspaper in India by circulation."
    language = "gu"
    __author__ = "unkn0wn"
    oldest_article = 1  # days
    max_articles_per_feed = 50
    encoding = "utf-8"
    use_embedded_content = False
    masthead_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Divya_Bhaskar_%282019-11-01%29.svg/1920px-Divya_Bhaskar_%282019-11-01%29.svg.png"
    no_stylesheets = True
    remove_attributes = ["style", "height", "width"]
    ignore_duplicate_articles = {"url"}
    compress_news_images = True
    compress_news_images_auto_size = 10
    scale_news_images = (800, 800)

    def get_cover_url(self):
        soup = self.index_to_soup("https://epaper.divyabhaskar.co.in/")
        tag = soup.find(attrs={"class": "scaleDiv"})
        if tag:
            self.cover_url = tag.find("img")["src"].replace("_ss.jpg", "_l.jpg")
        return super().get_cover_url()

    keep_only_tags = [
        classes("f5afa1d3"),
    ]

    remove_tags = [
        classes(
            "_3c197847 _66d97d7f e0d43c76 bhaskar-widget-container-class _28e65306 _8adadf19 _07c65a39"
        ),
        dict(name="svg"),
    ]

    feeds = [
        ("Gujarat", "https://www.divyabhaskar.co.in/rss-v1--category-1035.xml"),
        ("National", "https://divyabhaskar.co.in/rss-v1--category-1037.xml"),
        ("DvB Original", "https://divyabhaskar.co.in/rss-v1--category-11879.xml"),
        ("International", "https://divyabhaskar.co.in/rss-v1--category-1038.xml"),
        ("Sports", "https://divyabhaskar.co.in/rss-v1--category-970.xml"),
        ("Business", "https://divyabhaskar.co.in/rss-v1--category-969.xml"),
        ("Lifestyle", "https://divyabhaskar.co.in/rss-v1--category-5029.xml"),
        ("Utility", "https://divyabhaskar.co.in/rss-v1--category-10695.xml"),
        ("Entertainment", "https://divyabhaskar.co.in/rss-v1--category-12042.xml"),
    ]


calibre_most_common_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36"
