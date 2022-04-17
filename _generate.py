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
from urllib.parse import urljoin
import shutil
from timeit import default_timer as timer

import requests
import humanize

logger = logging.getLogger(__file__)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.INFO)


start_time = timer()
publish_folder = "public"
publish_site = "https://ping.github.io/newsrack/"
default_recipe_timeout = 120

Receipe = namedtuple(
    "Recipe", ["recipe", "name", "slug", "src_ext", "target_ext", "timeout"]
)
ReceipeOutput = namedtuple(
    "ReceipeOutput", ["title", "file", "rename_to", "published_dt"]
)

# default style
with open("static/site.css", "r", encoding="utf-8") as f:
    site_css = f.read()

# default style
with open("static/site.js", "r", encoding="utf-8") as f:
    site_js = f.read()

# the azw3 formats don't open well in the kindle (stuck, cannot return to library)
recipes = [
    Receipe(
        recipe="nytimes-global",
        name="NY Times Global",
        slug="nytimes-global",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
    Receipe(
        recipe="wapo",
        name="The Washington Post",
        slug="wapo",
        src_ext="mobi",
        target_ext=[],
        timeout=600,
    ),
    Receipe(
        recipe="guardian",
        name="The Guardian",
        slug="guardian",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
    Receipe(
        recipe="ft",
        name="Financial Times",
        slug="ft",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
    Receipe(
        recipe="politico-magazine",
        name="POLITICO Magazine",
        slug="politico-magazine",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
    Receipe(
        recipe="economist",
        name="The Economist",
        slug="economist",
        src_ext="mobi",
        target_ext=[],
        timeout=300,
    ),
    Receipe(
        recipe="joongangdaily",
        name="Joongang Daily",
        slug="joongang-daily",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
    Receipe(
        recipe="scmp",
        name="South China Morning Post",
        slug="scmp",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
    Receipe(
        recipe="thediplomat",
        name="The Diplomat",
        slug="the-diplomat",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
    Receipe(
        recipe="channelnewsasia",
        name="ChannelNewsAsia",
        slug="channelnewsasia",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
    Receipe(
        recipe="fivebooks",
        name="Five Books",
        slug="fivebooks",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
    Receipe(
        recipe="nytimes-books",
        name="New York Times Books",
        slug="nytimes-books",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
]

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


# format file size in human readable format
def human_readable_size(size, decimal_places=2):
    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]:
        if size < 1024.0 or unit == "PiB":
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f}{unit}"


generated = {}
today = datetime.utcnow()
index = {}  # generate index.json
cached = fetch_cache()
cache_sess = requests.Session()

for recipe in recipes:
    if recipe.slug in skip_recipes_slugs:
        logger.info(f'[!] SKIPPED recipe: "{recipe.slug}"')
        continue

    logger.info(f'{"-" * 20} Executing "{recipe.name}" recipe... {"-" * 30}')
    recipe_start_time = timer()

    generated[recipe.name] = []
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
        try:
            # existing file does not exist
            if not regenerate_recipes_slugs:
                exit_code = subprocess.call(
                    cmd,
                    timeout=recipe.timeout,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )
            elif regenerate_recipes_slugs and recipe.slug in regenerate_recipes_slugs:
                # regenerate restriction in place, so we only regenerate the ones specified
                exit_code = subprocess.call(
                    cmd,
                    timeout=recipe.timeout,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )
            else:
                # regeneration restriction in place and this recipe is not in the list
                # we will try to fetch an existing copy
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
                    # not cached, so generate anyway
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
        generated[recipe.name].append(
            ReceipeOutput(
                title=title,
                file=source_file_name,
                rename_to=f"{recipe.slug}-{pub_date:%Y-%m-%d}.{recipe.src_ext}",
                published_dt=pub_date,
            )
        )
        index[recipe.name].append(f"{recipe.slug}-{pub_date:%Y-%m-%d}.{recipe.src_ext}")

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
                generated[recipe.name].append(
                    ReceipeOutput(
                        title=title,
                        file=target_file_name,
                        rename_to=f"{recipe.slug}-{pub_date:%Y-%m-%d}.{ext}",
                        published_dt=pub_date,
                    )
                )
                index[recipe.name].append(f"{recipe.slug}-{pub_date:%Y-%m-%d}.{ext}")

        recipe_elapsed_time = timedelta(seconds=timer() - recipe_start_time)
        logger.info(
            f'{"=" * 20} "{recipe.name}" recipe took {humanize.precisedelta(recipe_elapsed_time)} {"=" * 20}'
        )

listing = ""
generated_items = [(k, v) for k, v in generated.items() if v]
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
            f'<div class="book"><a href="{book.rename_to}">{os.path.splitext(book.file)[1]}<span class="file-size">{human_readable_size(file_size, decimal_places=1)}</span></a></div>'
        )

    listing += f"""<li>
    {books[0].title or recipe_name}
    {" ".join(book_links)}
    <span class="pub-date" data-pub-date="{int(books[0].published_dt.timestamp() * 1000)}">
        Published at {books[0].published_dt:%Y-%m-%d %-I:%M%p %z}
    </span>
    </li>"""

for r in recipes:
    success = False
    for recipe_name, _ in generated_items:
        if recipe_name == r.name:
            success = True
            break
    if not success:
        listing += f"""<li class="not-available">{r.name}
            <span class="pub-date">Not available</span></li>"""

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
    )
    index_html_file = os.path.join(publish_folder, "index.html")
    with open(index_html_file, "w", encoding="utf-8") as f:
        f.write(html_output)
