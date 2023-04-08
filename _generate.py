# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from collections import namedtuple
from datetime import datetime, timezone, timedelta
from functools import cmp_to_key
from math import ceil
from pathlib import Path
from timeit import default_timer as timer
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlencode
from xml.dom import minidom

import humanize  # type: ignore
import requests  # type: ignore
from bleach import linkify

from _opds import init_feed, simple_tag, extension_contenttype_map
from _recipe_utils import sort_category, Recipe
from _recipes import (
    recipes as default_recipes,
    categories_sort as default_categories_sort,
)
from _recipes_custom import (
    recipes as custom_recipes,
    categories_sort as custom_categories_sort,
)
from _utils import generate_cover, slugify

logger = logging.getLogger(__file__)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

publish_folder = Path("public")
meta_folder = Path("meta")
job_log_filename = "job_log.json"
catalog_path = "catalog.xml"
index_json_filename = "index.json"
default_retry_wait_interval = 2

RecipeOutput = namedtuple(
    "RecipeOutput",
    [
        "recipe",
        "title",
        "file",
        "rename_to",
        "published_dt",
        "description",
    ],
)

# sort categories for display
# Ignoring mypy error below because of https://github.com/python/mypy/issues/9372
sort_category_key = cmp_to_key(  # type: ignore[misc]
    lambda a, b: sort_category(
        a[0], b[0], custom_categories_sort or default_categories_sort  # type: ignore[index]
    )
)


def _get_env_csv(key: str) -> List[str]:
    # get csv format env values
    slugs: List[str] = []
    try:
        slugs = [r.strip() for r in str(os.environ[key]).split(",") if r.strip()]
    except (KeyError, ValueError):
        pass
    return slugs


def _get_env_accounts_info() -> Dict:
    accounts_info = {}
    try:
        json_str = str(os.environ["accounts"])
        if json_str:
            accounts_info = json.loads(json_str)
            if not isinstance(accounts_info, dict):
                logger.error(
                    f"accounts did not deserialize into a dict: {type(accounts_info)}"
                )
                accounts_info = {}
    except KeyError:
        pass
    except json.decoder.JSONDecodeError:
        logger.exception("Unable to parse accounts secret as json.")
    return accounts_info


# fetch index.json from published site
def _fetch_cache(site, cache_sess: requests.Session) -> Dict:
    retry_attempts = 1
    timeout = 15
    for attempt in range(1 + retry_attempts):
        res = cache_sess.get(urljoin(site, index_json_filename), timeout=timeout)
        try:
            res.raise_for_status()
            return res.json()
        except Exception as err:  # noqa, pylint: disable=broad-except
            if attempt < retry_attempts:
                logger.warning(
                    f"{err.__class__.__name__} downloading {index_json_filename}"
                    f"Retrying after {default_retry_wait_interval}s..."
                )
                timeout += 15
                time.sleep(default_retry_wait_interval)
                continue
            logger.exception(f"{err.__class__.__name__} fetching {index_json_filename}")
    return {}


def _add_recipe_summary(
    rec: Recipe, status: str, duration: Optional[timedelta] = None
) -> str:
    duration_str = "0"
    if duration:
        duration_str = humanize.precisedelta(duration)
    return f"| {rec.name} | {status} | {duration_str} |\n"


def _write_opds(generated_output: Dict, recipe_covers: Dict, publish_site: str) -> None:
    """
    Generate minimal OPDS

    :param generated_output:
    :return:
    """
    main_doc = minidom.Document()
    main_feed = init_feed(main_doc, publish_site, "newsrack", "News Rack")

    for category, publications in sorted(
        generated_output.items(), key=sort_category_key
    ):
        cat_doc = minidom.Document()
        cat_feed = init_feed(
            cat_doc, publish_site, "newsrack", f"News Rack - {category.title()}"
        )

        generated_items = [(k, v) for k, v in publications.items() if v]
        for recipe_name, books in sorted(
            generated_items, key=lambda item: item[1][0].published_dt, reverse=True
        ):
            for doc, feed in [(main_doc, main_feed), (cat_doc, cat_feed)]:
                entry = doc.createElement("entry")
                entry.appendChild(
                    simple_tag(
                        doc, "id", books[0].recipe.slug if books else recipe_name
                    )
                )
                entry.appendChild(
                    simple_tag(
                        doc,
                        "title",
                        f"{books[0].title or recipe_name}",
                    )
                )
                entry.appendChild(
                    simple_tag(
                        doc,
                        "summary",
                        f"{books[0].title or recipe_name} published at {books[0].published_dt:%Y-%m-%d %H:%M%p}.",
                    )
                )
                entry.appendChild(
                    simple_tag(
                        doc,
                        "content",
                        f"{books[0].description or recipe_name}",
                        attributes={"type": "text/html"},
                    )
                )
                entry.appendChild(
                    simple_tag(
                        doc,
                        "updated",
                        f"{books[0].published_dt:%Y-%m-%dT%H:%M:%SZ}",
                    )
                )
                entry.appendChild(
                    simple_tag(
                        doc,
                        "category",
                        attributes={"label": category.title()},
                    )
                )
                author_tag = simple_tag(doc, "author")
                author_tag.appendChild(simple_tag(doc, "name", category.title()))
                entry.appendChild(author_tag)

                covers = recipe_covers.get(books[0].recipe.slug)
                if covers:
                    cover_file_name = covers["cover"]
                    cover_file_path = publish_folder.joinpath(cover_file_name)
                    cover_thumbnail_file_name = covers["thumbnail"]
                    cover_thumbnail_file_path = publish_folder.joinpath(
                        cover_thumbnail_file_name
                    )
                    if cover_file_path.exists():
                        entry.appendChild(
                            simple_tag(
                                doc,
                                "link",
                                attributes={
                                    "rel": "http://opds-spec.org/image",
                                    "type": "image/jpeg",
                                    "href": cover_file_name,
                                },
                            )
                        )
                    if cover_thumbnail_file_path.exists():
                        entry.appendChild(
                            simple_tag(
                                doc,
                                "link",
                                attributes={
                                    "rel": "http://opds-spec.org/image/thumbnail",
                                    "type": "image/jpeg",
                                    "href": cover_thumbnail_file_name,
                                },
                            )
                        )

                for book in books:
                    book_ext = Path(book.file).suffix
                    link_type = (
                        extension_contenttype_map.get(book_ext)
                        or "application/octet-stream"
                    )
                    entry.appendChild(
                        simple_tag(
                            doc,
                            "link",
                            attributes={
                                "rel": "http://opds-spec.org/acquisition",
                                "type": link_type,
                                "href": f"{Path(book.rename_to).name}",
                            },
                        )
                    )
                feed.appendChild(entry)

        opds_xml_path = publish_folder.joinpath(f"{slugify(category, True)}.xml")
        with opds_xml_path.open("wb") as f:  # type: ignore
            f.write(cat_doc.toprettyxml(encoding="utf-8", indent=""))

    opds_xml_path = publish_folder.joinpath(catalog_path)
    with opds_xml_path.open("wb") as f:  # type: ignore
        f.write(main_doc.toprettyxml(encoding="utf-8", indent=""))


def _find_output(folder_path: Path, slug: str, ext: str) -> List[Path]:
    """
    This is an improvement over using just glob because it finds outputs
    more precisely by the exact slug.
    Previously, if 2 recipes have similar slugs, e.g. "wsj" vs "wsj-print",
    using glob will result in the wrong outputs being detected.
    """
    slug_match_re = re.compile(slug + r"(-\d{4}-\d{2}-\d{2})?\." + ext)
    res = folder_path.glob(f"{slug}*.{ext}")
    return [r for r in res if slug_match_re.match(r.name)]


def _download_from_cache(
    recipe: Recipe, cached: Dict, publish_site: str, cache_sess: requests.Session
) -> bool:
    """
    Download a recipe output from the published site
    :param recipe:
    :param cached:
    :param publish_site:
    :param cache_sess:
    :return:
    """
    abort = False
    # [TODO] changed from using name to slug, check name to keep backward compat
    cached_files = cached.get(recipe.slug, []) or cached.get(recipe.name, [])
    for cached_item in cached_files:
        ext = Path(cached_item["filename"]).suffix
        if ext != f".{recipe.src_ext}" and ext not in [
            f".{x}" for x in recipe.target_ext
        ]:
            continue

        ebook_url = urljoin(publish_site, cached_item["filename"])
        try:
            # see if this fixes the ReadTimeout for large files, e.g. WSJ-print
            cache_sess.head(ebook_url, timeout=5)
        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.HTTPError,  # it happens
            requests.exceptions.ConnectionError,  # e.g. Connection aborted.
        ) as head_err:  # noqa
            logger.warning(
                f"{head_err.__class__.__name__} sending HEAD request for {ebook_url}"
            )
            time.sleep(default_retry_wait_interval)

        timeout = 30
        for attempt in range(1 + recipe.retry_attempts):
            try:
                logger.debug(f'Downloading "{ebook_url}"...')
                ebook_res = cache_sess.get(ebook_url, timeout=timeout, stream=True)
                ebook_res.raise_for_status()
                with publish_folder.joinpath(cached_item["filename"]).open("wb") as f:
                    shutil.copyfileobj(ebook_res.raw, f)
                abort = False
                break
            except (
                requests.exceptions.ReadTimeout,
                requests.exceptions.HTTPError,  # it happens
                requests.exceptions.ConnectionError,  # e.g. Connection aborted.
            ) as err:
                if attempt < recipe.retry_attempts:
                    logger.warning(
                        f"{err.__class__.__name__} downloading {ebook_url}. "
                        f"Retrying after {default_retry_wait_interval}s..."
                    )
                    timeout += 30
                    time.sleep(default_retry_wait_interval)
                    continue
                logger.error(f"[!] {err.__class__.__name__} for {ebook_url}")
                abort = True
                if ext == f".{recipe.src_ext}":
                    # if primary format, abort early
                    return abort
    return abort


def _linkify_attrs(attrs, _=False):
    """
    Add required attributes when linkifying
    :param attrs:
    :param new:
    :return:
    """
    attrs[(None, "rel")] = "noreferrer nofollow noopener"
    attrs[(None, "target")] = "_blank"
    return attrs


def run(
    publish_site: str, source_url: str, commit_hash: str, verbose_mode: bool
) -> None:
    # set path to recipe includes in os environ so that recipes can pick it up
    os.environ["recipes_includes"] = str(Path("recipes/includes/").absolute())

    # for GitHub
    job_summary = """| Recipe | Status | Duration |
| ------ | ------ | -------- |
"""
    if not publish_site.endswith("/"):
        publish_site += "/"

    job_log: Dict[str, float] = {}
    try:
        with meta_folder.joinpath(job_log_filename).open("r", encoding="utf-8") as f:
            job_log = json.load(f)
    except Exception as err:  # noqa, pylint: disable=broad-except
        logger.warning(f"Unable to load job log: {err}")

    today = datetime.utcnow().replace(tzinfo=timezone.utc)
    cache_sess = requests.Session()
    cached = _fetch_cache(publish_site, cache_sess)
    index = {}  # type: ignore
    recipe_descriptions = {}
    recipe_covers = {}
    generated: Dict[str, Dict[str, List[RecipeOutput]]] = {}

    # skip specified recipes in CI
    skip_recipes_slugs: List[str] = _get_env_csv("skip")
    # run specified recipes in CI
    regenerate_recipes_slugs: List[str] = _get_env_csv("regenerate")

    start_time = timer()

    accounts_info = _get_env_accounts_info()

    recipes: List[Recipe] = custom_recipes or default_recipes
    for recipe in recipes:
        recipe_path = Path(f"{recipe.recipe}.recipe")
        if not recipe.name:
            try:
                with recipe_path.open("r", encoding="utf-8") as f:
                    recipe_source = f.read()
                    mobj = re.search(
                        r"\n_name\s=\s['\"](?P<name>.+)['\"]\n", recipe_source
                    ) or re.search(
                        r"\btitle\s+=\s+u?['\"](?P<name>.+)['\"]\n", recipe_source
                    )
                    if mobj:
                        recipe.name = mobj.group("name")
                    else:
                        logger.warning(f"Unable to extract recipe name for {recipe}.")
                        recipe.name = (
                            f"{recipe.recipe}.recipe"  # set name to recipe file name
                        )
            except FileNotFoundError:
                logger.warning(
                    f"Built-in recipes should be configured with a recipe name: {recipe.recipe}"
                )
                recipe.name = f"{recipe.recipe}.recipe"
            except Exception:  # noqa, pylint: disable=broad-except
                logger.exception("Error getting recipe name")
                continue

        if recipe_path.exists():
            os.environ["newsrack_title_dt_format"] = recipe.title_date_format

        job_status = ""
        recipe.last_run = job_log.get(recipe.slug, 0)
        logger.info(f"::group::{recipe.name}")

        if recipe.slug in skip_recipes_slugs:
            logger.info(f'[!] SKIPPED recipe: "{recipe.slug}"')
            logger.info("::endgroup::")
            job_summary += _add_recipe_summary(recipe, ":arrow_right_hook: Skipped")
            continue

        logger.info(f'{"-" * 20} Executing "{recipe.name}" recipe... {"-" * 30}')
        recipe_start_time = timer()

        if recipe.category not in generated:
            generated[recipe.category] = {}
        generated[recipe.category][recipe.name] = []
        index[recipe.slug] = []

        source_file_name = Path(f"{recipe.slug}.{recipe.src_ext}")
        source_file_path = publish_folder.joinpath(source_file_name)
        cmd = [
            "ebook-convert",
            str(recipe_path),
            str(source_file_path),
        ]
        try:
            recipe_account = accounts_info.get(recipe.slug, {})
            recipe_username = recipe_account.get("username", None)
            recipe_password = recipe_account.get("password", None)
            if recipe_username and recipe_password:
                cmd.extend(
                    [f"--username={recipe_username}", f"--password={recipe_password}"]
                )
        except:  # noqa, pylint: disable=bare-except
            pass
        if recipe.conv_options and recipe.conv_options.get(recipe.src_ext):
            cmd.extend(recipe.conv_options[recipe.src_ext])
        customised_css_filename = Path("static", f"{recipe.src_ext}.css")
        if customised_css_filename.exists():
            cmd.append(f"--extra-css={str(customised_css_filename)}")
        if verbose_mode:
            cmd.append("-vv")

        exit_code = 0

        # set recipe debug output folder
        if verbose_mode:
            os.environ["recipe_debug_folder"] = str(publish_folder.absolute())

        # [TODO] changed from using name to slug, check name to keep backward compat
        cached_files = cached.get(recipe.slug, []) or cached.get(recipe.name, [])

        if not _find_output(publish_folder, recipe.slug, recipe.src_ext):
            # existing file does not exist
            try:
                if (
                    # regenerate restriction is not in place and recipe is enabled
                    (recipe.is_enabled() and not regenerate_recipes_slugs)
                    # regenerate restriction is in place and recipe is included
                    or (
                        regenerate_recipes_slugs
                        and recipe.slug in regenerate_recipes_slugs
                    )
                    # not cached (so that we always have a copy available)
                    or not cached_files
                ):
                    original_recipe_timeout = recipe.timeout
                    for attempt in range(recipe.retry_attempts + 1):
                        try:
                            # run recipe
                            exit_code = subprocess.call(
                                cmd,
                                timeout=recipe.timeout,
                                stdout=sys.stdout,
                                stderr=sys.stderr,
                            )
                            break
                        except subprocess.TimeoutExpired:
                            if attempt < recipe.retry_attempts:
                                recipe_elapsed_time = timedelta(
                                    seconds=timer() - recipe_start_time
                                )
                                wait_interval = ceil(recipe.timeout / 100)
                                logger.warning(
                                    f"TimeoutExpired fetching '{recipe.name}' "
                                    f"after {humanize.precisedelta(recipe_elapsed_time)}. "
                                    f"Retrying after {wait_interval}s..."
                                )
                                # increase recipe timeout by 10% on retry but up to a max of 20min
                                recipe.timeout = max(int(1.1 * recipe.timeout), 20 * 60)
                                time.sleep(max(min(wait_interval, 2), 10))
                                continue
                            raise
                        finally:
                            # it's not used anymore, but restore original timeout
                            # value just in case
                            recipe.timeout = original_recipe_timeout

                    job_log[recipe.slug] = time.time()

                else:
                    # use cache
                    logger.warning(f'Using cached copy for "{recipe.name}".')
                    abort_recipe = _download_from_cache(
                        recipe, cached, publish_site, cache_sess
                    )
                    if not abort_recipe:
                        job_status = ":outbox_tray: From cache"
                    else:
                        recipe_elapsed_time = timedelta(
                            seconds=timer() - recipe_start_time
                        )
                        logger.info(
                            f'{"=" * 10} "{recipe.name}" recipe took {humanize.precisedelta(recipe_elapsed_time)} {"=" * 20}'
                        )
                        logger.info("::endgroup::")
                        job_summary += _add_recipe_summary(
                            recipe, ":x: Cache Timeout", recipe_elapsed_time
                        )
                        continue

            except subprocess.TimeoutExpired:
                logger.exception(f"[!] TimeoutExpired fetching '{recipe.name}'")
                recipe_elapsed_time = timedelta(seconds=timer() - recipe_start_time)
                logger.info(
                    f'{"=" * 10} "{recipe.name}" recipe took {humanize.precisedelta(recipe_elapsed_time)} {"=" * 20}'
                )
                logger.info("::endgroup::")
                job_summary += _add_recipe_summary(
                    recipe, ":x: Convert Timeout", recipe_elapsed_time
                )
                continue
        else:
            job_status = ":file_folder: From local"

        # unset debug folder
        if os.environ.get("recipe_debug_folder", ""):
            del os.environ["recipe_debug_folder"]

        source_file_paths = sorted(
            _find_output(publish_folder, recipe.slug, recipe.src_ext)
        )
        if cached_files and not source_file_paths:
            logger.warning(
                f'Using cached copy for "{recipe.name}" because recipe has no output.'
            )
            # try to use cached copy if recipe does not have output
            # for example FT(Print) has no weekend issue, so we'll try to keep the last issue
            _ = _download_from_cache(recipe, cached, publish_site, cache_sess)
            source_file_paths = sorted(
                _find_output(publish_folder, recipe.slug, recipe.src_ext)
            )
            if source_file_paths:
                exit_code = (
                    0  # reset exit_code (not 0 because of failed recipe ebook-convert)
                )
                job_status = ":outbox_tray: From cache"

        if not source_file_paths:
            logger.error(
                f"Unable to find source generated: '/{recipe.slug}*.{recipe.src_ext}'"
            )
            recipe_elapsed_time = timedelta(seconds=timer() - recipe_start_time)
            logger.info(
                f'{"=" * 20} "{recipe.name}" recipe took {humanize.precisedelta(recipe_elapsed_time)} {"=" * 20}'
            )
            logger.info("::endgroup::")
            job_summary += _add_recipe_summary(
                recipe, ":x: No output", recipe_elapsed_time
            )
            continue

        source_file_path = source_file_paths[-1]
        source_file_name = Path(source_file_path.name)
        if not exit_code:
            logger.debug(f'Get book meta info for "{source_file_path}"')
            proc = subprocess.Popen(
                ["ebook-meta", str(source_file_path)], stdout=subprocess.PIPE
            )
            meta_out = proc.stdout.read().decode("utf-8")  # type: ignore
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
            rename_file_name = Path(
                f"{recipe.slug}-{pub_date:%Y-%m-%d}.{recipe.src_ext}"
            )

            comments = []
            description = ""
            mobj = re.search(r"Comments\s+:\s(?P<comments>.+)", meta_out, re.DOTALL)
            if mobj:
                try:
                    comments = [
                        c.strip()
                        for c in mobj.group("comments").split("\n")
                        if c.strip()
                    ]
                    description = (
                        f"{comments[0]}"
                        f'<ul><li>{"</li><li>".join(comments[1:-1])}</li></ul>'
                        f"{linkify(comments[-1], callbacks=[_linkify_attrs])}"
                    )
                except:  # noqa, pylint: disable=bare-except
                    pass

            generated[recipe.category][recipe.name].append(
                RecipeOutput(
                    recipe=recipe,
                    title=title,
                    file=source_file_name,
                    rename_to=rename_file_name,
                    published_dt=pub_date,
                    description=description,
                )
            )

            pseudo_series_index = pub_date.year * 1000 + pub_date.timetuple().tm_yday
            # (rename_file_name != source_file_name) checks that it is a newly generated file
            # so that we don't regenerate the cover needlessly
            if (
                recipe.overwrite_cover
                and title
                and rename_file_name != source_file_name
            ):
                # customise cover
                logger.debug(f'Setting cover for "{source_file_path}"')
                try:
                    cover_file_path = Path(f"{str(source_file_path)}.png")
                    generate_cover(
                        cover_file_path, title, recipe.cover_options, logger=logger
                    )
                    cover_cmd = [
                        "ebook-meta",
                        str(source_file_path),
                        f"--cover={str(cover_file_path)}",
                        f"--series={recipe.name}",
                        f"--index={pseudo_series_index}",
                        f"--publisher={publish_site}",
                    ]
                    _ = subprocess.call(cover_cmd, stdout=subprocess.PIPE)
                    cover_file_path.unlink()
                except Exception:  # noqa, pylint: disable=broad-except
                    logger.exception("Error generating cover")
            elif rename_file_name != source_file_name:
                # just set series name
                series_cmd = [
                    "ebook-meta",
                    str(source_file_path),
                    f"--series={recipe.name}",
                    f"--index={pseudo_series_index}",
                    f"--publisher={publish_site}",
                ]
                _ = subprocess.call(series_cmd, stdout=subprocess.PIPE)

            index[recipe.slug].append(
                {
                    "filename": f"{recipe.slug}-{pub_date:%Y-%m-%d}.{recipe.src_ext}",
                    "published": pub_date.timestamp(),
                }
            )

            # convert generate book into alternative formats
            for ext in recipe.target_ext:
                target_file_name = Path(f"{recipe.slug}.{ext}")
                target_file_path = Path(publish_folder, target_file_name)

                cmd = [
                    "ebook-convert",
                    str(source_file_path),
                    str(target_file_path),
                    f"--series={recipe.name}",
                    f"--series-index={pseudo_series_index}",
                    f"--publisher={publish_site}",
                ]
                if recipe.conv_options and recipe.conv_options.get(ext):
                    cmd.extend(recipe.conv_options[ext])

                customised_css_filename = Path("static", f"{ext}.css")
                if customised_css_filename.exists():
                    cmd.append(f"--extra-css={str(customised_css_filename)}")
                if verbose_mode:
                    cmd.append("-vv")
                if not _find_output(publish_folder, recipe.slug, ext):
                    exit_code = subprocess.call(
                        cmd,
                        timeout=recipe.timeout,
                        stdout=sys.stdout,
                        stderr=sys.stderr,
                    )
                target_file_path = sorted(
                    _find_output(publish_folder, recipe.slug, ext)
                )[-1]
                target_file_name = Path(target_file_path.name)

                if not exit_code:
                    generated[recipe.category][recipe.name].append(
                        RecipeOutput(
                            recipe=recipe,
                            title=title,
                            file=target_file_name,
                            rename_to=f"{recipe.slug}-{pub_date:%Y-%m-%d}.{ext}",
                            published_dt=pub_date,
                            description=comments,
                        )
                    )
                    index[recipe.slug].append(
                        {
                            "filename": f"{recipe.slug}-{pub_date:%Y-%m-%d}.{ext}",
                            "published": pub_date.timestamp(),
                        }
                    )

            recipe_elapsed_time = timedelta(seconds=timer() - recipe_start_time)
            logger.info(
                f'{"=" * 20} "{recipe.name}" recipe took {humanize.precisedelta(recipe_elapsed_time)} {"=" * 20}'
            )
            logger.info("::endgroup::")
            job_summary += _add_recipe_summary(
                recipe,
                job_status or ":white_check_mark: Completed",
                recipe_elapsed_time,
            )

    static_assets_start_time = timer()
    # generate index.html
    listing = ""
    for _, (category, publications) in enumerate(
        sorted(generated.items(), key=sort_category_key)
    ):
        generated_items = [(k, v) for k, v in publications.items() if v]
        publication_listing = []
        for recipe_name, books in sorted(
            generated_items, key=lambda item: item[1][0].published_dt, reverse=True
        ):
            book_links = []
            for book in books:
                # change filename to datestamped name
                book_file = publish_folder.joinpath(book.file)
                book_rename_to = publish_folder.joinpath(book.rename_to)
                if book.file != book.rename_to:
                    book_file.rename(book_rename_to)
                cover_file_name = Path(f"{book_rename_to.stem}.jpg")
                cover_file_path = publish_folder.joinpath(cover_file_name)
                cover_thumbnail_file_name = Path(f"{book_rename_to.stem}.thumb.jpg")
                cover_thumbnail_file_path = publish_folder.joinpath(
                    cover_thumbnail_file_name
                )
                if (not book.recipe.overwrite_cover) and (not cover_file_path.exists()):
                    # only extract default cover not generated by newsrack
                    cover_get_cmd = [
                        "ebook-meta",
                        f"--get-cover={str(cover_file_path)}",
                        str(book_rename_to),
                    ]
                    try:
                        _ = subprocess.call(cover_get_cmd, stdout=subprocess.PIPE)
                        temp_cover_file_name = Path(f"{book_rename_to.stem}.temp.jpg")
                        temp_cover_file_path = publish_folder.joinpath(
                            temp_cover_file_name
                        )
                        imagemagick_cmd = [
                            "convert",
                            str(cover_file_path),
                            "-quality",
                            "70",
                            "-resize",
                            "1024x1024>",
                            "-unsharp",
                            "0x.5",
                            "-strip",
                            str(temp_cover_file_path),
                        ]
                        exit_code = subprocess.call(imagemagick_cmd)
                        if exit_code:
                            logger.warning(
                                "convert exited with the code: {0!s}".format(exit_code)
                            )
                        else:
                            temp_cover_file_path.rename(cover_file_path)
                        imagemagick_cmd = [
                            "convert",
                            str(cover_file_path),
                            "-quality",
                            "80",
                            "-thumbnail",
                            "500x500>",
                            "-unsharp",
                            "0x.5",
                            str(cover_thumbnail_file_path),
                        ]
                        exit_code = subprocess.call(imagemagick_cmd)
                        if exit_code:
                            logger.warning(
                                "convert (thumbnail) exited with the code: {0!s}".format(
                                    exit_code
                                )
                            )
                    except (
                        Exception  # noqa, pylint: disable=broad-except
                    ) as get_cover_err:
                        logger.warning(
                            "Unable to extract cover for %s: %s",
                            book.rename_to,
                            str(get_cover_err),
                        )
                if (not book.recipe.overwrite_cover) and cover_file_path.exists():
                    recipe_covers[book.recipe.slug] = {
                        "cover": str(cover_file_name),
                        "thumbnail": str(cover_thumbnail_file_name),
                    }

                file_size = book_rename_to.stat().st_size
                book_ext = book_file.suffix
                reader_link = ""
                if book_ext == ".epub":
                    reader_link = f'<a class="reader not-for-kindle" title="Read in browser" href="reader.html?{urlencode({"file": book.rename_to})}"><svg><use href="reader_sprites.svg#icon-book"></use></svg></a>'
                book_links.append(
                    f'<div class="book">'
                    f'<a href="{book.rename_to}">{book_ext}<span class="file-size">{humanize.naturalsize(file_size).replace(" ", "")}</span>'
                    f"</a>{reader_link}"
                    f"</div>"
                )
            publication_listing.append(
                f"""
            <li id="{books[0].recipe.slug}" data-cat-id="cat-{slugify(category, True)}" data-cat-name="{category}"
                    data-tags="{"" if not books[0].recipe.tags else "#" + " #".join(books[0].recipe.tags)}">
            <span class="title">{books[0].title or recipe_name}</span>
            {" ".join(book_links)}
            <div class="pub-date" data-pub-date="{int(books[0].published_dt.timestamp() * 1000)}">
                Published at {books[0].published_dt:%Y-%m-%d %-I:%M%p %z}
                {"" if not books[0].recipe.tags else '<span class="tags">#' + " #".join(books[0].recipe.tags) + "</span>"}
            </div>
            <div class="contents hide"></div>
            </li>"""
            )
            recipe_descriptions[books[0].recipe.slug] = books[0].description

        # display recipes without output
        generated_recipe_names = [recipe_name for recipe_name, _ in generated_items]
        unsuccessful_category_recipes = [
            r
            for r in recipes
            if r.category == category
            and r.name
            and r.name not in generated_recipe_names
        ]
        for r in unsuccessful_category_recipes:
            publication_listing.append(
                f"""<li id="{r.slug}" data-cat-id="cat-{slugify(r.category, True)}" data-cat-name="{r.category}" class="not-available" data-tags="{"" if not r.tags else "#" + " #".join(r.tags)}">
                <span class="title">{r.name}</span>
                <div class="pub-date">Not available
                    <span class="tags">{"" if not r.tags else "#" + " #".join(r.tags)}</span>
                </div></li>"""
            )

        listing += f"""<div class="category-container is-open"><h2 id="cat-{slugify(category, True)}" class="category is-open">{category}
        <a class="opds" title="OPDS for {category.title()}" href="{slugify(category, True)}.xml">OPDS</a></h2>
        <ol class="books">{"".join(publication_listing)}</ol>
        <div class="close-cat-container"><div class="close-cat-shortcut" data-click-target="cat-{slugify(category)}"></div></div>
        </div>
        """

    with publish_folder.joinpath(index_json_filename).open(
        "w", encoding="utf-8"
    ) as f_in:
        index["_generated"] = int(time.time())
        json.dump(index, f_in, indent=0)

    elapsed_time = timedelta(seconds=timer() - start_time)

    if not meta_folder.exists():
        meta_folder.mkdir(parents=True, exist_ok=True)
    with meta_folder.joinpath(job_log_filename).open("w", encoding="utf-8") as f:
        json.dump(job_log, f, indent=0)

    site_css = "static/site.css"
    if os.path.exists("static/custom.css"):
        site_css = "static/custom.css"
    site_js = "static/site.compiled.js"
    if os.path.exists("static/custom.js"):
        site_js = "static/custom.js"
    site_html = "static/index.html"
    if os.path.exists("static/custom.html"):
        site_html = "static/custom.html"

    with (
        open(site_css, "r", encoding="utf-8") as f_site_css,
        open(site_js, "r", encoding="utf-8") as f_site_js,
        open(site_html, "r", encoding="utf-8") as f_in,
        Path(publish_folder, "index.html").open("w", encoding="utf-8") as f_out,
    ):
        site_js = f"var RECIPE_DESCRIPTIONS = {json.dumps(recipe_descriptions)};"
        site_js += f"var RECIPE_COVERS = {json.dumps(recipe_covers)};"
        site_js += f_site_js.read()
        html_output = f_in.read().format(
            listing=listing,
            css=f_site_css.read(),
            refreshed_ts=int(time.time() * 1000),
            refreshed_dt=datetime.now(tz=timezone.utc),
            js=site_js,
            publish_site=publish_site,
            elapsed=humanize.naturaldelta(elapsed_time, minimum_unit="seconds"),
            catalog=catalog_path,
            source_link=f'<a class="git" href="{source_url}">{commit_hash[0:7]}</a>',
        )
        f_out.write(html_output)

    # Generate reader html
    reader_js = "static/reader.compiled.js"
    if os.path.exists("static/reader_custom.js"):
        reader_js = "static/reader_custom.js"
    with (
        open(reader_js, "r", encoding="utf-8") as f_reader_js,
        open("static/reader.css", "r", encoding="utf-8") as f_reader_css,
        open("static/reader.html", "r", encoding="utf-8") as f_in,
        open(
            os.path.join(publish_folder, "reader.html"), "w", encoding="utf-8"
        ) as f_out,
    ):
        html_output = f_in.read().format(css=f_reader_css.read(), js=f_reader_js.read())
        f_out.write(html_output)

    _write_opds(generated, recipe_covers, publish_site)

    static_assets_elapsed_time = timedelta(seconds=timer() - static_assets_start_time)

    job_summary += f'\nStatic assets took {humanize.naturaldelta(static_assets_elapsed_time, minimum_unit="seconds")}.\n'

    with open("job_summary.md", "w", encoding="utf-8") as f:
        f.write(job_summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("publish_site", type=str, help="Deployment site url")
    parser.add_argument("repo_url", type=str, help="Source repo url")
    parser.add_argument("commit_hash", type=str, help="Commit hash")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Enable more verbose messages for debugging",
    )
    args = parser.parse_args()

    try:
        verbose = str(os.environ["verbose"]).strip().lower() == "true"
    except (KeyError, ValueError):
        verbose = False

    verbose = verbose or args.verbose
    if verbose:
        logger.setLevel(logging.DEBUG)

    run(args.publish_site, args.repo_url, args.commit_hash, verbose)
