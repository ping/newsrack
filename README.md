# newsrack

Generate an online "newsrack" of periodicals for your ereader.

Uses [calibre](https://calibre-ebook.com/) + [recipes](https://manual.calibre-ebook.com/news_recipe.html), [GitHub Actions](.github/workflows/build.yml), and hosted
on [GitHub Pages](https://pages.github.com/).

## Running Your Own Instance

### General Steps

1. Fork this repository.
2. Create a new branch, for example `custom`. Using a new branch makes a few things, like contributing fixes for example, easier.
3. Add your own recipes to the [`recipes_custom/`](recipes_custom) folder and customise [_recipes_custom.py](_recipes_custom.py). Optional.
4. Customise the cron schedule and job run time in [.github/workflows/build.yml](.github/workflows/build.yml). Optional.
5. Set the new branch `custom` as default.
6. Enable Pages in repository settings to deploy from `GitHub Actions`.
7. If needed, manually trigger the `Build` workflow from Actions to start your first build.

### What Can Be Customised

- The formats generated (`src_ext`, `target_ext`)
- When periodical recipes are enabled (`enable_on`)
- Remove/add recipes
- cron schedule and job timeout interval in [.github/workflows/build.yml](.github/workflows/build.yml)
- Cover colours and fonts

Look at the `Recipe` class in [_recipe_utils.py](_recipe_utils.py) to discover other options.

[Example fork repo](https://github.com/ping/newsrack-fork-test/) / [Example customisations](https://github.com/ping/newsrack-fork-test/compare/main...custom)

#### Recipe Definition

```python
# To be defined in _recipes_custom.py
Recipe(
    recipe="example",  # actual recipe name
    slug="example",  # file name slug
    src_ext="mobi",  # recipe output format
    category="news",  # category
    name="An Example Publication",
    # display name, taken from recipe source by default. Must be defined for built-in recipes.
    target_ext=[],
    # alt formats that the src_ext format will be converted to
    timeout=300,  # max interval (seconds) for executing the recipe, default 180 seconds
    overwrite_cover=False,  # generate a plain cover to overwrite Calibre's
    enable_on=True,  # determines when to run the recipe
    retry_attempts=1,  # retry attempts on TimeoutExpired, ReadTimeout
    cover_options=CoverOptions(),  # cover options
    tags=["example"],   # used in search
),
```

#### Examples

Run a built-in Calibre periodical recipe:

```python
Recipe(
    recipe="Associated Press",
    name="Associated Press",  # Required for built-in recipes
    slug="ap",
    src_ext="mobi",
    category="news",
),
```

Only generate epubs:

```python
Recipe(
    recipe="example",  # example.recipe.py
    slug="example",
    src_ext="epub",  # generate epub
    target_ext=[],  # don't generate alt formats
    category="example",
),
```

Use `enable_on` to conditionally enable a recipe:

```python
from _recipe_utils import Recipe, onlyon_days, onlyat_hours, onlyon_weekdays

Recipe(
    recipe="example1",
    slug="example1",
    src_ext="epub",
    category="example",
    enable_on=onlyon_weekdays([0]),  # only on Mondays
),
Recipe(
    recipe="example2",
    slug="example2",
    src_ext="epub",
    category="example",
    enable_on=onlyon_days([1, 14]),  # only on days 1, 14 of each month
),
Recipe(
    recipe="example3",
    slug="example3",
    src_ext="epub",
    category="example",
    enable_on=onlyat_hours(list(range(6, 12)), -5),  # from 6am-11.59am daily, for the timezone UTC-5
),

# instead of using the available functions, you can
# also define your own custom functions for enable_on
```

Use calibre-generated cover:

```python
Recipe(
    recipe="example",
    slug="example",
    src_ext="epub",
    category="example",
    overwrite_cover=False,
),
```

Customise the title date format and generated cover:

```python
from _recipe_utils import CoverOptions

Recipe(
    recipe="example",
    slug="example",
    src_ext="epub",
    category="example",
    title_date_format = "%Y-%m-%d",
    cover_options=CoverOptions(
        text_colour="white",
        background_colour="black",
        title_font_path="path/to/example.ttf",
        datestamp_font_path="path/to/example.ttf"
    ),
),
```

#### Recipe Accounts

Recipe accounts can be defined using a [environment secret](https://docs.github.com/en/actions/security-guides/encrypted-secrets) named ``ACCOUNTS``. The secret value is a json-serialised ``dict`` of recipe accounts like below:

```json
{
  "example-recipe-slug": {
    "username": "example_username",
    "password": "example_password"
  }
}
```

## Available Recipes

In addition to built-in Calibre [recipes](https://github.com/kovidgoyal/calibre/tree/master/recipes), [customised
recipes (`recipes/*.recipe.py`)](recipes) are included in this repository.

Recipes customised here have a modified `publication_date` which is set to the latest article date. This allows the
outputs to be sorted by recency. The recipe `title` is also modified to include the latest article date or issue name.

In alphabetical order:

<details>
<summary><b>News</b></summary>

1. [Asahi Shimbun](https://www.asahi.com/ajw/)
2. [Channel News Asia](https://www.channelnewsasia.com/)
3. [The Financial Times](https://www.ft.com/)
4. [The Financial Times (Print)](https://www.ft.com/todaysnewspaper/international)
5. [The Guardian](https://www.theguardian.com/international)
6. [The JoongAng Daily](https://koreajoongangdaily.joins.com/)
7. [The Korea Herald](https://koreaherald.com/)
8. [The New York Times](https://www.nytimes.com/)
9. [The New York Times (Print)](https://www.nytimes.com/section/todayspaper)
10. [South China Morning Post](https://www.scmp.com/)
11. [Sydney Morning Herald](https://www.smh.com.au/)
12. [Taipei Times](https://www.taipeitimes.com/)
13. [Wall Street Journal (Print)](https://www.wsj.com/print-edition/today)
14. [The Washington Post](https://www.washingtonpost.com/)
15. ~~[The Japan Times](https://www.japantimes.co.jp/)~~
16. ~~[Bloomberg News](https://www.bloomberg.com/)~~

</details>

<details>
<summary><b>Magazines</b></summary>

1. [The Atlantic Magazine](https://www.theatlantic.com/magazine/)
2. [The Economist](https://www.economist.com/printedition)
3. [Foreign Affairs](https://www.foreignaffairs.com/magazine)
4. [Harvard Business Review](https://hbr.org/magazine)
5. [Harvard International Review](https://hir.harvard.edu/)
6. [MIT Technology Review Magazine](https://www.technologyreview.com/magazine/)
7. [Nature](https://www.nature.com/nature/current-issue/)
8. [The New Republic Magazine](https://newrepublic.com/magazine)
9. [The New Yorker](https://www.newyorker.com/)
10. [Scientific American](https://www.scientificamerican.com/)
11. [Smithsonian Magazine](https://www.smithsonianmag.com/)
12. [The Spectator](https://www.spectator.co.uk/magazine)
13. [Time Magazine](https://time.com/magazine/)
14. [The World Today](https://www.chathamhouse.org/publications/the-world-today/)
15. ~~[Bloomberg Businessweek](https://www.bloomberg.com/businessweek)~~

</details>

<details>
<summary><b>Online Magazines</b></summary>

1. [The Atlantic](https://www.theatlantic.com/)
2. [The Diplomat](https://thediplomat.com/)
3. [FiveThirtyEight](https://fivethirtyeight.com/)
4. [Forbes - Editor's Picks](https://www.forbes.com/editors-picks/)
5. [Fulcrum](https://fulcrum.sg)
6. [Knowable Magazine](https://knowablemagazine.org/)
7. [Longreads - Features](https://longreads.com/features/)
8. [MIT Press Reader](https://thereader.mitpress.mit.edu/)
9. [MIT Technology Review](https://www.technologyreview.com/)
10. [Nautilus](https://nautil.us/)
11. [Politico](https://www.politico.com/)
12. [ProPublica](https://www.propublica.org/)
13. [Rest of World](https://restofworld.org)
14. [The Third Pole](https://www.thethirdpole.net/)
15. [Vox](https://www.vox.com/)
16. [Wired](https://www.wired.com/magazine/)

</details>

<details>
<summary><b>Books</b></summary>

1. [Asian Review of Books](https://asianreviewofbooks.com)
2. [Five Books](https://fivebooks.com/)
3. [Literary Hub](https://lithub.com)
4. [London Review of Books](https://www.lrb.co.uk/)
5. [The New Yorks Times - Books](https://www.nytimes.com/section/books)
6. [Poetry](https://www.poetryfoundation.org/poetrymagazine)

</details>

