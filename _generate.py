import os
import sys
import logging
from datetime import datetime, timezone, timedelta
import time
import re
import subprocess
from collections import namedtuple
import glob
import json
from urllib.parse import urljoin, urlparse
import shutil
from timeit import default_timer as timer
import argparse
import textwrap
from functools import cmp_to_key

import requests
import humanize
from PIL import Image, ImageDraw, ImageFont

from _recipes import recipes

logger = logging.getLogger(__file__)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("publish_site", type=str, help="Deployment site url")
parser.add_argument(
    "-v",
    "--verbose",
    dest="verbose",
    action="store_true",
    help="Enable more verbose messages for debugging",
)
args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)

start_time = timer()
publish_folder = "public"
publish_site = args.publish_site
if not publish_site.endswith("/"):
    publish_site += "/"

parsed_site = urlparse(publish_site)
username, domain, _ = parsed_site.netloc.split(".")
source_url = f"https://{domain}.com/{username}{parsed_site.path}"

# for cover generation
font_big = ImageFont.truetype("static/OpenSans-Bold.ttf", 82)
font_med = ImageFont.truetype("static/OpenSans-Semibold.ttf", 72)

RecipeOutput = namedtuple(
    "RecipeOutput", ["title", "file", "rename_to", "published_dt", "category"]
)

# default style
with open("static/site.css", "r", encoding="utf-8") as f:
    site_css = f.read()

# default style
with open("static/site.js", "r", encoding="utf-8") as f:
    site_js = f.read()


# use environment variables to skip certain recipes in CI
skip_recipes_slugs = []
try:
    skip_recipes_slugs = str(os.environ["skip"])
    skip_recipes_slugs = [r.strip() for r in skip_recipes_slugs.split(",") if r.strip()]
except (KeyError, ValueError):
    pass

regenerate_recipes_slugs = []
try:
    regenerate_recipes_slugs = str(os.environ["regenerate"])
    regenerate_recipes_slugs = [
        r.strip() for r in regenerate_recipes_slugs.split(",") if r.strip()
    ]
except (KeyError, ValueError):
    pass

verbose_mode = False
try:
    verbose_mode = str(os.environ["verbose"]).strip()
except (KeyError, ValueError):
    pass


# fetch index.json from published site
def fetch_cache():
    res = requests.get(urljoin(publish_site, "index.json"), timeout=15)
    try:
        res.raise_for_status()
        return res.json()
    except Exception as err:  # noqa
        logger.exception("[!] Error fetching index.json")
        return {}


def generate_cover(file_name, title_text, cover_width=889, cover_height=1186):
    """
    Generate a plain image cover file

    :param file_name: Filename to be saved as
    :param title_text: Cover text
    :param cover_width: Width
    :param cover_height: Height
    :return:
    """
    rectangle_offset = 25
    title_texts = [t.strip() for t in title_text.split(":")]

    img = Image.new("RGB", (cover_width, cover_height), color="white")
    img_draw = ImageDraw.Draw(img)
    # rectangle outline
    img_draw.rectangle(
        (
            rectangle_offset,
            rectangle_offset,
            cover_width - rectangle_offset,
            cover_height - rectangle_offset,
        ),
        width=2,
        outline="black",
    )

    total_height = 0
    line_gap = 25
    text_w_h = []
    for i, text in enumerate(title_texts):
        if i == 0:
            wrapper = textwrap.TextWrapper(width=15)
            word_list = wrapper.wrap(text=text)

            for ii in word_list[:-1]:
                text_w, text_h = img_draw.textsize(ii, font=font_big)
                text_w_h.append([ii, text_w, text_h, text_h, font_big])
                total_height += text_h + line_gap

            text_w, text_h = img_draw.textsize(word_list[-1], font=font_big)
            text_w_h.append([word_list[-1], text_w, text_h, text_h, font_big])
            total_height += text_h + line_gap
        else:
            text_w, text_h = img_draw.textsize(text, font=font_med)
            text_w_h.append([text, text_w, text_h, text_h, font_med])
            total_height += text_h + line_gap

    cumu_offset = 0
    for text, text_w, text_h, h_offset, font in text_w_h:
        img_draw.text(
            (
                int((cover_width - text_w) / 2),
                int((cover_height - total_height) / 2) + cumu_offset,
            ),
            text,
            font=font,
            fill="black",
        )
        cumu_offset += h_offset
    img.save(file_name)


generated = {}
today = datetime.utcnow().replace(tzinfo=timezone.utc)
index = {}  # generate index.json
cached = fetch_cache()
cache_sess = requests.Session()

for recipe in recipes:
    if recipe.slug in skip_recipes_slugs:
        logger.info(f'[!] SKIPPED recipe: "{recipe.slug}"')
        continue

    logger.info(f'{"-" * 20} Executing "{recipe.name}" recipe... {"-" * 30}')
    recipe_start_time = timer()

    if recipe.category not in generated:
        generated[recipe.category] = {}
    generated[recipe.category][recipe.name] = []
    index[recipe.name] = []

    source_file_name = f"{recipe.slug}.{recipe.src_ext}"
    source_file_path = os.path.join(publish_folder, source_file_name)
    cmd = [
        "ebook-convert",
        f"{recipe.recipe}.recipe",
        source_file_path,
        "--dont-download-recipe",
    ]
    if recipe.src_ext == "mobi":
        cmd.extend(["--output-profile=kindle_oasis", "--mobi-file-type=both"])
    if verbose_mode:
        cmd.append("-vv")

    exit_code = 0

    # use glob for re-run cases in local dev
    if not glob.glob(publish_folder + f"/{recipe.slug}*.{recipe.src_ext}"):
        # existing file does not exist
        try:
            # regenerate restriction is not in place and recipe is enabled
            if (recipe.is_enabled() and not regenerate_recipes_slugs) or (
                # regenerate restriction is in place and recipe is included
                regenerate_recipes_slugs
                and recipe.slug in regenerate_recipes_slugs
            ):
                # run recipe
                exit_code = subprocess.call(
                    cmd,
                    timeout=recipe.timeout,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )
            else:
                # use cache
                logger.warning(f'Using cached copy for "{recipe.name}".')
                if cached.get(recipe.name):
                    for name in cached[recipe.name]:
                        ebook_url = urljoin(publish_site, name)
                        ebook_res = cache_sess.get(ebook_url, timeout=15, stream=True)
                        ebook_res.raise_for_status()
                        with open(
                            os.path.join(publish_folder, os.path.basename(ebook_url)),
                            "wb",
                        ) as f:
                            shutil.copyfileobj(ebook_res.raw, f)
                else:
                    # not cached, so run it anyway to ensure that we try to have a copy
                    logger.warning(f'"{recipe.name}" is not cached.')
                    exit_code = subprocess.call(
                        cmd,
                        timeout=recipe.timeout,
                        stdout=sys.stdout,
                        stderr=sys.stderr,
                    )

        except subprocess.TimeoutExpired:
            logger.exception(f"[!] TimeoutExpired fetching '{recipe.name}'")
            recipe_elapsed_time = timedelta(seconds=timer() - recipe_start_time)
            logger.info(
                f'{"=" * 10} "{recipe.name}" recipe took {humanize.precisedelta(recipe_elapsed_time)} {"=" * 20}'
            )
            continue

    source_file_paths = sorted(
        glob.glob(publish_folder + f"/{recipe.slug}*.{recipe.src_ext}")
    )
    if not source_file_paths:
        logger.error(
            f"Unable to find source generated: '/{recipe.slug}*.{recipe.src_ext}'"
        )
        recipe_elapsed_time = timedelta(seconds=timer() - recipe_start_time)
        logger.info(
            f'{"=" * 20} "{recipe.name}" recipe took {humanize.precisedelta(recipe_elapsed_time)} {"=" * 20}'
        )
        continue

    source_file_path = source_file_paths[-1]
    source_file_name = os.path.basename(source_file_path)

    if not exit_code:
        logger.debug(f'Get book meta info for "{source_file_path}"')
        proc = subprocess.Popen(
            ["ebook-meta", source_file_path], stdout=subprocess.PIPE
        )
        meta_out = proc.stdout.read().decode("utf-8")
        mobj = re.search(
            r"Published\s+:\s(?P<pub_date>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
            meta_out,
        )
        pub_date = today
        if mobj:
            pub_date = datetime.strptime(
                mobj.group("pub_date"), "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=timezone.utc)
        title = ""
        mobj = re.search(r"Title\s+:\s(?P<title>.+)", meta_out)
        if mobj:
            title = mobj.group("title")
        rename_file_name = f"{recipe.slug}-{pub_date:%Y-%m-%d}.{recipe.src_ext}"
        generated[recipe.category][recipe.name].append(
            RecipeOutput(
                title=title,
                file=source_file_name,
                rename_to=rename_file_name,
                published_dt=pub_date,
                category=recipe.category,
            )
        )

        # (rename_file_name != source_file_name) checks that it is a newly generated file
        # so that we don't regenerate the cover needlessly
        if recipe.overwrite_cover and title and rename_file_name != source_file_name:
            # customise cover
            logger.debug(f'Setting cover for "{source_file_path}"')
            try:
                cover_file_path = f"{source_file_path}.png"
                generate_cover(cover_file_path, title)
                cover_cmd = [
                    "ebook-meta",
                    source_file_path,
                    f"--cover={cover_file_path}",
                ]
                _ = subprocess.call(cover_cmd, stdout=subprocess.PIPE)
                os.remove(cover_file_path)
            except Exception:  # noqa
                logger.exception("Error generating cover")

        index[recipe.name].append(f"{recipe.slug}-{pub_date:%Y-%m-%d}.{recipe.src_ext}")

        # convert generate book into alternative formats
        for ext in recipe.target_ext:
            target_file_name = f"{recipe.slug}.{ext}"
            target_file_path = os.path.join(publish_folder, target_file_name)

            cmd = [
                "ebook-convert",
                source_file_path,
                target_file_path,
            ]
            if not glob.glob(publish_folder + f"/{recipe.slug}*.{ext}"):
                exit_code = subprocess.call(
                    cmd,
                    timeout=recipe.timeout,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )
            target_file_path = sorted(
                glob.glob(publish_folder + f"/{recipe.slug}*.{ext}")
            )[-1]
            target_file_name = os.path.basename(target_file_path)

            if not exit_code:
                generated[recipe.category][recipe.name].append(
                    RecipeOutput(
                        title=title,
                        file=target_file_name,
                        rename_to=f"{recipe.slug}-{pub_date:%Y-%m-%d}.{ext}",
                        published_dt=pub_date,
                        category=recipe.category,
                    )
                )
                index[recipe.name].append(f"{recipe.slug}-{pub_date:%Y-%m-%d}.{ext}")

        recipe_elapsed_time = timedelta(seconds=timer() - recipe_start_time)
        logger.info(
            f'{"=" * 20} "{recipe.name}" recipe took {humanize.precisedelta(recipe_elapsed_time)} {"=" * 20}'
        )


sorted_categories = ["news", "magazine", "books"]


def sort_category(a, b):
    try:
        a_index = sorted_categories.index(a[0])
    except ValueError:
        a_index = 999
    try:
        b_index = sorted_categories.index(b[0])
    except ValueError:
        b_index = 999

    if a_index < b_index:
        return -1
    if a_index > b_index:
        return 1
    if a_index == b_index:
        return -1 if a[0] < b[0] else 1


sort_category_key = cmp_to_key(sort_category)

listing = ""
for category, publications in sorted(generated.items(), key=sort_category_key):
    generated_items = [(k, v) for k, v in publications.items() if v]
    publication_listing = []
    for recipe_name, books in sorted(
        generated_items, key=lambda item: item[1][0].published_dt, reverse=True
    ):
        book_links = []
        for book in books:
            # change filename to datestamped name
            if book.file != book.rename_to:
                os.rename(
                    os.path.join(publish_folder, book.file),
                    os.path.join(publish_folder, book.rename_to),
                )
            file_size = os.path.getsize(os.path.join(publish_folder, book.rename_to))
            book_links.append(
                f'<div class="book"><a href="{book.rename_to}">{os.path.splitext(book.file)[1]}<span class="file-size">{humanize.naturalsize(file_size).replace(" ", "")}</span></a></div>'
            )
        publication_listing.append(
            f"""<li>{books[0].title or recipe_name}{" ".join(book_links)}
            <span class="pub-date" data-pub-date="{int(books[0].published_dt.timestamp() * 1000)}">
                Published at {books[0].published_dt:%Y-%m-%d %-I:%M%p %z}
            </span>
            </li>"""
        )
    category_recipes = [r for r in recipes if r.category == category]
    for r in category_recipes:
        success = False
        for recipe_name, _ in generated_items:
            if recipe_name == r.name:
                success = True
                break
        if not success:
            publication_listing.append(
                f"""<li class="not-available">{r.name}
                <span class="pub-date">Not available</span></li>"""
            )

    listing += f"""<li>{category}
    <ol class="books">{"".join(publication_listing)}</ol>
    </li>"""

with open(os.path.join(publish_folder, "index.json"), "w", encoding="utf-8") as f_in:
    index["_generated"] = int(time.time())
    json.dump(index, f_in, indent=0)

elapsed_time = timedelta(seconds=timer() - start_time)

with open("static/index.html", "r", encoding="utf-8") as f_in:
    html_output = f_in.read().format(
        listing=listing,
        css=site_css,
        refreshed_ts=int(time.time() * 1000),
        refreshed_dt=datetime.now(tz=timezone.utc),
        js=site_js,
        publish_site=publish_site,
        elapsed=humanize.naturaldelta(elapsed_time, minimum_unit="seconds"),
        source_link=f'<a href="{source_url}">Source</a>.',
    )
    index_html_file = os.path.join(publish_folder, "index.html")
    with open(index_html_file, "w", encoding="utf-8") as f:
        f.write(html_output)
