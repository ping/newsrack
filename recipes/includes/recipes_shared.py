import json
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Optional, Dict, List
from urllib.parse import urlencode

from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.ptempfile import PersistentTemporaryDirectory, PersistentTemporaryFile
from calibre.utils.browser import Browser


def get_date_format() -> str:
    try:
        var_value = os.environ["newsrack_title_dt_format"]
    except:  # noqa
        var_value = "%-d %b, %Y"
    return var_value


def format_title(feed_name: str, post_date: datetime) -> str:
    """
    Format title
    :return:
    """
    return f"{feed_name}: {post_date:{get_date_format()}}"


class BasicNewsrackRecipe(object):
    remove_javascript = True
    no_stylesheets = True
    compress_news_images = True
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    ignore_duplicate_articles = {"url"}

    timeout = 20
    timefmt = ""  # suppress date output
    pub_date: Optional[datetime] = None  # custom publication date
    temp_dir: Optional[PersistentTemporaryDirectory] = None

    def publication_date(self) -> Optional[datetime]:
        return self.pub_date

    def cleanup(self) -> None:
        if self.temp_dir:
            self.log("Deleting temp files...")  # type: ignore[attr-defined]
            shutil.rmtree(self.temp_dir)


class WordPressNewsrackRecipe(BasicNewsrackRecipe):
    use_embedded_content = False
    auto_cleanup = False  # don't clean up because it messes up the embed code and sometimes ruins the og-link logic
    is_wordpresscom = False

    @staticmethod
    def parse_datetime(date_string, wordpresscom=False) -> datetime:
        # Can't use is_wordpresscom because I made this a staticmethod -_-
        return datetime.strptime(
            date_string, "%Y-%m-%dT%H:%M:%S%z" if wordpresscom else "%Y-%m-%dT%H:%M:%S"
        )

    def extract_authors(self, post: Dict) -> List:
        if self.is_wordpresscom:
            post_authors = []
            if post.get("author"):
                post_authors = [post["author"]["name"]]
        else:
            try:
                post_authors = [
                    a["name"] for a in post.get("_embedded", {}).get("author", [])
                ]
            except (KeyError, TypeError):
                post_authors = []
        return post_authors

    def extract_categories(self, post: Dict) -> List:
        categories = []
        if self.is_wordpresscom:
            if post.get("categories"):
                categories = [c["name"] for c in post["categories"].values()]
        else:
            if post.get("categories"):
                categories = [t["name"] for t in self.extract_terms(post, "category")]
        return categories

    def extract_tags(self, post: Dict) -> List:
        tags = []
        if self.is_wordpresscom:
            if post.get("tags"):
                tags = [c["name"] for c in post["tags"].values()]
        else:
            if post.get("tags"):
                tags = [t["name"] for t in self.extract_terms(post, "post_tag")]
        return tags

    def extract_terms(self, post: Dict, taxonomy: str) -> List:
        terms = []
        try:
            for wp_terms in post.get("_embedded", {}).get("wp:term", []):
                terms.extend([t for t in wp_terms if t["taxonomy"] == taxonomy])
        except (KeyError, TypeError):
            pass
        return terms

    def populate_article_metadata(self, article, soup, _):
        # pick up the og link from preprocess_raw_html() and set it as url instead of the api endpoint
        og_link = soup.select_one("[data-og-link]")
        if og_link:
            article.url = og_link["data-og-link"]

    def get_posts(
        self, feed_url: str, oldest_article: int, custom_params: Dict, br: Browser
    ) -> list:
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
            if self.is_wordpresscom:
                params = {
                    "page": page,
                    "number": per_page,
                    "after": cutoff_date.isoformat(),
                }
            else:
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
            self.log.debug(f"Fetching {endpoint} ...")  # type: ignore[attr-defined]
            retrieved_posts = []
            try:
                res = br.open_novisit(endpoint)
                posts_json_raw_bytes = res.read()
                encodings = ["utf-8", "utf-8-sig"]
                for i, encoding in enumerate(encodings, start=1):
                    try:
                        posts_json_raw = posts_json_raw_bytes.decode(encoding)
                        if self.is_wordpresscom:
                            retrieved_posts = json.loads(posts_json_raw).get(
                                "posts", []
                            )
                        else:
                            retrieved_posts = json.loads(posts_json_raw)
                        break
                    except json.decoder.JSONDecodeError as json_err:
                        self.log.warning(f"Error decoding json: {json_err}")
                        if i < len(encodings):
                            continue
                        raise

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
            except json.decoder.JSONDecodeError:
                raise
            except Exception as err:  # HTTP 400
                self.log.warning(f"Error encountered while fetching posts: {err}")
                break

        return posts

    def get_articles(
        self,
        articles: Dict,
        feed_name: str,
        feed_url: str,
        oldest_article: int,
        custom_params: Dict,
        br: Browser,
    ) -> Dict:
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
            if self.is_wordpresscom:
                # Example: 2023-04-04T10:09:05+06:00
                post_update_dt = self.parse_datetime(
                    p["modified"], self.is_wordpresscom
                )
                post_date = self.parse_datetime(p["date"], self.is_wordpresscom)
            else:
                post_update_dt = self.parse_datetime(p["modified_gmt"]).replace(
                    tzinfo=timezone.utc
                )
                post_date = self.parse_datetime(p["date"])

            if not self.pub_date or post_update_dt > self.pub_date:
                self.pub_date = post_update_dt
            if not latest_post_date or post_date > latest_post_date:
                latest_post_date = post_date
                self.title = format_title(feed_name, post_date)

            section_name = f"{post_date:{get_date_format()}}"
            if len(self.get_feeds()) > 1:  # type: ignore[attr-defined]
                section_name = f"{feed_name}: {post_date:{get_date_format()}}"
            if section_name not in articles:
                articles[section_name] = []

            with PersistentTemporaryFile(suffix=".json", dir=self.temp_dir) as f:
                f.write(json.dumps(p).encode("utf-8"))
            articles[section_name].append(
                {
                    "title": BeautifulSoup(
                        unescape(
                            p["title"]
                            if self.is_wordpresscom
                            else p["title"]["rendered"]
                        )
                    ).get_text()
                    or "Untitled",
                    "url": "file://" + f.name,
                    "date": f"{post_date:%-d %B, %Y}",
                    "description": unescape(
                        p["excerpt"]
                        if self.is_wordpresscom
                        else p["excerpt"]["rendered"]
                    ),
                }
            )
        return articles
