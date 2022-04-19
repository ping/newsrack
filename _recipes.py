from collections import namedtuple

Receipe = namedtuple(
    "Recipe", ["recipe", "name", "slug", "src_ext", "target_ext", "timeout"]
)
default_recipe_timeout = 120

# the azw3 formats don't open well in the kindle (stuck, cannot return to library)
recipes = [
    Receipe(
        recipe="channelnewsasia",
        name="ChannelNewsAsia",
        slug="channelnewsasia",
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
        recipe="economist",
        name="The Economist",
        slug="economist",
        src_ext="mobi",
        target_ext=[],
        timeout=300,
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
        recipe="fivebooks",
        name="Five Books",
        slug="fivebooks",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
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
        recipe="japan-times",
        name="Japan Times",
        slug="japan-times",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
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
        recipe="korea-herald",
        name="Korea Herald",
        slug="korea-herald",
        src_ext="mobi",
        target_ext=[],
        timeout=default_recipe_timeout,
    ),
    Receipe(
        recipe="nytimes-global",
        name="NY Times Global",
        slug="nytimes-global",
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
    Receipe(
        recipe="politico-magazine",
        name="POLITICO Magazine",
        slug="politico-magazine",
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
        recipe="wapo",
        name="The Washington Post",
        slug="wapo",
        src_ext="mobi",
        target_ext=[],
        timeout=600,
    ),
]
