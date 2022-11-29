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

from _recipe_utils import (
    Recipe,
    CoverOptions,
    onlyon_days,
    onlyat_hours,
    onlyon_weekdays,
    first_n_days_of_month,
    last_n_days_of_month,
)

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

categories_sort: List[str] = ["News", "Magazines", "Online Magazines", "Books"]

# Keep this list in alphabetical order
recipes: List[Recipe] = [
    Recipe(
        recipe="asahi-shimbun",
        slug="asahi-shimbun",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["asia", "japan"],
        cover_options=CoverOptions(
            logo_path_or_url="https://p.potaufeu.asahi.com/ajw/css/images/en_logo@2x.png"
        ),
    ),
    Recipe(
        recipe="asian-review",
        slug="arb",
        src_ext="mobi",
        target_ext=["epub"],
        category="Books",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], 8),
        tags=["asia"],
        cover_options=CoverOptions(
            logo_path_or_url="https://i2.wp.com/asianreviewofbooks.com/content/wp-content/uploads/2016/09/ARBwidelogo.png"
        ),
    ),
    Recipe(
        recipe="atlantic",
        slug="the-atlantic",
        src_ext="mobi",
        target_ext=["epub"],
        category="Online Magazines",
        tags=["editorial", "commentary"],
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/The_Atlantic_Logo_11.2019.svg/1200px-The_Atlantic_Logo_11.2019.svg.png"
        ),
    ),
    Recipe(
        recipe="atlantic-magazine",
        slug="atlantic-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -4) and last_n_days_of_month(14, -4),
        tags=["editorial", "commentary"],
    ),
    Recipe(
        recipe="channelnewsasia",
        slug="channelnewsasia",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["asia", "singapore"],
        cover_options=CoverOptions(
            logo_path_or_url="https://www.channelnewsasia.com/sites/default/themes/mc_cna_theme/images/logo.png"
        ),
    ),
    Recipe(
        recipe="thediplomat",
        name="The Diplomat",
        slug="the-diplomat",
        src_ext="mobi",
        target_ext=["epub"],
        category="Online Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5], 5.5),
        tags=["asia"],
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/The_Diplomat_logo.svg/1024px-The_Diplomat_logo.svg.png"
        ),
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
        cover_options=CoverOptions(
            logo_path_or_url="https://fivebooks.com/app/themes/five-books/assets/images/logo.png"
        ),
    ),
    Recipe(
        recipe="fivethirtyeight",
        slug="fivethirtyeight",
        src_ext="mobi",
        target_ext=["epub"],
        category="Online Magazines",
        tags=["politics"],
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/FiveThirtyEight_Logo.svg/1024px-FiveThirtyEight_Logo.svg.png"
        ),
    ),
    Recipe(
        recipe="forbes-editors-picks",
        slug="forbes-editors-picks",
        src_ext="mobi",
        target_ext=["epub"],
        timeout=360,  # will glitch often and take a really long time
        retry_attempts=2,
        category="Online Magazines",
        tags=["business"],
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -4)
        and onlyat_hours(list(range(8, 20)), -4),
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Forbes_logo.svg/1024px-Forbes_logo.svg.png"
        ),
    ),
    Recipe(
        recipe="foreign-affairs",
        slug="foreign-affairs",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Magazines",
        enable_on=(first_n_days_of_month(7, -4) or last_n_days_of_month(7, -4))
        and onlyat_hours(list(range(8, 22)), -4),
    ),
    Recipe(
        recipe="ft",
        slug="ft-online",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["business"],
        cover_options=CoverOptions(
            logo_path_or_url="https://www.ft.com/partnercontent/content-hub/static/media/ft-horiz-new-black.215c1169.png"
        ),
    ),
    Recipe(
        recipe="ft-paper",
        slug="ft-print",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["business"],
        cover_options=CoverOptions(
            logo_path_or_url="https://www.ft.com/partnercontent/content-hub/static/media/ft-horiz-new-black.215c1169.png"
        ),
    ),
    Recipe(
        recipe="guardian",
        slug="guardian",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/The_Guardian.svg/1024px-The_Guardian.svg.png"
        ),
    ),
    Recipe(
        recipe="harvard-intl-review",
        slug="harvard-intl-review",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        enable_on=onlyat_hours(list(range(11, 15))),
        cover_options=CoverOptions(
            logo_path_or_url="https://hir.harvard.edu/content/images/2020/12/HIRlogo_crimson-4.png"
        ),
    ),
    Recipe(
        recipe="hbr",
        slug="hbr",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Magazines",
        enable_on=first_n_days_of_month(3, -5) or last_n_days_of_month(14, -5),
        tags=["business"],
    ),
    Recipe(
        recipe="joongangdaily",
        slug="joongang-daily",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["asia", "southkorea"],
        cover_options=CoverOptions(
            logo_path_or_url="https://koreajoongangdaily.joins.com/resources/images/common/logo.png"
        ),
    ),
    Recipe(
        recipe="knowable-magazine",
        slug="knowable-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        tags=["science"],
        cover_options=CoverOptions(logo_path_or_url="https://i.imgur.com/OMxGtzQ.jpg"),
    ),
    Recipe(
        recipe="korea-herald",
        slug="korea-herald",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["asia", "southkorea"],
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/en/thumb/5/55/The_Korea_Herald.svg/1024px-The_Korea_Herald.svg.png"
        ),
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
        recipe="longreads-features",
        slug="longreads-features",
        src_ext="mobi",
        target_ext=["epub"],
        category="Online Magazines",
        enable_on=onlyon_weekdays([0, 2, 4, 6]) and onlyat_hours(list(range(0, 6))),
        cover_options=CoverOptions(
            logo_path_or_url="https://i0.wp.com/longreads.com/wp-content/uploads/2022/08/longreads-logo-1.png?w=600&ssl=1"
        ),
    ),
    Recipe(
        recipe="mit-press-reader",
        slug="mit-press-reader",
        src_ext="mobi",
        target_ext=["epub"],
        category="Online Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4], -4),
        cover_options=CoverOptions(
            text_colour="#444444",
            logo_path_or_url="https://dhjhkxawhe8q4.cloudfront.net/mit-press/wp-content/uploads/2022/03/25123303/mitp-reader-logo_0-scaled.jpg",
        ),
    ),
    Recipe(
        recipe="mit-tech-review",
        slug="mit-tech-review-feed",
        src_ext="mobi",
        target_ext=["epub"],
        category="Online Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5], -4),
        tags=["technology"],
        cover_options=CoverOptions(
            text_colour="#444444",
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/MIT_Technology_Review_modern_logo.svg/1024px-MIT_Technology_Review_modern_logo.svg.png",
        ),
    ),
    Recipe(
        recipe="mit-tech-review-magazine",
        slug="mit-tech-review-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        overwrite_cover=False,
        enable_on=first_n_days_of_month(7, -5) or last_n_days_of_month(7, -5),
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
        category="Online Magazines",
        tags=["science"],
        cover_options=CoverOptions(
            logo_path_or_url="https://assets.nautil.us/13891_bb83b72bf545e376f3ff9443bda39421.png"
        ),
    ),
    Recipe(
        recipe="new-republic-magazine",
        slug="new-republic-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        overwrite_cover=False,
        enable_on=(first_n_days_of_month(7) or last_n_days_of_month(7))
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
        timeout=900,
        retry_attempts=0,
        enable_on=onlyat_hours(
            list(range(0, 4)) + list(range(8, 18)) + list(range(22, 24))
        ),
        cover_options=CoverOptions(
            logo_path_or_url="https://static01.nyt.com/newsgraphics/2015/12/23/masthead-2016/8118277965bda8228105578895f2f4a7aeb22ce2/nyt-logo.png"
        ),
    ),
    Recipe(
        recipe="nytimes-paper",
        slug="nytimes-print",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        timeout=900,
        retry_attempts=0,
        enable_on=onlyat_hours(list(range(4, 8))),
        cover_options=CoverOptions(
            logo_path_or_url="https://static01.nyt.com/newsgraphics/2015/12/23/masthead-2016/8118277965bda8228105578895f2f4a7aeb22ce2/nyt-logo.png"
        ),
    ),
    Recipe(
        recipe="nytimes-books",
        slug="nytimes-books",
        src_ext="mobi",
        target_ext=["epub"],
        category="Books",
        timeout=300,
        retry_attempts=0,
        enable_on=onlyat_hours(list(range(18, 22))),
        cover_options=CoverOptions(
            logo_path_or_url="https://static01.nyt.com/newsgraphics/2015/12/23/masthead-2016/8118277965bda8228105578895f2f4a7aeb22ce2/nyt-logo.png"
        ),
    ),
    Recipe(
        recipe="poetry",
        slug="poetry-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=False,
        category="Books",
        enable_on=first_n_days_of_month(7, -6) or last_n_days_of_month(7, -5),
        tags=["literature", "arts"],
    ),
    Recipe(
        recipe="politico-magazine",
        slug="politico-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        category="Online Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5], -5),
        cover_options=CoverOptions(
            logo_path_or_url="https://www.politico.com/dims4/default/bbb0fd2/2147483647/resize/1160x%3E/quality/90/?url=https%3A%2F%2Fstatic.politico.com%2F0e%2F5b%2F3cf3e0f04ca58370112ab667c255%2Fpolitico-logo.png"
        ),
    ),
    Recipe(
        recipe="propublica",
        slug="propublica",
        src_ext="mobi",
        target_ext=["epub"],
        category="Online Magazines",
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/ProPublica_text_logo.svg/1280px-ProPublica_text_logo.svg.png"
        ),
    ),
    Recipe(
        recipe="restofworld",
        slug="restofworld",
        src_ext="mobi",
        target_ext=["epub"],
        category="Online Magazines",
        enable_on=onlyon_weekdays([0, 1, 2, 3, 4, 5])
        and onlyat_hours(list(range(9, 19))),
        tags=["technology"],
        cover_options=CoverOptions(
            logo_path_or_url="https://149346090.v2.pressablecdn.com/wp-content/uploads/2020/05/cropped-SocialCard-1.png"
        ),
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
        tags=["asia", "hongkong"],
        cover_options=CoverOptions(
            logo_path_or_url="https://cdn.shopify.com/s/files/1/0280/0258/2595/files/SCMP_Logo_2018_540x.png"
        ),
    ),
    Recipe(
        recipe="spectator-magazine",
        slug="spectator-magazine",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        tags=["europe", "britain"],
        enable_on=onlyon_weekdays([4]),
        overwrite_cover=False,
    ),
    Recipe(
        recipe="sydney-morning-herald",
        slug="sydney-morning-herald",
        src_ext="mobi",
        target_ext=["epub"],
        category="News",
        tags=["australia"],
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/en/thumb/8/86/Sydney_Morning_Herald_logo.svg/1024px-Sydney_Morning_Herald_logo.svg.png"
        ),
    ),
    Recipe(
        recipe="taipei-times",
        slug="taipei-times",
        src_ext="mobi",
        target_ext=["epub"],
        timeout=600,
        category="News",
        enable_on=onlyat_hours(list(range(6, 14)), 8),
        tags=["asia", "taiwan"],
        cover_options=CoverOptions(
            logo_path_or_url="https://www.taipeitimes.com/assets/images/logo.gif"
        ),
    ),
    Recipe(
        recipe="thirdpole",
        slug="thirdpole",
        src_ext="mobi",
        target_ext=["epub"],
        category="Online Magazines",
        enable_on=onlyat_hours(list(range(5, 20)), 5.5),
        tags=["asia", "climate"],
        cover_options=CoverOptions(
            logo_path_or_url="https://www.thethirdpole.net/content/uploads/2020/02/TheThirdPoleLogo2.png"
        ),
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
        category="Online Magazines",
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Vox_logo.svg/300px-Vox_logo.svg.png"
        ),
    ),
    Recipe(
        recipe="wapo",
        slug="wapo",
        src_ext="mobi",
        target_ext=["epub"],
        timeout=600,
        category="News",
        cover_options=CoverOptions(
            logo_path_or_url="https://www.washingtonpost.com/sf/brand-connect/dell-technologies/the-economics-of-change/media/wp_logo_black.png"
        ),
    ),
    Recipe(
        recipe="wired",
        slug="wired",
        src_ext="mobi",
        target_ext=["epub"],
        overwrite_cover=True,
        category="Online Magazines",
        tags=["technology"],
        enable_on=(first_n_days_of_month(7) or last_n_days_of_month(7))
        and onlyat_hours(list(range(10, 18))),
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Wired_logo.svg/1024px-Wired_logo.svg.png"
        ),
    ),
    Recipe(
        recipe="world-today",
        slug="world-today",
        src_ext="mobi",
        target_ext=["epub"],
        category="Magazines",
        enable_on=(first_n_days_of_month(7) or last_n_days_of_month(7))
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
        cover_options=CoverOptions(
            logo_path_or_url="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/WSJ_Logo.svg/1024px-WSJ_Logo.svg.png"
        ),
    ),
]
