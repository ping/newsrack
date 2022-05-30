from dataclasses import dataclass, field
from typing import List, Union, Callable
from datetime import datetime, timezone, timedelta
import time
from functools import cmp_to_key

default_recipe_timeout = 120


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
        bool, Callable[[], bool]
    ] = True  # determines when to run the recipe
    run_interval_in_days: float = 0  # kinda like Calibre's every X days
    drift_in_hours: float = (
        1  # allowance for schedule drift since scheduler is not precise
    )
    job_log: dict = field(default_factory=dict, init=False)

    def is_enabled(self) -> bool:
        is_due = self.job_log.get(self.name, 0) < (
            time.time()
            - (24 * self.run_interval_in_days - self.drift_in_hours) * 60 * 60
        )
        if callable(self.enable_on):
            return is_due and self.enable_on()
        return is_due and self.enable_on


sorted_categories = ["news", "magazines", "books"]


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


# Only mobi work as periodicals on the Kindle
# Notes:
#   - When epub is converted to mobi periodicals:
#       - masthead is lost
#       - mobi retains periodical support but has the non-funtional
#         calibre generated nav, e.g. Next Section, Main, etc
#       - article summary/description is lost
#   - When mobi periodical is converted to epub:
#       - epub loses the calibre generated nav, e.g. Next Section, Main, etc
#         but full toc is retained
#   - Recipe can be defined twice with different src_ext, will work except
#     for potential throttling and time/bandwidth taken

# Keep this list in alphabetical order
recipes = [
    Recipe(
        recipe="asahi-shimbun",
        slug="asahi-shimbun",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="asian-review",
        slug="arb",
        src_ext="mobi",
        category="books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], 8),
    ),
    Recipe(
        recipe="atlantic",
        slug="the-atlantic",
        src_ext="mobi",
        timeout=180,
        category="magazines",
    ),
    Recipe(
        recipe="atlantic-magazine",
        slug="atlantic-magazine",
        src_ext="mobi",
        overwrite_cover=False,
        category="magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -4),
    ),
    Recipe(
        recipe="channelnewsasia",
        slug="channelnewsasia",
        src_ext="mobi",
        timeout=180,
        category="news",
    ),
    Recipe(
        recipe="thediplomat",
        name="The Diplomat",
        slug="the-diplomat",
        src_ext="mobi",
        category="magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5], 5.5),
    ),
    Recipe(
        recipe="economist",
        slug="economist",
        src_ext="mobi",
        overwrite_cover=False,
        category="magazines",
        timeout=240,
    ),
    Recipe(
        recipe="ft",
        slug="ft",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="fivebooks",
        slug="fivebooks",
        src_ext="mobi",
        category="books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4]),
    ),
    Recipe(
        recipe="guardian",
        slug="guardian",
        src_ext="mobi",
        category="news",
    ),
    # Ad-blocked/Requires login
    # Recipe(
    #     recipe="japan-times",
    #     slug="japan-times",
    #     src_ext="mobi",
    #     category="news",
    # ),
    Recipe(
        recipe="joongangdaily",
        slug="joongang-daily",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="korea-herald",
        slug="korea-herald",
        src_ext="mobi",
        timeout=180,
        category="news",
    ),
    Recipe(
        recipe="london-review",
        slug="lrb",
        src_ext="mobi",
        overwrite_cover=False,
        category="books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4]),
    ),
    Recipe(
        recipe="nature",
        slug="nature",
        src_ext="mobi",
        category="magazines",
        overwrite_cover=False,
        enable_on=onlyon_weekdays([2, 3, 4], 0),
    ),
    Recipe(
        recipe="newyorker",
        slug="newyorker",
        src_ext="mobi",
        category="magazines",
        overwrite_cover=False,
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -5),
    ),
    Recipe(
        recipe="nytimes-global",
        slug="nytimes-global",
        src_ext="mobi",
        timeout=180,
        category="news",
    ),
    Recipe(
        recipe="nytimes-paper",
        slug="nytimes-print",
        src_ext="mobi",
        overwrite_cover=False,
        timeout=180,
        category="news",
    ),
    Recipe(
        recipe="nytimes-books",
        slug="nytimes-books",
        src_ext="mobi",
        category="books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -5),
    ),
    Recipe(
        recipe="politico-magazine",
        slug="politico-magazine",
        src_ext="mobi",
        category="magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5], -5),
    ),
    Recipe(
        recipe="scientific-american",
        slug="scientific-american",
        src_ext="mobi",
        category="magazines",
        overwrite_cover=False,
        enable_on=onlyon_days(list(range(13, 18)), -5),  # middle of the month?
    ),
    Recipe(
        recipe="scmp",
        slug="scmp",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="taipei-times",
        slug="taipei-times",
        src_ext="mobi",
        timeout=180,
        category="news",
    ),
    Recipe(
        recipe="thirdpole",
        slug="thirdpole",
        src_ext="mobi",
        category="magazines",
        enable_on=onlyat_hours(list(range(5, 20)), 5.5),
    ),
    Recipe(
        recipe="time-magazine",
        slug="time-magazine",
        src_ext="mobi",
        overwrite_cover=False,
        category="magazines",
        enable_on=onlyon_weekdays([3, 4, 5, 6], -4),
    ),
    Recipe(
        recipe="vox",
        slug="vox",
        src_ext="mobi",
        category="magazines",
    ),
    Recipe(
        recipe="wapo",
        slug="wapo",
        src_ext="mobi",
        timeout=600,
        category="news",
    ),
    Recipe(
        recipe="wired",
        slug="wired",
        src_ext="mobi",
        timeout=180,
        overwrite_cover=True,
        category="magazines",
    ),
]
