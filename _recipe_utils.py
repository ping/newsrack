# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0
import sys
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Union

# adapted from calibre.constants.iswindows
_plat = sys.platform.lower()
is_windows = "win32" in _plat or "win64" in _plat
default_recipe_timeout = 180

# format-specific ebook-convert options
default_conv_options: Dict[str, List[str]] = {
    "mobi": ["--output-profile=kindle_oasis", "--mobi-file-type=both"],
    "pdf": ["--pdf-page-numbers"],
    "epub": [
        "--output-profile=tablet",
        # to fix the problem of images having a fixed height after conversion
        "--extra-css=img{height:auto !important;}",
        # to fix the problem of some font sizes being too small
        "--font-size-mapping=10,12,14,16,18,20,22,24",
    ],
}


@dataclass
class CoverOptions:
    """Cover options"""

    cover_width: int = 889
    cover_height: int = 1186
    border_offset: int = 25
    border_width: int = 2
    text_colour: str = "black"
    background_colour: str = "white"
    title_font_path: str = "static/OpenSans-Bold.ttf"
    title_font_size: int = 80
    datestamp_font_path: str = "static/OpenSans-Semibold.ttf"
    datestamp_font_size: int = 72
    logo_path_or_url: str = ""  # must be a png/jpg/gif


@dataclass
class Recipe:
    """A calibre recipe definition"""

    recipe: str  # actual recipe name
    slug: str  # file name slug
    src_ext: str  # recipe output format
    category: str  # category, e.g. News
    name: str = ""  # display name, taken from recipe source by default
    target_ext: List[str] = field(
        default_factory=list
    )  # alt formats that src_ext will be converted to
    timeout: int = default_recipe_timeout  # max time allowed for executing the recipe
    overwrite_cover: bool = True  # generate a plain cover to overwrite calibre's
    last_run: float = 0  # last run unix timestamp
    enable_on: Union[
        bool, Callable[..., bool]
    ] = True  # determines when to run the recipe
    retry_attempts: int = (
        1  # number of attempts to retry on TimeoutExpired, ReadTimeout
    )
    conv_options: Dict[str, List[str]] = field(
        default_factory=lambda: default_conv_options
    )  # conversion options for specific formats
    cover_options: CoverOptions = (
        CoverOptions()
    )  # customise script-generated cover, used when overwrite_cover=True
    tags: List[str] = field(default_factory=list)  # used in search
    title_date_format: str = (
        "%d %b, %Y" if is_windows else "%-d %b, %Y"
    )  # used to format a date in the title and recipe
    recipe_datetime_format: str = (
        "%I:%M%p, %-d %b, %Y" if is_windows else "%-I:%M%p, %-d %b, %Y"
    )  # used to format a datetime in the recipe

    def is_enabled(self) -> bool:
        if callable(self.enable_on):
            return self.enable_on(self)
        return self.enable_on


def sort_category(a: str, b: str, categories_sort: List[str]) -> int:
    try:
        a_index = categories_sort.index(a)
    except ValueError:
        a_index = 999
    try:
        b_index = categories_sort.index(b)
    except ValueError:
        b_index = 999

    if a_index < b_index:
        return -1
    if a_index > b_index:
        return 1
    return -1 if a < b else 1


def get_local_now(offset: float = 0.0) -> datetime:
    return (
        datetime.utcnow()
        .replace(tzinfo=timezone.utc)
        .astimezone(timezone(offset=timedelta(hours=offset)))
    )


def onlyon_weekdays(days_of_the_week: List[int], offset: float = 0.0) -> bool:
    """
    Enable recipe only on the specified days_of_the_week

    :param days_of_the_week: Starts with 0 = Monday
    :param offset: timezone offset hours
    :return:
    """
    return get_local_now(offset).weekday() in days_of_the_week


def onlyon_days(days_of_the_month: List[int], offset: float = 0.0) -> bool:
    """
    Enable recipe only on the specified days_of_the_month

    :param days_of_the_month:
    :param offset: timezone offset hours
    :return:
    """
    return get_local_now(offset).day in days_of_the_month


def onlyat_hours(hours_of_the_day: List[int], offset: float = 0.0) -> bool:
    """
    Enable recipe only at the specified hours_of_the_day

    :param hours_of_the_day:
    :param offset: timezone offset hours
    :return:
    """
    return get_local_now(offset).hour in hours_of_the_day


def every_x_days(last_run: float, days: float, drift: float = 0.0) -> bool:
    """
    Enable recipe after X days after last run.

    .. code-block:: python

        Recipe(
            recipe="example",
            slug="example",
            src_ext="epub",
            category="Example",
            enable_on=lambda recipe: every_x_days(
                last_run=recipe.last_run, days=2, drift=60
            ),
        ),

    :param last_run:
    :param days:
    :param drift: In minutes
    :return:
    """
    if not last_run:
        return True
    last_run_dt = datetime.utcfromtimestamp(last_run).replace(tzinfo=timezone.utc)
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    return (now - last_run_dt) >= (timedelta(days=days) - timedelta(minutes=drift))


def every_x_hours(last_run: float, hours: float, drift: float = 0.0) -> bool:
    """
    Enable recipe after X hours after last run.

    .. code-block:: python

        Recipe(
            recipe="example",
            slug="example",
            src_ext="epub",
            category="Example",
            enable_on=lambda recipe: every_x_hours(
                last_run=recipe.last_run, hours=2, drift=15
            ),
        ),

    :param last_run:
    :param hours:
    :param drift: In minutes
    :return:
    """
    if not last_run:
        return True
    last_run_dt = datetime.utcfromtimestamp(last_run).replace(tzinfo=timezone.utc)
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    return (now - last_run_dt) >= (timedelta(hours=hours) - timedelta(minutes=drift))


def last_n_days_of_month(n_days: int, offset: float = 0.0) -> bool:
    """
    Enable recipe only on the last n days of the month

    :param n_days:
    :param offset: timezone offset hours
    :return:
    """
    now = get_local_now(offset)
    month_start, month_end = monthrange(now.year, now.month)
    month_days = list(range(month_start, month_end + 1))
    return onlyon_days(month_days[-n_days:], offset)


def first_n_days_of_month(n_days: int, offset: float = 0.0) -> bool:
    """
    Enable recipe only on the first n days of the month

    :param n_days:
    :param offset: timezone offset hours
    :return:
    """
    return onlyon_days(list(range(1, n_days + 1)), offset)
