import json
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import urlencode

from calibre.ptempfile import PersistentTemporaryDirectory, PersistentTemporaryFile


def format_title(feed_name, post_date):
    """
    Format title
    :return:
    """
    try:
        var_value = os.environ["newsrack_title_dt_format"]
        return f"{feed_name}: {post_date:{var_value}}"
    except:  # noqa
        return f"{feed_name}: {post_date:%-d %b, %Y}"


class BasicNewsrackRecipe(object):
    remove_javascript = True
    no_stylesheets = True
    compress_news_images = True
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images

    timeout = 20
    timefmt = ""  # suppress date output
    pub_date = None  # custom publication date
    temp_dir = None

    def publication_date(self):
        return self.pub_date

    def cleanup(self):
        if self.temp_dir:
            self.log("Deleting temp files...")
            shutil.rmtree(self.temp_dir)


class WordPressNewsrackRecipe(BasicNewsrackRecipe):
    use_embedded_content = False
    auto_cleanup = False  # don't clean up because it messes up the embed code and sometimes ruins the og-link logic

    def extract_authors(self, post):
        try:
            post_authors = [
                a["name"] for a in post.get("_embedded", {}).get("author", [])
            ]
        except (KeyError, TypeError):
            post_authors = []
        return post_authors

    def extract_categories(self, post):
        categories = []
        if post.get("categories"):
            try:
                for terms in post.get("_embedded", {}).get("wp:term", []):
                    categories.extend(
                        [t["name"] for t in terms if t["taxonomy"] == "category"]
                    )
            except (KeyError, TypeError):
                pass
        return categories

    def extract_tags(self, post):
        tags = []
        if post.get("tags"):
            try:
                for terms in post.get("_embedded", {}).get("wp:term", []):
                    tags.extend(
                        [t["name"] for t in terms if t["taxonomy"] == "post_tag"]
                    )
            except (KeyError, TypeError):
                pass
        return tags

    def populate_article_metadata(self, article, soup, _):
        # pick up the og link from preprocess_raw_html() and set it as url instead of the api endpoint
        og_link = soup.select_one("[data-og-link]")
        if og_link:
            article.url = og_link["data-og-link"]

    def get_posts(self, feed_url, oldest_article, custom_params, br):
        """
        Get posts from WP
        :param feed_url: WP posts endpoint
        :param oldest_article: in days
        :param custom_params: overwrite default params
        :param br: browser instance
        :return:
        """
        per_page = 100
        page = 1
        posts = []

        cutoff_date = datetime.today().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=oldest_article)

        if not custom_params:
            custom_params = {}

        while True:
            params = {
                "rest_route": "/wp/v2/posts",
                "page": page,
                "per_page": per_page,
                "after": cutoff_date.isoformat(),
                "_embed": "1",
                "_": int(time.time() * 1000),
            }
            params.update(custom_params)
            # clear out None values to allow custom_params to unset default params
            for k in [k for k in params.keys() if params[k] is None]:
                del params[k]

            endpoint = f"{feed_url}?{urlencode(params)}"
            self.log.debug(f"Fetching {endpoint} ...")
            try:
                res = br.open_novisit(endpoint)
                posts_json_raw = res.read().decode("utf-8")
                retrieved_posts = json.loads(posts_json_raw)
                if not retrieved_posts:
                    break
                posts.extend(retrieved_posts)
                try:
                    # abort early to save one extra request
                    headers = res.info()
                    if headers.get("x-wp-totalpages"):
                        wp_totalpages = int(headers["x-wp-totalpages"])
                        if wp_totalpages == page:
                            break
                except:
                    # do nothing else if we can't parse headers for page info
                    # rely on HTTP 400 to detect paging break
                    pass
                page += 1
            except:  # HTTP 400
                break

        return posts

    def get_articles(
        self, articles, feed_name, feed_url, oldest_article, custom_params, br
    ):
        """
        Extract articles

        :param articles:
        :param feed_name:
        :param feed_url: WP posts endpoint
        :param oldest_article: in days
        :param custom_params: overwrite default params
        :param br: browser instance
        :return:
        """
        posts = self.get_posts(feed_url, oldest_article, custom_params, br)

        self.temp_dir = PersistentTemporaryDirectory()
        latest_post_date = None
        for p in posts:
            post_update_dt = datetime.strptime(
                p["modified_gmt"], "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=timezone.utc)
            if not self.pub_date or post_update_dt > self.pub_date:
                self.pub_date = post_update_dt
            post_date = datetime.strptime(p["date"], "%Y-%m-%dT%H:%M:%S")
            if not latest_post_date or post_date > latest_post_date:
                latest_post_date = post_date
                self.title = format_title(feed_name, post_date)

            section_name = f"{post_date:%-d %B, %Y}"
            if len(self.get_feeds()) > 1:
                section_name = f"{feed_name}: {post_date:%-d %B, %Y}"
            if section_name not in articles:
                articles[section_name] = []

            with PersistentTemporaryFile(suffix=".json", dir=self.temp_dir) as f:
                f.write(json.dumps(p).encode("utf-8"))
            articles[section_name].append(
                {
                    "title": unescape(p["title"]["rendered"]) or "Untitled",
                    "url": "file://" + f.name,
                    "date": f"{post_date:%-d %B, %Y}",
                    "description": unescape(p["excerpt"]["rendered"]),
                }
            )
        return articles
