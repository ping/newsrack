# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Union, Callable, Dict

default_recipe_timeout = 180

# format-specific ebook-convert options
default_conv_options: Dict[str, List[str]] = {
    "mobi": ["--output-profile=kindle_oasis", "--mobi-file-type=both"],
    "pdf": ["--pdf-page-numbers"],
    "epub": ["--output-profile=tablet"],
}


@dataclass
class CoverOptions:
    """Cover options"""

    cover_width: int = 889
    cover_height: int = 1186
    text_colour: str = "black"
    background_colour: str = "white"
    title_font_path: str = "static/OpenSans-Bold.ttf"
    title_font_size: int = 80
    datestamp_font_path: str = "static/OpenSans-Bold.ttf"
    datestamp_font_size: int = 72


@dataclass
class Recipe:
    """A Calibre recipe definition"""

    recipe: str  # actual recipe name
    slug: str  # file name slug
    src_ext: str  # recipe output format
    category: str  # category, e.g. News
    name: str = ""  # display name, taken from recipe source by default
    target_ext: List[str] = field(
        default_factory=list
    )  # alt formats that src_ext will be converted to
    timeout: int = default_recipe_timeout  # max time allowed for executing the recipe
    overwrite_cover: bool = True  # generate a plain cover to overwrite Calibre's
    enable_on: Union[
        bool, Callable[..., bool]
    ] = True  # determines when to run the recipe
    retry_attempts: int = (
        1  # number of attempts to retry on TimeoutExpired, ReadTimeout
    )
    conv_options: Dict[str, List[str]] = field(
        default_factory=lambda: default_conv_options, init=False
    )  # conversion options for specific formats
    cover_options: CoverOptions = (
        CoverOptions()
    )  # customise script-generated cover, used when overwrite_cover=True
    tags: List[str] = field(default_factory=list)  # used in search

    def is_enabled(self) -> bool:
        if callable(self.enable_on):
            return self.enable_on()
        return self.enable_on


def sort_category(a, b, categories_sort):
    try:
        a_index = categories_sort.index(a[0])
    except ValueError:
        a_index = 999
    try:
        b_index = categories_sort.index(b[0])
    except ValueError:
        b_index = 999

    if a_index < b_index:
        return -1
    if a_index > b_index:
        return 1
    if a_index == b_index:
        return -1 if a[0] < b[0] else 1


def get_local_now(offset: float = 0.0):
    return (
        datetime.utcnow()
        .replace(tzinfo=timezone.utc)
        .astimezone(timezone(offset=timedelta(hours=offset)))
    )


def onlyon_weekdays(days_of_the_week: List[int], offset: float = 0.0):
    """
    Enable recipe only on the specified days_of_the_week

    :param days_of_the_week: Starts with 0 = Monday
    :param offset: timezone offset hours
    :return:
    """
    return get_local_now(offset).weekday() in days_of_the_week


def onlyon_days(days_of_the_month: List[int], offset: float = 0.0):
    """
    Enable recipe only on the specified days_of_the_month

    :param days_of_the_month:
    :param offset: timezone offset hours
    :return:
    """
    return get_local_now(offset).day in days_of_the_month


def onlyat_hours(hours_of_the_day: List[int], offset: float = 0.0):
    """
    Enable recipe only at the specified hours_of_the_day

    :param hours_of_the_day:
    :param offset: timezone offset hours
    :return:
    """
    return get_local_now(offset).hour in hours_of_the_day
