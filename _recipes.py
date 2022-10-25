# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

# --------------------------------------------------------------------
# This file defines default recipes distributed with newsrack.
# To customise your own instance, do not modify this file.
# Add your recipes to _recipes_custom.py instead and new recipe source
# files to recipes_custom/.
# --------------------------------------------------------------------

from typing import List

from _recipe_utils import Recipe, onlyon_days, onlyat_hours, onlyon_weekdays

# Only mobi work as periodicals on the Kindle
# Notes:
#   - When epub is converted to mobi periodicals:
#       - masthead is lost
#       - mobi retains periodical support but has the non-functional
#         calibre generated nav, e.g. Next Section, Main, etc
#       - article summary/description is lost
#   - When mobi periodical is converted to epub:
#       - epub loses the calibre generated nav, e.g. Next Section, Main, etc
#         but full toc is retained
#   - Recipe can be defined twice with different src_ext, will work except
#     for potential throttling and time/bandwidth taken

categories_sort: List[str] = ["News", "Magazines", "Books"]

# Keep this list in alphabetical order
recipes: List[Recipe] = [
    Recipe(
        recipe="asahi-shimbun",
        slug="asahi-shimbun",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["asia"],
    ),
    Recipe(
        recipe="asian-review",
        slug="arb",
        src_ext="mobi",
        target_ext=["epub"],
        category="Books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], 8),
        tags=["asia"],
    ),
    Recipe(
        recipe="atlantic",
        slug="the-atlantic",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        tags=["editorial", "commentary"],
    ),
    Recipe(
        recipe="atlantic-magazine",
        slug="atlantic-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -4)
        and onlyon_days(list(range(32 - 14, 32)), -4),
        tags=["editorial", "commentary"],
    ),
    Recipe(
        recipe="channelnewsasia",
        slug="channelnewsasia",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["asia"],
    ),
    Recipe(
        recipe="thediplomat",
        name="The Diplomat",
        slug="the-diplomat",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5], 5.5),
        tags=["asia"],
    ),
    Recipe(
        recipe="economist",
        slug="economist",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Magazines",
        tags=["business"],
        timeout=240,
    ),
    Recipe(
        recipe="fivebooks",
        slug="fivebooks",
        src_ext="mobi",
        target_ext=["epub"],
        category="Books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4]),
    ),
    Recipe(
        recipe="forbes-editors-picks",
        slug="forbes-editors-picks",
        src_ext="mobi",
        target_ext=["epub"],
        timeout=360,  # will glitch often and take a really long time
        retry_attempts=2,
        category="Magazines",
        tags=["business"],
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -4)
        and onlyat_hours(list(range(8, 20)), -4),
    ),
    Recipe(
        recipe="foreign-affairs",
        slug="foreign-affairs",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Magazines",
        enable_on=onlyon_days(list(range(1, 1 + 7)) + list(range(32 - 7, 32)), -4)
        and onlyat_hours(list(range(8, 22)), -4),
    ),
    Recipe(
        recipe="ft",
        slug="ft-online",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["business"],
    ),
    Recipe(
        recipe="ft-paper",
        slug="ft-print",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["business"],
    ),
    Recipe(
        recipe="guardian",
        slug="guardian",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
    ),
    Recipe(
        recipe="harvard-intl-review",
        slug="harvard-intl-review",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        enable_on=onlyat_hours(list(range(11, 15))),
    ),
    Recipe(
        recipe="hbr",
        slug="hbr",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Magazines",
        enable_on=onlyon_days(list(range(1, 1 + 3)) + list(range(32 - 14, 32)), -5),
        tags=["business"],
    ),
    Recipe(
        recipe="joongangdaily",
        slug="joongang-daily",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["asia"],
    ),
    Recipe(
        recipe="knowable-magazine",
        slug="knowable-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        tags=["science"],
    ),
    Recipe(
        recipe="korea-herald",
        slug="korea-herald",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["asia"],
    ),
    Recipe(
        recipe="london-review",
        slug="lrb",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4]),
    ),
    Recipe(
        recipe="mit-press-reader",
        slug="mit-press-reader",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -4),
    ),
    Recipe(
        recipe="mit-tech-review",
        slug="mit-tech-review-feed",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5], -4),
        tags=["technology"],
    ),
    Recipe(
        recipe="mit-tech-review-magazine",
        slug="mit-tech-review-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        overwrite_cover=False,
        enable_on=onlyon_days(list(range(1, 1 + 7)) + list(range(32 - 7, 32)), -5),
        tags=["technology"],
    ),
    Recipe(
        recipe="nature",
        slug="nature",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        overwrite_cover=False,
        enable_on=onlyon_weekdays([2, 3, 4], 0),
        tags=["science"],
    ),
    Recipe(
        recipe="nautilus",
        slug="nautilus",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        tags=["science"],
    ),
    Recipe(
        recipe="new-republic-magazine",
        slug="new-republic-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        overwrite_cover=False,
        enable_on=onlyon_days(list(range(1, 7)) + list(range(24, 32)))
        and onlyat_hours(list(range(8, 16))),
    ),
    Recipe(
        recipe="newyorker",
        slug="newyorker",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        overwrite_cover=False,
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -5),
        tags=["editorial", "commentary"],
    ),
    # don't let NYT recipes overlap to avoid throttling
    Recipe(
        recipe="nytimes-global",
        slug="nytimes-global",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        timeout=480,
        enable_on=onlyat_hours(
            list(range(0, 4)) + list(range(8, 18)) + list(range(22, 24))
        ),
    ),
    Recipe(
        recipe="nytimes-paper",
        slug="nytimes-print",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="News",
        enable_on=onlyat_hours(list(range(4, 8))),
    ),
    Recipe(
        recipe="nytimes-books",
        slug="nytimes-books",
        src_ext="mobi",
        target_ext=["epub"],
        category="Books",
        enable_on=onlyat_hours(list(range(18, 22))),
    ),
    Recipe(
        recipe="poetry",
        slug="poetry-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Magazines",
        enable_on=onlyon_days(list(range(1, 1 + 7)) + list(range(32 - 7, 32)), -5),
        tags=["literature", "arts"],
    ),
    Recipe(
        recipe="propublica",
        slug="propublica",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
    ),
    Recipe(
        recipe="politico-magazine",
        slug="politico-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5], -5),
    ),
    Recipe(
        recipe="restofworld",
        slug="restofworld",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5])
        and onlyat_hours(list(range(9, 19))),
        tags=["technology"],
    ),
    Recipe(
        recipe="scientific-american",
        slug="scientific-american",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        overwrite_cover=False,
        enable_on=onlyon_days(list(range(15, 31)), -5),  # middle of the month?
        tags=["science"],
    ),
    Recipe(
        recipe="scmp",
        slug="scmp",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["asia"],
    ),
    Recipe(
        recipe="sydney-morning-herald",
        slug="sydney-morning-herald",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
    ),
    Recipe(
        recipe="taipei-times",
        slug="taipei-times",
        src_ext="mobi",
        target_ext=["epub"],
        timeout=600,
        category="News",
        enable_on=onlyat_hours(list(range(6, 14)), 8),
        tags=["asia"],
    ),
    Recipe(
        recipe="thirdpole",
        slug="thirdpole",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        enable_on=onlyat_hours(list(range(5, 20)), 5.5),
        tags=["asia", "climate"],
    ),
    Recipe(
        recipe="time-magazine",
        slug="time-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Magazines",
        enable_on=onlyon_weekdays([3, 4, 5, 6], -4),
    ),
    Recipe(
        recipe="vox",
        slug="vox",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
    ),
    Recipe(
        recipe="wapo",
        slug="wapo",
        src_ext="mobi",
        target_ext=["epub"],
        timeout=600,
        category="News",
    ),
    Recipe(
        recipe="wired",
        slug="wired",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=True,
        category="Magazines",
        tags=["technology"],
    ),
    Recipe(
        recipe="world-today",
        slug="world-today",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        enable_on=onlyon_days(list(range(1, 7)) + list(range(24, 32)))
        and onlyat_hours(list(range(4, 12))),
    ),
    Recipe(
        recipe="wsj-paper",
        slug="wsj-print",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["business"],
        timeout=300,
        enable_on=onlyat_hours(list(range(0, 8)), -4),
    ),
]
