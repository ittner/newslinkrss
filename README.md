# About

newslinkrss generates RSS feeds from generic sites that do not provide their
own. This is done by loading a given URL and collecting all links that
matches a pattern (given as a regular expression) to gather the relevant
information.

The results are printed as a RSS feed to stdout or, optionally, to a file. The
best usage approach is just to configure your **local** feed reader, like
[Liferea](https://lzone.de/liferea/) or [Newsboat](https://newsboat.org/), to
use a "command" source and pass the correct command line arguments to generate
a suitable feed -- this allows you to centralize the configuration in the
reader itself and let it handle update times, etc.

Run `newslinkrss --help` for the complete list of command line options.


# Intended audience (and a rant)

This script is mostly intended to technically versed people using some kind
of Unix operating system (e.g. Linux). I was planning to write some detailed
documentation but gave I just up. There is no much hope of making it friendly
to casual users when every use case requires complex command lines, abuse of
regular expressions, timefmt strings, XPath, etc.

Everything would be just easier if websites simply provided clean and
complete RSS or Atom feeds, but these are becoming rarer every day. Most sites
just assume we want to follow them through social media (and that we *use*
social media!) while giving away privacy and submitting ourselves to tracking
and personal data collection in exchange for timelines algorithmically
optimized to improve "engagement" with advertisers.

I'm still resisting and wrote lots of feed scrapers/filters in the last 10
or so years; newslinkrss is one that replaced several of these ad-hoc filters
by centralizing some very common pieces of code and is polished enough to be
published.




# Installation


## Installing from PyPI

This is the simplest installation method and will deliver the latest **stable**
version of the program. To install the current stable version in your `$HOME`
directory, just type:

    pip3 install newslinkrss

This assumes pip3 is installed and configured (which usually happens by
default in Linux distributions intended for general use).



## Installing from the Git repository

This installation process is recommended for developers and people wanting
the newest version. For that, just clone the Git repository and install or
update the program with:

    pip install -U .

You may want to do this in a virtual environment so it won't interfere with
other user-level or system-wide components and will make experimentation
with development versions easier. In this case, just do:

    python3 -m venv my-venv
    . my-venv/bin/activate
    pip install -U .


newslinkrss depends on a few libraries and has one technically optional
dependency on [lxml](https://lxml.de/), but the setup script will always
install it anyway -- it is possible to run the script without installing it,
but a few nice features will be unavailable (XPath, `--with-body`, etc.).



# Usage examples

To generate a feed from site https://www.jaraguadosul.sc.gov.br/noticias.php ,
collecting all links with the substring `/news/` in the URL, use:

    newslinkrss -p '.+/news/.+' https://www.jaraguadosul.sc.gov.br/noticias.php


### Following pages and generating complete feeds

And a more complex example where it is necessary to follow the target of
candidate links and stitch information from several sources (URL, link text
and destination contents) together. Assume we want to generate a feed from
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
  (option `--http-timeout`).

- As we are already following and downloading the links, there is no much
  extra cost in generating a full feed, i.e., one that includes the full
  text of the page. Option `--with-body` will copy the entire contents of
  the "body" element from the page into the feed, just removing a few
  obviously unwanted tags (scripts, forms, etc.). Using this option requires
  a careful usage of options `--max-links` and `--max-page-length` to limit
  the amount of data we download, as it is pretty easy to generate some huge
  feeds.

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


### Using XPath expressions

Sometimes we need to fight really hard to get the date that a particular item
was last updated. Taking GitHub issues as an example: while GH provides Atom
feeds for releases and commits (but always to specific branches), there is
none for issues and pull requests. Of course, there is a API for that but it
requires authentication with a GitHub account, enables tracking, and required
writing a specific bridge to get the data as a feed. This makes the scraping
approach easier even with the very convoluted example that follows.

The URLs for issues and PRs are pretty usable, we can already use them to
limit how many issues will be shown, their status, filter by date, etc. Just
look at the example.

However, we need to get the date of the last comment on the issue and set it
as the publishing date of the feed, otherwise the reader won't show us that
it was updated. A solution for that is following every page and using a
XPath expression to find the last occurrence of a "relative-time" tag that
GitHub uses to mark the timestamp of a comment and parse its date from
attribute "datetime". This is done with options `--date-from-xpath` and
`--xpath-date-fmt`.

The resulting command line is the following but, again, the only extended
documentation is the one available in `--help`.

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

Debugging XPath expressions is not a very easy task, best way is just open
the target page in Firefox, launch web developer tools and use the $x() helper
function to get what the expression will return, for example:
`$x('(//h3/a/relative-time)[last()]/@datetime')`.


### Caveats

Be very careful with escape characters! For the shell, it is recommended to
use single quotes for regexes, so "\\" is not escaped. This is more
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



## Contributing

For this project I started an experiment: I'm using [sourcehut](https://sr.ht/)
for the code repository and other management tools, instead of the usual Github
or Gitlab. That's the old-school way of doing things and most features just
work without an user account. Check the [project page](https://sr.ht/~ittner/newslinkrss/)
there to see how it works.

If this sounds too strange, just clone the repository with an
`git clone https://git.sr.ht/~ittner/newslinkrss`, publish your fork somewhere
and send an email with the branches to be merged to `~ittner/newslinkrss@lists.sr.ht`
(that's correct. Tildes and slashes are valid for email addresses)

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


