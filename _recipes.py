from dataclasses import dataclass, field
from typing import List, Union, Callable
from datetime import datetime, timezone, timedelta

default_recipe_timeout = 120


@dataclass
class Recipe:
    """A Calibre recipe definition"""

    recipe: str
    name: str
    slug: str
    src_ext: str
    category: str
    target_ext: List[str] = field(default_factory=list)
    timeout: int = default_recipe_timeout
    overwrite_cover: bool = True
    enable_on: Union[bool, Callable[[], bool]] = True

    def is_enabled(self):
        if callable(self.enable_on):
            return self.enable_on()
        return self.enable_on


def get_local_now(offset: float = 0.0):
    return (
        datetime.utcnow()
        .replace(tzinfo=timezone.utc)
        .astimezone(timezone(offset=timedelta(hours=offset)))
    )


def onlyon_weekdays(days_of_the_week: List[int], offset: float = 0.0):
    return get_local_now(offset).weekday() in days_of_the_week


def onlyon_days(days_of_the_month: List[int], offset: float = 0.0):
    return get_local_now(offset).day in days_of_the_month


def onlyat_hours(hours_of_the_day: List[int], offset: float = 0.0):
    return get_local_now(offset).hour in hours_of_the_day


# the azw3 formats don't open well in the kindle (stuck, cannot return to library)
recipes = [
    Recipe(
        recipe="asian-review",
        name="Asian Review of Books",
        slug="arb",
        src_ext="mobi",
        category="books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], 8),
    ),
    Recipe(
        recipe="atlantic",
        name="The Atlantic",
        slug="the-atlantic",
        src_ext="mobi",
        timeout=180,
        category="magazines",
    ),
    Recipe(
        recipe="atlantic-magazine",
        name="The Atlantic Magazine",
        slug="atlantic-magazine",
        src_ext="mobi",
        overwrite_cover=False,
        category="magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -4),
    ),
    Recipe(
        recipe="channelnewsasia",
        name="ChannelNewsAsia",
        slug="channelnewsasia",
        src_ext="mobi",
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
        name="The Economist",
        slug="economist",
        src_ext="mobi",
        overwrite_cover=False,
        category="news",
        timeout=240,
    ),
    Recipe(
        recipe="ft",
        name="Financial Times",
        slug="ft",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="fivebooks",
        name="Five Books",
        slug="fivebooks",
        src_ext="mobi",
        category="books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4]),
    ),
    Recipe(
        recipe="guardian",
        name="The Guardian",
        slug="guardian",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="japan-times",
        name="Japan Times",
        slug="japan-times",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="joongangdaily",
        name="Joongang Daily",
        slug="joongang-daily",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="korea-herald",
        name="Korea Herald",
        slug="korea-herald",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="london-review",
        name="London Review of Books",
        slug="lrb",
        src_ext="mobi",
        overwrite_cover=False,
        category="books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4]),
    ),
    Recipe(
        recipe="newyorker",
        name="The New Yorker",
        slug="newyorker",
        src_ext="mobi",
        category="magazines",
        overwrite_cover=False,
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -5),
    ),
    Recipe(
        recipe="nytimes-global",
        name="NY Times Global",
        slug="nytimes-global",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="nytimes-books",
        name="New York Times Books",
        slug="nytimes-books",
        src_ext="mobi",
        category="books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -5),
    ),
    Recipe(
        recipe="politico-magazine",
        name="POLITICO Magazine",
        slug="politico-magazine",
        src_ext="mobi",
        category="magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5], -5),
    ),
    Recipe(
        recipe="scientific-american",
        name="Scientific American",
        slug="scientific-american",
        src_ext="mobi",
        category="magazines",
        overwrite_cover=False,
        enable_on=onlyon_days(list(range(13, 18)), -5),  # middle of the month?
    ),
    Recipe(
        recipe="scmp",
        name="South China Morning Post",
        slug="scmp",
        src_ext="mobi",
        category="news",
    ),
    Recipe(
        recipe="thirdpole",
        name="The Third Pole",
        slug="thirdpole",
        src_ext="mobi",
        category="magazines",
        enable_on=onlyat_hours(list(range(5, 20)), 5.5),
    ),
    Recipe(
        recipe="wapo",
        name="The Washington Post",
        slug="wapo",
        src_ext="mobi",
        timeout=600,
        category="news",
    ),
]
