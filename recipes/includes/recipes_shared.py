import json
import os
import re
import shutil
import time
import warnings
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Optional, Dict, List, Callable
from urllib.parse import urlencode

from calibre import browser
from calibre.constants import iswindows
from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.ptempfile import PersistentTemporaryDirectory, PersistentTemporaryFile
from calibre.utils.browser import Browser
from calibre.web.feeds import Feed


def get_date_format() -> str:
    try:
        var_value = os.environ["newsrack_title_dt_format"]
    except:  # noqa
        # %-d is not available on Windoows
        var_value = "%d %b, %Y" if iswindows else "%-d %b, %Y"
    return var_value


def get_datetime_format() -> str:
    try:
        var_value = os.environ["newsrack_title_dts_format"]
    except:  # noqa
        var_value = "%I:%M%p, %-d %b, %Y" if iswindows else "%-I:%M%p, %-d %b, %Y"
    return var_value


def parse_date(
    date_string: str,
    tz_info: Optional[timezone] = timezone.utc,
    as_utc: bool = True,
    **kwargs,
):
    """

    :param date_string:
    :param tz_info: Sets the parsed date to this timezone if it does not have a tz
    :param as_utc: Returns value as a UTC datetime if True
    :param kwargs: Other kwargs passed to parse()
    :return:
    """
    # Inspired by: https://github.com/kovidgoyal/calibre/blob/ec9e64437cbd378c50dc0fc9f8261a958781ef8e/src/calibre/utils/date.py#L88C29-L116

    # Difference:
    # - defaults to day 1
    # - allows custom tz

    from dateutil.parser import parse  # provided by calibre

    if not date_string:
        return None
    if "default" not in kwargs:
        kwargs["default"] = datetime.now(tz_info).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
    dt = parse(date_string, **kwargs)
    if tz_info and dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz_info)
    if as_utc:
        return dt.astimezone(timezone.utc)
    return dt


def format_title(feed_name: str, post_date: datetime) -> str:
    """
    Format title
    :return:
    """
    return f"{feed_name}: {post_date:{get_date_format()}}"


COMMA_SEP_RE = re.compile(r"\s*,\s*")
SPACE_SEP_RE = re.compile(r"\s+")
NON_NUMERIC_RE = re.compile(r"[^\d]+")


def extract_from_img_srcset(srcset: str, max_width=0):
    sources = [s.strip() for s in COMMA_SEP_RE.split(srcset) if s.strip()]
    if len(sources) == 1:
        # just regular img url probably
        return sources[0]
    parsed_sources = []
    for src in sources:
        src_n_width = [s.strip() for s in SPACE_SEP_RE.split(src) if s.strip()]
        if len(src_n_width) != 2:
            raise ValueError(f"Not a valid srcset: {srcset}")
        parsed_sources.append(
            (
                src_n_width[0].strip(),
                int(NON_NUMERIC_RE.sub("", src_n_width[1].strip())),
            )
        )
    parsed_sources = list(set(parsed_sources))
    parsed_sources = sorted(parsed_sources, key=lambda x: x[1], reverse=True)
    if not max_width:
        return parsed_sources[0][0]
    for img, width in parsed_sources:
        if width <= max_width:
            return img
    return parsed_sources[-1][0]


class BasicNewsrackRecipe(object):
    encoding = "utf-8"
    remove_javascript = True
    no_stylesheets = True
    auto_cleanup = False
    compress_news_images = True
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    ignore_duplicate_articles = {"url"}
    use_embedded_content = False
    remove_empty_feeds = True

    timeout = 20
    timefmt = ""  # suppress date output
    pub_date: Optional[datetime] = None  # custom publication date
    temp_dir: Optional[PersistentTemporaryDirectory] = None

    def publication_date(self) -> Optional[datetime]:
        return self.pub_date

    def parse_date(
        self,
        date_string: str,
        tz_info: Optional[timezone] = timezone.utc,
        as_utc: bool = True,
        **kwargs,
    ):
        """

        :param date_string:
        :param tz_info: Sets the parsed date to this timezone if it does not have a tz
        :param as_utc: Returns value as a UTC datetime if True
        :param kwargs: Other kwargs passed to parse()
        :return:
        """
        return parse_date(date_string, tz_info, as_utc, **kwargs)

    def cleanup(self) -> None:
        if self.temp_dir:
            self.log("Deleting temp files...")  # type: ignore[attr-defined]
            shutil.rmtree(self.temp_dir)

    def get_ld_json(self, soup: BeautifulSoup, filter_fn: Callable, attrs=None) -> Dict:
        """
        Get the script element containing the LD-JSON content

        :param soup:
        :param filter_fn:
        :param attrs:
        :return:
        """
        if attrs is None:
            attrs = {"type": "application/ld+json"}
        for script_json in soup.find_all("script", attrs=attrs):
            if not script_json.contents:
                continue
            data = json.loads(script_json.contents[0])
            if filter_fn(data):
                return data
        return {}

    def get_script_json(
        self, soup: BeautifulSoup, prefix_expr: str, attrs=None
    ) -> Dict:
        """
        Converts a script element's json content into a dict object

        :param soup:
        :param prefix_expr:
        :param attrs:
        :return:
        """
        if attrs is None:
            attrs = {"src": False}
        prefix_expr_re = re.compile(prefix_expr) if prefix_expr else None
        for script in soup.find_all("script", attrs):
            if not script.contents:
                continue
            script_js = script.contents[0].strip()
            if prefix_expr and not prefix_expr_re.match(script_js):
                continue
            if prefix_expr:
                script_js = prefix_expr_re.sub("", script_js)
            if script_js.endswith(";"):
                script_js = script_js[:-1]
            script_js = script_js.replace(":undefined", ":null")
            try:
                return json.loads(script_js)
            except json.JSONDecodeError:
                # sometimes this borks because of a stray '\n', e.g. scmp
                try:
                    return json.loads(script_js.replace("\n", " "))
                except json.JSONDecodeError:
                    self.log.exception("Unable to parse script as json")
                    self.log.debug(script.contents[0])
        return {}

    def extract_from_img_srcset(self, srcset: str, max_width=0):
        return extract_from_img_srcset(srcset, max_width)

    def debug_json_dump(self, obj, indent=2):
        self.log.debug(json.dumps(obj, indent=indent))

    def generate_debug_index(self, urls):
        """
        Helper function to debug articles. To be used in parse_index().

        :param urls:
        :return:
        """
        return [
            (
                "Tests",
                [
                    {"title": f"Test {n}", "url": url}
                    for n, url in enumerate(urls, start=1)
                ],
            )
        ]

    def group_feeds_by_date(
        self, timezone_offset_hours: int = 0, filter_article: Optional[Callable] = None
    ):
        """
        Group feed articles by date

        :param timezone_offset_hours:
        :param filter_article:
        :return:
        """
        parsed_feeds = super().parse_feeds()
        if len(parsed_feeds or []) != 1:
            return parsed_feeds

        articles = []
        for feed in parsed_feeds:
            if filter_article:
                articles.extend([a for a in feed.articles if filter_article(a)])
            else:
                articles.extend(feed.articles)
        articles = sorted(articles, key=lambda a: a.utctime, reverse=True)
        new_feeds = []
        curr_feed = None
        parsed_feed = parsed_feeds[0]

        for i, a in enumerate(articles, start=1):
            date_published = a.utctime.replace(tzinfo=timezone.utc)
            date_published_loc = date_published.astimezone(
                timezone(offset=timedelta(hours=timezone_offset_hours))
            )
            article_index = f"{date_published_loc:{get_date_format()}}"
            if i == 1:
                curr_feed = Feed(log=parsed_feed.logger)
                curr_feed.title = article_index
                curr_feed.description = parsed_feed.description
                curr_feed.image_url = parsed_feed.image_url
                curr_feed.image_height = parsed_feed.image_height
                curr_feed.image_alt = parsed_feed.image_alt
                curr_feed.oldest_article = parsed_feed.oldest_article
                curr_feed.articles = []
            if curr_feed.title == article_index:
                curr_feed.articles.append(a)
            else:
                new_feeds.append(curr_feed)
                curr_feed = Feed(log=parsed_feed.logger)
                curr_feed.title = article_index
                curr_feed.description = parsed_feed.description
                curr_feed.image_url = parsed_feed.image_url
                curr_feed.image_height = parsed_feed.image_height
                curr_feed.image_alt = parsed_feed.image_alt
                curr_feed.oldest_article = parsed_feed.oldest_article
                curr_feed.articles = []
                curr_feed.articles.append(a)
            if i == len(articles):
                # last article
                new_feeds.append(curr_feed)

        return new_feeds


class BasicCookielessNewsrackRecipe(BasicNewsrackRecipe):
    """
    The basic recipe extended to not send cookies. This is meant for news
    sources that change the content it delivers based on cookies.
    """

    request_as_gbot = False  # flag to toggle gbot emulation

    def get_browser(self, *args, **kwargs):
        return self

    def clone_browser(self, *args, **kwargs):
        return self.get_browser()

    def open_novisit(self, *args, **kwargs):
        br = browser()
        if self.request_as_gbot:
            br.addheaders = [
                (
                    "User-agent",
                    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                ),
                ("Referer", "https://www.google.com/"),
                ("X-Forwarded-For", "66.249.66.1"),
            ]
        br.set_handle_gzip(True)
        return br.open_novisit(*args, **kwargs)

    open = open_novisit


class WordPressNewsrackRecipe(BasicNewsrackRecipe):
    use_embedded_content = False
    auto_cleanup = False  # don't clean up because it messes up the embed code and sometimes ruins the og-link logic
    is_wordpresscom = False

    @staticmethod
    def parse_datetime(date_string, wordpresscom=False) -> datetime:
        """
        Deprecated in favour of parse_date(date_string, tz_info=None, as_utc=False).

        :param date_string:
        :param wordpresscom:
        :return:
        """
        # Can't use self.is_wordpresscom because I made this a staticmethod -_-
        warnings.warn(
            "WordPressNewsrackRecipe.parse_datetime() is deprecated in favour of "
            "self.parse_date(date_string, tz_info=None, as_utc=False)",
            DeprecationWarning,
        )  # 2023.06.19 - remove in 6 mths
        return parse_date(date_string, tz_info=None, as_utc=False)

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
                res = br.open_novisit(endpoint, timeout=self.timeout)
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
        group_by_date: bool = True,
    ) -> Dict:
        """
        Extract articles

        :param articles:
        :param feed_name:
        :param feed_url: WP posts endpoint
        :param oldest_article: in days
        :param custom_params: overwrite default params
        :param br: browser instance
        :param group_by_date: group posts by date
        :return:
        """
        posts = self.get_posts(feed_url, oldest_article, custom_params, br)

        self.temp_dir = PersistentTemporaryDirectory()
        latest_post_date = None
        for p in posts:
            if self.is_wordpresscom:
                # Example: 2023-04-04T10:09:05+06:00
                post_update_dt = self.parse_date(
                    p["modified"], tz_info=None, as_utc=False
                )
                post_date = self.parse_date(p["date"], tz_info=None, as_utc=False)
            else:
                post_update_dt = self.parse_date(
                    p["modified_gmt"], tz_info=timezone.utc
                )
                post_date = self.parse_date(p["date"], tz_info=None, as_utc=False)

            if not self.pub_date or post_update_dt > self.pub_date:
                self.pub_date = post_update_dt
            if not latest_post_date or post_date > latest_post_date:
                latest_post_date = post_date
                self.title = format_title(feed_name, post_date)

            if group_by_date:
                section_name = f"{post_date:{get_date_format()}}"
                if len(self.get_feeds()) > 1:  # type: ignore[attr-defined]
                    section_name = f"{feed_name}: {post_date:{get_date_format()}}"
            else:
                section_name = feed_name

            with PersistentTemporaryFile(suffix=".json", dir=self.temp_dir) as f:
                f.write(json.dumps(p).encode("utf-8"))
                articles.setdefault(section_name, []).append(
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
                        "date": f"{post_date:{get_date_format()}}",
                        "description": unescape(
                            p["excerpt"]
                            if self.is_wordpresscom
                            else p["excerpt"]["rendered"]
                        ),
                    }
                )
        return articles
