# About

newslinkrss generates RSS feeds from generic sites that do not provide their
own. This is done by loading a given URL and collecting all links that
matches a pattern, given as a regular expression, to gather the relevant
information.

The results are printed as a RSS feed to stdout or, optionally, to a file. The
simplest way to use it is just configure your **local** feed reader, like
[Liferea](https://lzone.de/liferea/) or [Newsboat](https://newsboat.org/), to
use a "command" source and pass the correct command line arguments to generate
a suitable feed -- this allows you to centralize the configuration in the
reader itself and let it handle update times, etc.

Run `newslinkrss --help` for the complete list of command line options.


# Intended audience (and a rant)

This script is mostly intended to technically versed people using some kind
of Unix operating system (e.g. Linux). I was planning to write a detailed
documentation but I just gave up. There is no much hope of making it friendly
to casual users when every use case requires complex command lines, abuse of
regular expressions, strftime strings, XPath, etc.

## The Rant

Everything would be just easier if websites simply provided clean and complete
RSS or Atom feeds, but these sites are becoming rarer every day. Most sites
just assume we want to follow them through social media (and that we *use*
social media!) while giving away privacy and submitting ourselves to tracking
and personal data collection in exchange for timelines algorithmically
optimized to improve "engagement" with advertisers.

I'm still resisting and wrote lots of feed scrapers/filters in the last 10 or
so years; newslinkrss is one that replaced several of these ad-hoc filters by
centralizing some very common pieces of code and it is polished enough to be
published.




# Installation


## Installing from PyPI

This is the simplest installation method and will deliver the latest **stable**
version of the program. To install in your `$HOME` directory, just type:

    pip3 install newslinkrss

This assumes pip3 is installed and configured (which usually happens by
default in Linux distributions intended for general use).



## Installing from the Git repository

This installation process is recommended for developers and people wanting
the newest version. For that, just clone the Git repository and install or
update the program with:

    pip3 install -U .

You may want to do this in a virtual environment so it won't interfere with
other user-level or system-wide components and make experimentation with
development versions easier. In this case, just do:

    python3 -m venv my-venv
    . my-venv/bin/activate
    pip install -U .


newslinkrss depends on a few libraries and has one technically optional
dependency on [lxml](https://lxml.de/), but the setup script will always
install it anyway -- it is possible to run the script without installing it,
but a few nice features will be unavailable (XPath, `--with-body`, etc.).



# Usage examples

newslinkrss is lacking a lot of documentation, but the following examples
can show a bit of what it can and can not do. A complete list of options
can be read by typing `newslinkrss --help`.


### Simplest case

The simplest use case is just load a website, select all links matching a
pattern and expose a feed using the text of that link as description and
assuming that the publishing date is the date the command was run. For example,
to generate a feed from site https://www.jaraguadosul.sc.gov.br/noticias.php ,
collecting all links with the substring `/news/` in the URL, use:

    newslinkrss -p '.+/news/.+' https://www.jaraguadosul.sc.gov.br/noticias.php


### Following pages

We may need to get more information that the one available in the URL and
anchor text. This can be done by using option `--follow` (shortcut `-f`) that
will make newslinkrss load the candidate target page and look for more data
there. By default, it automatically captures the title of the page as the
title of the feed entry, page description as the item contents, and the page
publishing and update dates and times as the item publish time (**if** this
information is available in the page in some common formats, like
[Open Graph](https://ogp.me/) or Twitter cards.

With this option, newslinkrss will follow at most `--max-links` in the order
they appear in the HTML, make an HTTP GET request, download data up to the
limit given by option `--max-page-length`, while waiting up to `--http-timeout`
seconds to complete the process. Cookies will be remembered among these
requests, but they will only be kept in memory and forgotten once the program
finishes. To prevent excessive usage of memory and network resources, it is
important to set a good filter pattern and choose the link and download limits
wisely (the default values for these two are usually Ok, but edge cases may
require some fine-tuning).


### Generating complete feeds

Reuters [killed](https://news.ycombinator.com/item?id=23576022) its RSS feeds
in mid 2020, but we can bring them back to life and right into our news
readers. Our criteria will be:

- Find everything that appears as plain HTML on the front page:
  https://www.reuters.com/ There is an infinite scroll and more links are added
  periodically with Javascript, but we can just ignore this and load the page
  more frequently, giving chance to capture them;

- We want to be very selective with filtering so we only get the current news
  and do not waste time downloading things like section listings, utility
  pages, links for other domains, etc. By looking at the URLs of the news
  pages, we can notice that all of them follow a pattern similar to:
  https://www.reuters.com/world/europe/eu-proposes-create-solidarity-fund-ukraines-basic-needs-2022-03-18/
  Notice they all are in domain "https://www.reuters.com/", have at least one
  section ("/world/europe/") that is followed by part of the title and the
  publish date. This format is really great, as it allows us to ignore
  anything that does not look like a news article on the spot. So, a good
  pattern will be `'https://www.reuters.com/.+/.+\d{4}-\d{2}-\d{2}.+'`;

- newslinkrss deduplicates URLs automatically, so we don't need to worry if we
  end up capturing the same link twice;

- Target pages have Open Graph meta tags, so we can `--follow` them and get
  accurate publish dates and times with no extra effort. Better yet, as we know
  that **all** news pages that we want have them, we can also instruct
  newslinkrss to ignore any page without a valid date, preventing any non-news
  article, captured by accident, from appearing in our feed. This is done with
  option `--require-dates`;

- As we are already following and downloading the links, there is no much
  extra work to generate a full feed, i.e., one that includes the full text of
  the page. Option `--with-body` will copy the entire contents of the "body"
  element from the page into the feed, just removing a few obviously unwanted
  tags (scripts, forms, etc.). Including the entire body works for every case,
  but for this site we can filter a bit more and pick only actual text of the
  news article, ignoring unwanted noise like menus, sidebars, links to other
  news, etc. A quick "inspect element" shows that there is a single "article"
  element in the pages and that it has the text we want; We can use a XPath
  expression to select it with option `--body-xpath '//article'`. Again,
  careful usage of options `--max-links` and `--max-page-length` is required,
  as it is pretty easy to miss part of the text or generate some huge feeds
  by accident.

So, the complete syntax is:

    newslinkrss \
        --follow \
        -p 'https://www.reuters.com/.+/.+\d{4}-\d{2}-\d{2}.+' \
        --max-page-length 64 \
        --with-body \
        --body-xpath '//article' \
        --require-dates \
        https://www.reuters.com/



### Gathering more information

A more complex example is where it is necessary not only to follow the target
of candidate links but also stitch information from several sources (URL, link
text and destination contents) together. Assume we want to generate a feed from
https://revistaquestaodeciencia.com.br/ , which provides no facilities for it.
Looking into the site we find that:

- URLs for news articles have a date on them (in format `YYYY/MM/DD`), so it
  is possible to use this in the URL pattern (option `-p`) to limit which
  links the script will look for. Some are prefixed by a section stub and all
  are followed by a string generated from the title, so the regex must accept
  the date anywhere in it. Anything could be a filter here, but as all
  articles have a date on it we don't need to look anywhere else;

- There is no standard, not even de-facto standard, representation for the
  date an article was published, so the alternative is taking it from the URL
  too. This is done with options `--date-from-url` (which requires regular
  expression with a group capturing the substring that contains the date)
  `--url-date-fmt` (which defines the format of the date);

- Inconsistencies in the link formats prevent us from getting all articles
  titles from the links in the front page, so the alternative is to
  `--follow` every candidate link, downloading the target page and looking to
  the title there. This must be done **very carefully**: we don't want to
  abuse the website or get stuck downloading gigabytes of data, so we limit
  the processing to the first 50 links matching the regex (with option
  `--max-links`), only load the first 64 kB of data from the every followed
  link (option `--max-page-length`), and stop processing a page after 2s
  (option `--http-timeout`);

- We also generate a complete feed, as in the previous example, but there is
  no easy way to select a HTML element that has only the actual text of the
  article, so we include the complete of element "body".

The resulting command line is:

    newslinkrss -p '.+/\d{4}/\d{2}/\d{2}/.+' \
        --date-from-url '.*/(\d{4}/\d{2}/\d{2})/.*' \
        --url-date-fmt '%Y/%m/%d' \
        --follow \
        --with-body \
        --max-links 50 \
        --max-page-length 64 \
        --http-timeout 2 \
        'https://revistaquestaodeciencia.com.br/'

To make understanding easier, this example uses the long, verbose, form of
some options even when abbreviations are available. For the same reason, some
of the options are set to the default values and are not strictly required
but they are listed anyway. See `newslinkrss --help` for details.


### Using complex XPath expressions

Sometimes we need to fight really hard to get the date that a particular item
was last updated. Taking GitHub issues as an example: while GH provides Atom
feeds for releases and commits (but always to specific branches), there is
no equivalent for issues and pull requests. Of course, there is an API for
that but it requires authentication with a GitHub account, enables tracking,
and requires writing a specific bridge to get the data as a feed. This makes
the scraping approach easier even with the very convoluted example that
follows.

The URLs for issues and PRs are pretty usable, we can already use them to
limit how many issues will be shown, their status, filter by date, etc. Just
look at the one used in the example.

However, we need to get the date of the last comment on the issue and set it
as the publishing date of the item, otherwise the reader won't show us that
it was updated. A solution is to follow every issue page while using a XPath
expression to find the last occurrence of a "relative-time" tag that GitHub
uses to mark the timestamp of a comment and parse the absolute date from
attribute "datetime". This is done with options `--date-from-xpath` and
`--xpath-date-fmt`.

The resulting command line is the following:

    newslinkrss \
        --follow \
        --with-body \
        --http-timeout 5 \
        --max-links 30 \
        --max-page-length 1024 \
        -p '^https://github.com/.+/issues/\d+$' \
        --date-from-xpath '(//h3/a/relative-time)[last()]/@datetime' \
        --xpath-date-fmt '%Y-%m-%dT%H:%M:%SZ' \
        'https://github.com/lwindolf/liferea/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc'

Debugging XPath expressions is not a very easy task, the simplest way is just
open the target page in Firefox, launch web developer tools and use the $x()
helper function to get what the expression will return, for example:
`$x('(//h3/a/relative-time)[last()]/@datetime')`.



### Error reporting, testing, and other small tricks

By default, newslinkrss writes exceptions and error messages to the feed
output itself. This is a very practical way to report errors to the user, as
this program is intended to work mostly on the background of the actual
user-facing application. It is possible to disable this behavior with option
`--no-exception-feed` (shortcut `-E`).

Notice that the program always return a non-zero status code on failures. Some
news readers (e.g. Liferea) won't process the output in these cases and discard
the feed entries with the error reports. You may need to override the status
code with something like `newslinkrss YOUR_OPTIONS; exit 0`.

newslinkrss has an option `--test` that will skip the feed generation step
and just print the links and titles that were captured for a particular set
of options to stdout. That's a simple way to check if a pattern is working
as intended.

Option `-o` allows writing the output to an file; it is no much different
than redirecting stdout, but will ensure that only valid XML with the right
encoding is written.

Writing output to files and error reporting on the feed itself allows for
some unusual but interesting use patterns: for example, it is trivial for a
company, group, or development team to have an internal "feed server", where
feeds are centrally downloaded by a cron job, saved to a web server public
directory and then transparently provided to the end users. A setup with
Alpine and nginx running in a LXD container is surprisingly small.




## Caveats

Be very careful with escape characters! In the shell, it is recommended to
use single quotes for regexes, so "\\" is not escaped. This becomes more
confusing if your feed reader also use escape sequences but with different
or conflicting rules (e.g. Newsboat uses "\\" as escapes but does not follow
the same rules used by bash). When in doubt, run the command in the shell or
use a wrapper script to test for any unusual behavior introduced by the
program.

Some feed readers run commands in a synchronous (blocking) mode and their
interface will get stuck until the command terminates. Liferea had this
behavior [until version 1.13.7](https://github.com/lwindolf/liferea/commit/b03af3b0f6a4e42b17dfa49782faa6c044055738),
for example. A typical workaround is to create a script with all calls to
newslinkrss that saves the generated feeds to files (see option `-o`),
schedule this script to run from cron and configure Liferea to load the
feed from the files. This solves the frozen interface problem, but requires
configuring feeds in two different places.



# Bugs

Yes :-)



# Contributing

For this project I started an experiment: I'm using [sourcehut](https://sr.ht/)
as the primary repository for code and other tools, leaving the usual Github
and Gitlab as non-advertised mirrors. Sourcehut does everything by the
old-school way and most features just work without an user account. Check the
[project page](https://sr.ht/~ittner/newslinkrss/) there to see how it works.

If this sounds too strange, just clone the repository with an
`git clone https://git.sr.ht/~ittner/newslinkrss`, publish your fork somewhere
and send an email with the branches to be merged to `~ittner/newslinkrss@lists.sr.ht`
(that's correct: tildes and slashes are valid characters for email addresses).

If you change the code, please run in through pyflakes for static analysis and
[black](https://pypi.org/project/black/) to ensure a consistent formatting.




# License

Copyright (C) 2020  Alexandre Erwin Ittner <alexandre@ittner.com.br>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.




# Contact information

- Author: Alexandre Erwin Ittner
- Email: <alexandre@ittner.com.br>
- Web: <https://www.ittner.com.br>

