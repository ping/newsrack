# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

from datetime import datetime, timedelta, timezone
import time
from urllib.parse import urlencode
import json
import shutil

from calibre.web.feeds.news import BasicNewsRecipe
from calibre.ebooks.BeautifulSoup import BeautifulSoup
from calibre.ptempfile import PersistentTemporaryDirectory, PersistentTemporaryFile

_name = "The Third Pole"


class ThirdPole(BasicNewsRecipe):
    title = _name
    __author__ = "ping"
    description = (
        "The Third Pole is a multilingual platform dedicated to promoting "
        "information and discussion about the Himalayan watershed and the "
        "rivers that originate there. https://www.thethirdpole.net/"
    )
    language = "en"
    publication_type = "blog"
    oldest_article = 14  # days
    use_embedded_content = False
    encoding = "utf-8"
    remove_javascript = True
    no_stylesheets = True
    compress_news_images = True
    masthead_url = (
        "https://www.thethirdpole.net/content/uploads/2020/10/ThirdPoleLogo.svg"
    )
    scale_news_images = (800, 800)
    scale_news_images_to_device = False  # force img to be resized to scale_news_images
    auto_cleanup = True
    timeout = 20
    reverse_article_order = False
    timefmt = ""  # suppress date output
    pub_date = None  # custom publication date
    temp_dir = None

    remove_tags = [
        dict(class_=["block--related-news"]),
        dict(name=["script", "noscript", "style"]),
    ]

    extra_css = """
    .headline { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .article-meta {  margin-top: 1rem; margin-bottom: 1rem; }
    .article-meta .author { font-weight: bold; color: #444; margin-right: 0.5rem; }
    .article-section { display: block; font-weight: bold; color: #444; }
    .article-img img, .block--article-image__image img, .wp-caption img { display: block; max-width: 100%; height: auto; }
    .article-img .caption, .block--article-image__caption, .wp-caption-text {
        font-size: 0.8rem; display: block; margin-top: 0.2rem;
    }

    .block--pullout-stat, .block--accordion { margin-left: 0.5rem; font-family: monospace; text-align: left; }
    .block--pullout-stat .block--pullout-stat__title,
    .block--accordion .block--accordion__title
    { font-size: 1rem; font-weight: bold; margin-bottom: 0.4rem; }
    .block--pullout-stat .block--pullout-stat__content p,
    .block--accordion .block--accordion__content__inner p
    { margin: 0.2rem 0; }

    .block--pull-quote { text-align: center; }
    .block--pull-quote blockquote { margin-left: 0; margin-bottom: 0.4rem; font-size: 1.25rem; }
    .block--pull-quote cite { font-style: italic; font-size: 0.8rem; }
    """

    feeds = [
        (_name, "https://www.thethirdpole.net/wp-json/wp/v2/posts"),
    ]

    def _extract_featured_media(self, post, soup):
        """
        Include featured media with post content.

        :param post: post dict
        :param post_content: Extracted post content
        :return:
        """
        post_soup = BeautifulSoup(post["content"]["rendered"])
        for img in post_soup.find_all("img", attrs={"data-src": True}):
            img["src"] = img["data-src"]
        post_content = str(post_soup)
        if not post.get("featured_media"):
            return post_content

        feature_media_css = f"wp-image-{post['featured_media']}"
        if feature_media_css in post_content:
            # check already not embedded
            return post_content

        for feature_info in post.get("_embedded", {}).get("wp:featuredmedia", []):
            # put feature media at the start of the post
            if feature_info.get("source_url"):
                # higher-res
                container_ele = soup.new_tag("p", attrs={"class": "article-img"})
                img_ele = soup.new_tag("img", src=feature_info["source_url"])
                container_ele.append(img_ele)
                if feature_info.get("title", {}).get("rendered"):
                    cap_ele = soup.new_tag("span", attrs={"class": "caption"})
                    cap_ele.append(feature_info["title"]["rendered"])
                    container_ele.append(cap_ele)
                post_content = str(container_ele) + post_content
            else:
                post_content = (
                    feature_info.get("description", {}).get("rendered", "")
                    + post_content
                )
        return post_content

    def preprocess_raw_html(self, raw_html, url):
        # formulate the api response into html
        post = json.loads(raw_html)
        date_published_loc = datetime.strptime(post["date"], "%Y-%m-%dT%H:%M:%S")
        soup = BeautifulSoup(
            f"""<html>
        <head><title></title></head>
        <body>
            <article data-og-link="{post["link"]}">
            <h1 class="headline"></h1>
            <div class="article-meta">
                <span class="published-dt">
                    {date_published_loc:%-I:%M%p, %-d %b, %Y}
                </span>
            </div>
            </article>
        </body></html>"""
        )
        soup.head.title.string = post["title"]["rendered"]
        soup.find("h1").string = post["title"]["rendered"]
        soup.body.article.append(
            BeautifulSoup(self._extract_featured_media(post, soup))
        )
        # inject authors
        try:
            post_authors = [
                a["name"] for a in post.get("_embedded", {}).get("author", [])
            ]
            if post_authors:
                soup.find(class_="article-meta").insert(
                    0,
                    BeautifulSoup(
                        f'<span class="author">{", ".join(post_authors)}</span>'
                    ),
                )
        except (KeyError, TypeError):
            pass
        # inject categories
        if post.get("categories"):
            categories = []
            try:
                for terms in post.get("_embedded", {}).get("wp:term", []):
                    categories.extend(
                        [t["name"] for t in terms if t["taxonomy"] == "category"]
                    )
            except (KeyError, TypeError):
                pass
            if categories:
                soup.body.article.insert(
                    0,
                    BeautifulSoup(
                        f'<span class="article-section">{" / ".join(categories)}</span>'
                    ),
                )
        return str(soup)

    def populate_article_metadata(self, article, soup, first):
        # pick up the og link from preprocess_raw_html() and set it as url instead of the api endpoint
        og_link = soup.select("[data-og-link]")
        if og_link:
            article.url = og_link[0]["data-og-link"]

    def publication_date(self):
        return self.pub_date

    def cleanup(self):
        if self.temp_dir:
            self.log("Deleting temp files...")
            shutil.rmtree(self.temp_dir)

    def parse_index(self):
        br = self.get_browser()
        per_page = 100
        articles = {}
        self.temp_dir = PersistentTemporaryDirectory()

        for feed_name, feed_url in self.feeds:
            posts = []
            page = 1
            while True:
                cutoff_date = datetime.today().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=self.oldest_article)

                params = {
                    "page": page,
                    "per_page": per_page,
                    "after": cutoff_date.isoformat(),
                    "_embed": "1",
                    "_": int(time.time() * 1000),
                }
                endpoint = f"{feed_url}?{urlencode(params)}"
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
                    self.title = f"{feed_name}: {post_date:%-d %b, %Y}"

                section_name = f"{post_date:%-d %B, %Y}"
                if len(self.get_feeds()) > 1:
                    section_name = f"{feed_name}: {post_date:%-d %B, %Y}"
                if section_name not in articles:
                    articles[section_name] = []

                with PersistentTemporaryFile(suffix=".json", dir=self.temp_dir) as f:
                    f.write(json.dumps(p).encode("utf-8"))
                articles[section_name].append(
                    {
                        "title": p["title"]["rendered"] or "Untitled",
                        "url": "file://" + f.name,
                        "date": f"{post_date:%-d %B, %Y}",
                        "description": p["excerpt"]["rendered"],
                    }
                )

        return articles.items()
