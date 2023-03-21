# newsrack

Generate an online "newsrack" of periodicals for your ereader.

Features:
- Download anywhere using your device browser
- Subscribe via OPDS feeds

Uses [calibre](https://calibre-ebook.com/) + [recipes](https://manual.calibre-ebook.com/news_recipe.html), [GitHub Actions](.github/workflows/build.yml), and hosted
on [GitHub Pages](https://pages.github.com/).

![eInk Kindle Screenshot](https://user-images.githubusercontent.com/104607/226074902-b4a672ff-8fb0-4f2e-8307-b1ec736792e5.png)
![Mobile Screenshot](https://user-images.githubusercontent.com/104607/226074930-45289aec-0d56-48a2-a02e-deeca497851f.jpg)

[![Buy me a coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=&slug=ping&button_colour=FFDD00&font_colour=000000&font_family=Bree&outline_colour=000000&coffee_colour=ffffff)](https://www.buymeacoffee.com/ping)

## Running Your Own Instance

### General Steps

1. Fork this repository.
2. Create a new branch, for example `custom`. Using a new branch makes a few things, like contributing fixes for example, easier.
3. Add your own recipes to the [`recipes_custom/`](recipes_custom) folder and customise [_recipes_custom.py](_recipes_custom.py). Optional.
4. Customise the cron schedule and job run time in [.github/workflows/build.yml](.github/workflows/build.yml). Optional.
5. Set the new branch `custom` as default
   - from Settings > Branches > Default branch
6. Enable Pages in repository settings to deploy from `GitHub Actions`
   - from Settings > Pages > Build and deployment > Source
7. If needed, manually trigger the `Build` workflow from Actions to start your first build.

### What Can Be Customised

`newsrack` supports extensive customisation such as:
- add/remove recipes
- the formats generated
- when recipes are executed
- cover colours and fonts

Review the [wiki](https://github.com/ping/newsrack/wiki#customisation) page to understand what can be changed according to your preference.

You can also refer to the [example fork repo](https://github.com/ping/newsrack-fork-test/) and see the [actual customisations](https://github.com/ping/newsrack-fork-test/compare/main...custom) in action.


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
11. [Noema](https://www.noemamag.com/)
12. [Politico](https://www.politico.com/)
13. [ProPublica](https://www.propublica.org/)
14. [Quanta Magazine](https://www.quantamagazine.org/)
15. [Rest of World](https://restofworld.org)
16. [The Third Pole](https://www.thethirdpole.net/)
17. [Vox](https://www.vox.com/)
18. [Wired](https://www.wired.com/magazine/)

</details>

<details>
<summary><b>Arts & Culture</b></summary>

1. [Asian Review of Books](https://asianreviewofbooks.com)
2. [Five Books](https://fivebooks.com/)
3. [Literary Hub](https://lithub.com)
4. [London Review of Books](https://www.lrb.co.uk/)
5. [The New Yorks Times - Books](https://www.nytimes.com/section/books)
6. [The Paris Review - Daily](https://www.theparisreview.org/blog/)
7. [Poetry](https://www.poetryfoundation.org/poetrymagazine)

</details>

