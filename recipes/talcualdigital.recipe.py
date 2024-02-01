#!/usr/bin/env python
# vim:fileencoding=utf-8
from calibre.web.feeds.news import AutomaticNewsRecipe

class BasicUserRecipe1706819102(AutomaticNewsRecipe):
    title          = 'TalCual Digital'
    oldest_article = 2
    max_articles_per_feed = 100
    auto_cleanup   = True
    language       = 'es'
    remove_javascript = True
    remove_empty_feeds = True

    feeds          = [
        ('main', 'https://talcualdigital.com/feed'),
    ]