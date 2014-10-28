#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'九哥'
SITENAME = u'九哥的部落'
SITE_SUB_TITLE = u'技术、阅读、生活'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'Asia/Chongqing'

DEFAULT_LANG = u'zh'
HTML_LANG = u'zh'

# Feed generation is usually not desired when developing
# Feed configuration
FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = 'feeds/%s.atom.xml'

CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

# Blogroll
#LINKS = (('Pelican', 'http://getpelican.com/'),
#         ('Python.org', 'http://python.org/'),
#         ('Jinja2', 'http://jinja.pocoo.org/'),
#         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('github', 'https://github.com/zouivex'),
          ('linkedin', 'https://cn.linkedin.com/in/zouivex'),
          ('google plus', 'https://plus.google.com/u/0/104327320364152471669/'),
          ('rss', SITEURL + '/' + FEED_ALL_ATOM),)

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

# static paths will be copied without parsing their contents
STATIC_PATHS = [
    'images',
    'pdf',
    'extra/CNAME',
    'extra/favicon.png'
    ]

EXTRA_PATH_METADATA = {'extra/CNAME': {'path': 'CNAME'},
                       'extra/favicon.png': {'path': 'favicon.png'},}

# Same as Octopress structure
ARTICLE_URL = 'blog/{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = 'blog/{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'

MONTH_ARCHIVE_SAVE_AS = 'posts/{date:%Y}/{date:%b}/index.html'

# Extract metadata from file name
FILENAME_METADATA = '(?P<date>\d{4}-\d{2}-\d{2})_(?P<slug>.*)'

# Use totally new generated files each time
DELETE_OUTPUT_DIRECTORY = True

# This is a single author site
AUTHOR_URL = ''
AUTHOR_SAVE_AS = ''

#Theme configurations: foundation-default-colours
#THEME = 'theme/simplegrey'
THEME = 'theme/pelican-bootstrap3'

# Plugins
PLUGIN_PATHS = ["pelican-plugins"]

# Depends on
PLUGINS = []

DISQUS_SITENAME = 'httpzouivexgithubio'

# Support PDF download
# PDF_PROCESSOR = True

# Extensions
MD_EXTENSIONS = [
    'codehilite(css_class=highlight,linenums=False)',
    'extra',
    'toc'
    ]
#
# Configuration for theme pelican-bootstrap3
#
FAVICON = 'favicon.png'
TYPOGRIFY = True
CC_LICENSE = True

DISPLAY_RECENT_POSTS_ON_SIDEBAR = True
DISPLAY_CATEGORIES_ON_SIDEBAR = True
DISPLAY_TAGS_ON_SIDEBAR = True
DISPLAY_TAGS_INLINE = True
DISPLAY_CATEGORIES_ON_MENU = False
SHOW_ARTICLE_CATEGORY = True

PYGMENTS_STYLE = 'vs'
DISPLAY_ARTICLE_INFO_ON_INDEX = True
