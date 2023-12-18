# About

newslinkrss generates RSS feeds for websites that do not provide their own.
It works by loading URLs with lists of articles, looking for links matching
regular expressions, and optionally visiting them to get more information
and even processing these target pages with XPath and CSS Selectors if
necessary. It is basically a purpose-specific crawler or scraper.

The results are printed as a RSS feed to stdout or optionally to a file. The
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
regular expressions, strftime strings, XPath, CSS Selectors, etc.

## The Rant

Everything would be just easier if websites simply provided clean and complete
RSS or Atom feeds, but these sites are becoming rarer every day. Most sites
assume we want to follow them through social media (or that we *use* social
media!) and expect us to give away our privacy and submit ourselves to
tracking and personal data collection in exchange for timelines
algorithmically optimized to improve "engagement" with advertisers.

I'm still resisting and wrote lots of feed scrapers/filters in the last 18 or
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

newslinkrss depends on a few libraries, this will ensure all them are also
installed correctly.


## Installing from the Snap

newslinkrss is also available as [a Snap](https://snapcraft.io/newslinkrss).
This makes easy to always have the latest version, updated automatically, and
do not requires creating Python virtual environments or touching user or
system level Python modules. To install in any Snap-enabled distribution, run:

    sudo snap install newslinkrss

This will install and follow to the latest stable version; if you want to
always have the latest development version, freshly built from the Git master
branch, install it from the "edge" channel with:

    sudo snap install newslinkrss --edge



# Usage examples

newslinkrss is lacking a lot of documentation, but the following examples
can show a bit of what it can and can not do. To make understanding easier,
examples uses mostly the long, verbose, form of some options even when
abbreviations are available. A complete list of options, abbreviations,
default values, etc. can be read by typing `newslinkrss --help`.



### Simplest case

The simplest use case is just load a website, select all links matching a
pattern and expose a feed using the text of that link as description and
setting the publish date to the date and time that the command was run. For
example, to generate a feed from site https://www.jaraguadosul.sc.gov.br/noticias.php ,
collecting all links with the substring `/news/` in the URL, use:

    newslinkrss -p '.+/news/.+' https://www.jaraguadosul.sc.gov.br/noticias.php

It won't generate a good feed (the limitation with the dates being the
biggest issue) but we will go back to this example later. It is already
more practical than checking this government website manually, however.



### Following pages

To improve the situation exposed in the previous example, we may want to
get information that it not is available from the URL or anchor text.
Option `--follow` (shortcut `-f`) will make newslinkrss load the candidate
target page and look for more data there. By default, it automatically
captures the title of the page as the title of the feed entry, keeps the
summary from anchor text, and loads author information and the page
publishing and update dates and times from the page metadata (**if** this
information is available in some common format, like
[Open Graph](https://ogp.me/ ) or Twitter cards.

Reuters [killed](https://news.ycombinator.com/item?id=23576022) its RSS feeds
in mid 2020, so let's take them as an example and use newslinkrss to bring
the feed back to life and right into our news readers. Our criteria will be:

- First we must find every link that appears as plain HTML on the front page:
  https://www.reuters.com/ There is an infinite scroll and more links are
  added periodically with JavaScript, but we can just ignore this and poll
  the page more frequently, giving enough chance to capture them;

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

- newslinkrss deduplicates URLs automatically, so we don't need to worry if
  we end up capturing the same link twice;

- Target pages have Open Graph meta tags, so by just following them we can
  get accurate publish dates and times with no extra effort. Better yet, as
  we know that **all** news pages that we want have them, we can also instruct
  newslinkrss to ignore any page without a valid date, preventing any non-news
  article, captured by accident, from appearing in our feed. This is done
  with option `--require-dates`;

- All page titles are something like "The actual headline | Reuters". This
  format is nice for a website but not so for feed items: the "| Reuters"
  part is not only redundant (the feed title already tells us about the
  source of the article) but also noisy, as it makes scanning through the
  headlines harder. newslinkrss has an option `--title-regex` for exactly
  this use case of cleaning up redundant text from titles. It accepts a
  regular expression with a single capture group; if the expression matches,
  the text from the group will be used as the title, otherwise the original
  text will be used (so we don't loose titles if something changes at the
  source, for example). For this case, a good choice would be
  `--title-regex '(.+)\s+\|'` .

- When following pages we must be **very careful** as we do not want to
  abuse the website or get stuck downloading gigabytes of data. newslinkrss
  has several options to prevent these problems, all with sensible default
  values, but we should check if they work for every use case. At first we
  must limit number of links to be followed with option `--max-links` (the
  default value is 50, so it is OK for this so we can just omit the option
  for now), then we may use option `--max-page-length` to only load the
  first 512 kB of data from the every followed link, and stop processing a
  page after after a few seconds with option `--http-timeout` (the default
  value is 2 s, so we can omit this option for now too);

- Cookies will be remembered among these requests, but they will only be
  kept in memory and forgotten once the program finishes (there is an
  option `--no-cookies` if this behavior becomes a problem for a particular
  source).


So, our syntax for this will be:

    newslinkrss \
        --follow \
        -p 'https://www.reuters.com/.+/.+\d{4}-\d{2}-\d{2}.+' \
        --max-page-length 512 \
        --require-dates \
        --title-regex '(.+)\s+\|' \
        https://www.reuters.com/


### Generating complete feeds

Complete feeds are the ones which include the full text of the article with
it, instead of just a summary and a link. They are really nice as we can
read everything in the news aggregator itself. A good item body should be
mostly static and clean HTML (so no scripts, interactive content, aggressive
formatting, etc.) leaving everything else to the aggregator to handle.

So let's extend the previous example from Reuters website: as we are already
following and downloading the links, there is no much extra work to generate
the full feed from it. Option `--with-body` will copy the entire contents of
the "body" element from the page into the feed, just removing a few obviously
unwanted tags (scripts, forms, etc.).

Including the entire body works for every case, but for this site we can
filter a bit more and pick only actual text of the news article, ignoring
unwanted noise like menus, sidebars, links to other news, etc. Running a
quick "inspect element" in Firefox shows us that there is a single "article"
element in the pages and that it has the text we want. newslinkrss allows
using both XPath expressions and CSS Selectors to pick particular elements
from the DOM and, for this case, we choose XPath by using option
`--body-xpath '//article'` — sometimes CSS Selectors are easier and
cleaner, if it appears that you are struggling too much with a particular
XPath expression, try using a CSS Selector with `--body-csss` instead.

So, the updated syntax will be:

    newslinkrss \
        --follow \
        -p 'https://www.reuters.com/.+/.+\d{4}-\d{2}-\d{2}.+' \
        --max-page-length 512 \
        --with-body \
        --body-xpath '//article' \
        --require-dates \
        --title-regex '(.+)\s+\|' \
        https://www.reuters.com/

And now we have our feed!

The body for this example is very simple but the selectors (both XPath and
CSSS) are surprisingly powerful. They can return any number of elements in
any order, so you can create a readable item body from whatever exists in
the source page by carefully picking elements in the right order (XPath
operator "|" and CSSS "," are your friends!).


### Cleaning body elements (and handling bad CSS class names)

If we look at the bodies captured with the previous Reuters example, we will
notice that (at least in July 2023 when this text is being written) there are
still some unwanted elements that add too much noise to the output. Inside
the `article` element, we also get:

- Social media share buttons: actually, not the buttons themselves because
  for elements are removed by default, but the `ul` and `li` elements that
  encapsulated them remain -- newslinkrss simple does not know which ones
  are useful and which ones are not, so it can not remove them automatically;

- Related articles and "Read next" sections: we want only the text of the
  current article in a clean and readable format.

Usually it is very easy to get rid of these using options `--body-remove-xpath`
(shortcut `-X`) and `--body-remove-csss` (shortcut `-C`), but this particular
site has a very non-semantic structure and uses automatically generated
and unstable-looking class names like `article-header__toolbar__3lT1M`,
`article-body__toolbar__1_CO8`, and `article__read-next__Kjxdw`. However, we
can notice a pattern here: there are some stable prefixes and random suffixes
that will possibly change faster than the "stable" part.

We can handle these with a bit more advanced object selections. For this
case, let's use CSS Selectors as they are a bit shorter and more readable:

- First, we look for [attribute substrings](https://www.w3.org/TR/selectors/#attribute-substrings)
  and remove the toolbars with a
  `--body-remove-csss 'div[class*="article-header__toolbar__"], div[class*="article-body__toolbar__"]'`.
  Notice that we are playing really loose here! The first rule does not mean
  "any `div` element marked with a class with a name starting with
  `article-header__toolbar__`", it actually means "any `div` element with a
  `class` attribute containing the substring `article-header__toolbar__`". In
  a site with shorter class names, we would probably face a lot of false
  positives! But extracting feeds is almost always a game of kludges, so let
  it be.

- Do the same hack for the related articles but, looking a bit closer we can
  notice that inside its main div we also have another tagged with class
  `read-next-panel`, which is a pretty readable and stable-looking name! So
  let's add an extra standard match for it as a fail-safe in the event the
  external div stops matching; it will still leave some garbage text, but
  will remove the most of the article list. The syntax is
  `--body-remove-csss 'div[class*="article__read-next__"], div.read-next-panel'`.

We could have combined these two rules in one, but leaving them separate
makes debugging easier as the rules are printed with the log messages when
running with `--log debug`, allowing us to see which ones are matching.

It is also important to notice that options `--body-remove-*` work over the
DOM that was generated from `--body-xpath` or `--body-csss`. These options
allows a lot of control over the way the elements are copied from the main
document DOM, and the result can end up being very different once we start
using some clever selections.

So, our updated command line is now:

    newslinkrss \
        --follow \
        -p 'https://www.reuters.com/.+/.+\d{4}-\d{2}-\d{2}.+' \
        --max-page-length 512 \
        --with-body \
        --body-xpath '//article' \
        --body-remove-csss 'div[class*="article-header__toolbar__"], div[class*="article-body__toolbar__"]' \
        --body-remove-csss 'div[class*="article__read-next__"], div.read-next-panel' \
        --require-dates \
        --title-regex '(.+)\s+\|' \
        https://www.reuters.com/

... and it gives us a cleaner feed!




### A single feed from multiple start URLs

It is possible to have several start URLs and make newslinkrss generate a
single feed with content gathered from all of them, all other options
remaining the same. Typically, this can be used to filter only the sections
of interest from a site while keeping all articles in the same subscription
in your newsreader.

Let's continue with our Reuters example, but imagine we only want articles
from sections "World" and "Technology". We noticed before that the section
names appears in the URL, so a first approach may be just hack the link
pattern to require `(world|technology)` in it. However this solution may fail
to grab, for example, some news articles that appears in the "technology"
page but have a different section in their URLs (as they can be related to
both) or skip articles that do not appear in the front page at all (as space
there is limited).

This can be solved with this command:

    newslinkrss \
        --follow \
        -p 'https://www.reuters.com/.+/.+\d{4}-\d{2}-\d{2}.+' \
        --max-page-length 512 \
        --with-body \
        --body-xpath '//article' \
        --body-remove-csss 'div[class*="article-header__toolbar__"], div[class*="article-body__toolbar__"]' \
        --body-remove-csss 'div[class*="article__read-next__"], div.read-next-panel' \
        --require-dates \
        --title-regex '(.+)\s+\|' \
        --title "Reuters (Technology and World only)" \
        https://www.reuters.com/technology/ https://www.reuters.com/world/

Notice that it is almost the same command line used in the previous example,
except for the multiple URLs and option `--title`, which allow us to give an
alternate title to the feed. This is welcome because newslinkrss picks the
title from the first URL that has one, and it may be related to the first
section only (alternatively, you can rename the feed in your newsreader if
it has an option for it).

When using multiple start pages, a special attention is required to the
parameter `--max-links`! If the limit is reached in a page, links loaded
from later pages will be skipped.

This feature may be also used to capture more items from sites that split
them in very short pages but does still have stable pagination URLs, like:
`https://news.example.org/page-1.html https://news.example.org/page-2.html
https://news.example.org/page-3.html`.  If you are using newslinkrss in a
shell script, you may avoid repeated URLs by using sequence expansions (in
bash) or `seq -f` (in everything else).


### Gathering information from limited metadata

Some sites do not provide standard (not even quasi-standard) metadata that
newslinkrss can use automatically, so we must gather it from the pages
with site-specific approaches, following links and stitching information
from several elements together. Assume we want to generate a feed from
https://revistaquestaodeciencia.com.br/ , which provides no much facilities
for it. Looking into the site we find that:

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
  `--follow` every candidate link, downloading the target page and looking
  for  the title there.

- As we are already following, there is no much extra effort to also
  generate a complete feed. The full text of the article is in an "article"
  element, so we can use `--body-xpath "//article"` here too.

- The target page has no author information in its metadata so newslinkrss
  will not be able to find their names automatically. However, it has a link
  to the list of articles from the same author in format
  `<a href="/autor/author-name">Author Name</a>` and we can use the prefix
  from attribute `href` to pick it with XPath (using option
  `--author-from-xpath`) or CSS Selectors (with `--author-from-csss`). The
  CSS approach is simpler for this particular case, so let's use an
  `--author-from-csss 'a[href^="/autor/"]'`. While not required for this
  site (name is the only child element of "a"), some sites may prefix the
  author name with a "by " or similar; For these cases, we could also use
  options `--csss-author-regex` and `--xpath-author-regex` to select only the
  name with a regular expression. Also notice that author is an optional
  element in both RSS and Atom, but it is nice to have it appearing in the
  correct fields in the news reader so we can use this information for
  filtering reading lists, for example.

The resulting command line is:

    newslinkrss \
        -p 'https://revistaquestaodeciencia.com.br/.*\d{4}/\d{2}/\d{2}/.+' \
        --date-from-url '.*/(\d{4}/\d{2}/\d{2})/.*' \
        --url-date-fmt '%Y/%m/%d' \
        --follow \
        --with-body \
        --body-xpath "//article" \
        --author-from-csss 'a[href^="/autor/"]' \
        --max-page-length 512 \
        --http-timeout 4 \
        --title-regex '(.+)\s+\|' \
        'https://revistaquestaodeciencia.com.br/'


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



### The first example, revisited

Now that we have a few extra tricks in our sleeves we can check back that
very first example and fix some of its limitations:

- First, we need the correct publish dates; they are neither in the URL nor
  in the anchor text, so we need to `--follow` the pages and get the dates
  from there. The pages also have no metadata to do this easily, but they
  have a publish date intended for human readers in a slice of HTML like this:
  `<small class="text-muted"><b>23/12/2022</b> - some unrelated text</small>`,
  so it is pretty easy to get it with a CSS selector:
  `--date-from-csss 'small.text-muted > b'`. It will capture the "23/12/2022"
  from the text node of inner element "b", no need to filter through
  `--csss-date-regex` to remove unwanted text, but the date format is still
  ambiguous so we need to give an explicit format with option
  `--csss-date-fmt '%d/%m/%Y'`;

- Let's be extra careful with the URL pattern and never capture (or follow!)
  links pointing to other domains. We can replace it with a more restricted
  `-p 'https://www.jaraguadosul.sc.gov.br/news/.+'`;

- As we are already following the pages, let's also generate a full feed. The
  relevant part of the articles are inside a "div" element with attribute "id"
  set to "area_impressao" (that's Portuguese for "printing_area" and one may
  imagine it is being used to format the page for printing, however there is
  neither an alternate style sheet nor a @media selector for it ... anyway,
  at least it helps us to select the correct text). We can isolate this
  element with a XPath expression `'//div[@id="area_impressao"]'` but this is
  slightly more complex than the equivalent CSS Selector `div#area_impressao`,
  so let's stick with the later;

- That site can be a bit slow sometimes, so let's be extra tolerant and
  increase the HTTP timeout to 10 s;

And then we have our fixed command line:

    newslinkrss \
        -p 'https://www.jaraguadosul.sc.gov.br/news/.+' \
        --http-timeout 10 \
        --follow \
        --with-body \
        --body-csss 'div#area_impressao' \
        --date-from-csss 'small.text-muted > b' \
        --csss-date-fmt '%d/%m/%Y' \
        https://www.jaraguadosul.sc.gov.br/noticias.php

... not perfect, but it gives us a very practical and usable feed!



## More useful notes

### Capturing good titles

The title of an item is one of the most important attributes you can get from
a feed, as you probably will choose between continue reading or not based on
it. newslinkrss has some strategies for finding a good title even if the
source site has some very bad design choices.

If you are not following the target pages (i.e. not using option `--follow`),
the only title available will be the anchor text. If following, newslinkrss
will, by default, use the target document title with a fall back to the anchor
text or description for pages that do not have titles.

Some sites have titles that are just too polluted but also have an alternate
element with a descriptive text which can be used in its place. For these
cases, newslinkrss has options `--title-from-xpath` and `--title-from-csss`.
Both have the same effect but the former selects the element or attribute with
the alternate title using a XPath expression and the later picks an element
using a CSS Selector (it is not possible to select attributes with CSS). If
these options are given but do not return any valid text, newslinkrss will
fall back to the usual title selection.

After the title is selected, it is also interesting to remove redundant text
from it. newslinkrss has an option `--title-regex` for this exact purpose:
it accepts a regular expression with a single capture group and, if the
expression matches, the captured text will be used as the title. Otherwise it
will keep the original text, so we do not loose titles if something changed
at the source, for example.  Most common use case for this option is to remove
the name of the site from article titles: it is a good design to have them
in the web but, on a news reader, we do not want them using the very limited
space available for item titles just to repeat information already shown in
the feed title.

It is also possible to limit the length of the title, as sometimes errors in
the source site can give us insanely long ones. This is done with option
`--max-title-length` (shortcut: `-l`) and the default value, 150, should
probably work for the most use cases.



### Capturing publish dates

The date when a particular item was published is another very useful piece
of information from a feed, so newslinkrss also has several ways of getting
it from source pages, with availability depending on the way it is used (i.e.
with or without `--follow`) and the information available in the HTML.
Related options are the following:

- If explicitly used, options `--date-from-xpath`, `--xpath-date-regex`, and
  `--xpath-date-fmt` will allow reading dates from any element in the target
  page which can be found with a XPath expression. Naturally, the target page
  which must be downloaded with `--follow`; The XPath expression must return
  a string (from the inner text or the attributes of an element), the second
  is optional, but if given it must provide a regular expression with a single
  capture group with the date, and the third should give the date format. If
  no regex is given, all the string will be used and if no date format is
  given, the code will try some common date formats;

- If explicitly used, options `--date-from-csss`, `--csss-date-regex`, and
  `--csss-date-fmt` work in a similar way as the previous ones, but using
  CSS Selectors instead. They are not as powerful or flexible as XPath, but
  simpler, cleaner, and more suitable for HTML;

- If explicitly used, options `--date-from-text` and `--text-date-fmt` allow
  reading the date from the anchor text (i.e., the text inside tag `<a>`)
  associated to a particular entry in the index page; no `--follow` is
  necessary. The first option must provide a regular expression with a single
  capture group for the date (which allows removing non-date parts of the
  string) and the second option should give the date format. If the format is
  not given, the code will try some common date formats;

- If explicitly used, options `--date-from-url` and `--url-date-fmt` allow
  reading the date from the item link; this is specially interesting for
  sites that have URLs in format
  "https://example.org/posts/2020/09/22/happy-hobbit-day/" but provide
  no better source for a publish date. Again, no `--follow` is necessary. The
  first option must provide a regular expression with a single capture group
  with the date and the second option should give the date format. If the
  format is not given, code will try some common date formats;

- If no date was found yet and option `--follow` is used, dates will be read
  automatically from standard metadata (Open Graph, etc.) if they exists in
  the target page;

- If no date was found yet, but the HTTP request returned a "Last-Modified"
  header, assumes it as the actual last modification date (even if the
  server may be lying to us here).

These options are tried in this order with the first valid date being picked.
This way, options explicitly included in command line have priority, with
higher precedence being given to the ones which may return a "good" date.
If no date options are listed, or if could not grab a date from the document,
standard metadata and HTTP headers will be used (in this order).


#### Locale-dependent dates

Some date formats depend on the system locale, most common cases being month
names (tokens `%b` and `%B`), and the date parsing options will also depend
on it to interpret these dates correctly. By default, newslinkrss will use
the locale set for the current user, read from environment variables, and
ignore any failure if it is not available or is invalid. Option `--locale`
allows setting an explicit locale name, so newslinkrss will use it or abort
in the event of a failure. If you want to keep the default best-effort
approach for a non-default locale, set environment variable LC_ALL when
calling newslinkrss (i.e. call with
`"LC_ALL=pt_BR.UTF-8 newslinkrss <options>"`).



### Ignoring URLs

The link pattern (-p) has a counterpart `--ignore-pattern` (shortcut `-i`)
which also accepts a regular expression and makes `newslinkrss` ignore any
matching URL. Depending on the amount of information that the website puts on
the URLs, this can be used for excluding native advertisement, uninteresting
sections, or other unwanted content from the feed, without support from the
feed reader and without counting to the total URL limit (`-n`). While it is
possible to add this ignore rule to the link pattern itself, using `-i`
prevents that regular expression from becoming excessively complex and makes
debugging easier. This option can be used multiple times, a URL that match
any of them will be ignored.


### Cleaning URL query strings

Sometimes the source page has URLs with unwanted query string parameters,
like the [UTM trackers](https://en.wikipedia.org/wiki/UTM_parameters), or
multiple URLs differing only by irrelevant query string parameters and
pointing to the same destination page (and therefore confusing the duplicate
link detection). Option `--qs-remove-param` (shortcut `-Q`) may be used to
fix this. If the name of a parameter matches the regular expression given in
this option, that name/value pair will be removed from the URL query string.
This option may be repeated many times if necessary. Example: `-Q '^utm.+'`
(notice the anchor to only match prefixes).


### Excluding body elements

When generating a complete feed we may sometimes end up including some
unwanted elements from the source page into the item body, usually ads,
"related news" boxes, section headers, random images, distracting formatting,
unrelated links, etc. Some, but not all, of these noise sources can be
removed by carefully crafting XPath expressions or CSS selectors, but for the
cases where this is not possible, demand too much effort, or result in a
fragile solution, we can just remove the unwanted elements explicitly.

newslinkrss has tree command line options for this:

- Option `--body-remove-tag` (shortcut `-R`) will remove all occurrences of
  the given tag from the feed body and move their child elements to their
  parents. This can be used to remove formatting while preserving the inner
  text (e.g. `-R strong`) or to remove images from the body (with `-R img`,
  as "img" elements have no children);

- Option `--body-remove-xpath` (shortcut `-X`) will remove the elements
  given by a XPath expression **and** their children. This is a good way
  to remove banners, divs, etc. from the generated feed;

- Option `--body-remove-csss` (shortcut `-C`) will remove the elements given
  by a CSS Selector **and** their children. This is another way to remove
  banners, divs, etc. from the generated and more practical when selecting
  element by their CSS classes.

All three options can be repeated in the command line how many times as
necessary to express all required rules.


### Renaming tags and attributes

Sometimes we need to replace all occurrences of a HTML tag by another one
while preserving all attributes and structure; this is exceptionally common
when facing sites "infected" by Google AMP and exceptionally rare for
anything else. Option `--body-rename-tag` (shortcut: `-N`) exists for this
exact reason; assuming that we want to replace all instances of tag `amp-img`
by `img`, we can just do a `-N amp-img img`.

A similar use case appears when sites use lazy loading strategies for images.
It is a bit common to have the image "src" attribute pointing to a
placeholder image, sometimes inlined in a "data:" URL, while the URL for the
actual image is in another attribute, with a script loading the image only
after the user scrolls the page. Option `--body-rename-attr` can fix some of
these cases. Assuming that a site has all src attributes for img tags in the
attribute data-src, we can do `--body-rename-attr img data-src src`. Elements
that do not have the old attribute will not be changed. If the element
already has an attribute with the new name, it will be replaced. This
operation always runs **after** `--body-rename-tag` and sees the DOM as
already modified by it, so when renaming both tags and attributes, you must
look for the new tag name.


### Capturing categories

Every item of a feed can have a list of categories (the RSS name for tags or
topics) and they can be pretty valuable for sorting and filtering. By default,
newslinkrss tries to get them from Open Graph or quasi-standard metadata, but
some sites may only put them in some other element. Options
`--categories-from-xpath` and `--categories-from-csss` allow reading the
categories from the DOM using XPath and CSS Selectors, respectively.

For example, assume that a site has a list of tags in an element like this:

    <ul class="tags">
      <li><a href="/tag/essays">Essays</a></li>
      <li><a href="/tag/tolkien">Tolkien</a></li>
      <li><a href="/tag/the-silmarillion">The Silmarillion</a></li>
      <li><a href="/tag/unfinished-tales">Unfinished Tales</a></li>
    </ul>

We can easily get them using `--categories-from-csss 'ul.tags li a'`.

Sometimes list of tags can be trickier. Assume another site with a list of
topics in a single HTML meta tag similar to:

    <meta property="topics" content="essays, tolkien, the silmarillion, unfinished tales">

These categories are in an attribute, so we can use the XPath version to get
them, i.e. `--categories-from-xpath '//meta[@property="topics"]/@content'`.
The value, however, is a single string with no markup that allow us to get
the individual category names. For these cases we can use option
`--split-categories ","` (which applies to the results of both XPath and
CSSS versions) to split this string in a list of categories at every comma.

newslinkrss also does some simple cleanup for the list of categories
automatically (removing spaces, putting sensible limits to the number and
length of categories, etc.) to prevent some crazy situations.


### Handling request language options

Some sites change their rendering, response language, **date formats**, etc.
according to the preferred language information sent by the user's browser.
By default, newslinkrss uses the "LANG" environment variable to set this
language information (it is a bit of an optimization for the most common
case where the system language is the same as the one of the browser used for
debugging the options for a particular feed). To set a different one, you may
overwrite the LANG variable or use option `--lang`. The later option is more
flexible as it may be repeated to set several languages in order of preference
(e.g. `"--lang pt-BR --lang en-US --lang de-DE"`).

To not send any preferred language information to the server, independently
of one currently set for the system, clear the LANG variable for the
newslinkrss process invocation (e.g. `"LANG='' newslinkrss <other options>"`).


### Managing cookies

newslinkrss persists cookies among requests from the same program invocation
and forgets them once the program finishes; this is usually the most practical
choice for typical use cases, but there is an option `--no-cookies` to disable
all cookies if it becomes a problem for a particular source.

Conversely, sites may expect a particular cookies to be set to a specific
value, for example, to show news from a particular geographic region.
Command line option `--cookie` allows the user to define customized cookies
to handle these cases. This option supports the complete syntax defined by
[RFC 2965](https://www.rfc-editor.org/rfc/rfc2965.html), but a simple
`name=value` will work for the majority of use cases. Example:
`--cookie 'cookie-banner-consent-accepted=false'`. This option can be
repeated as many times as necessary.

If user-defined cookies are used together with option `--no-cookies`, the
target site will have access to them, but will not be able to change or
delete them (by overwriting or redefining the expiry date) or set new cookies.
This results in a read-only cookie jar that can be very useful for sites that
require cookies but use them to change behavior in unwanted ways after some
number of pages are processed.


### Setting arbitrary HTTP headers

Some sites may require unusual request options to work correctly. newslinkrss
has an option `--header` (shortcut: `-H`) to set any HTTP header for the
requests it sends. To use it, just pass the header in format `"NAME: VALUE"`
(e.g. `--header 'X-Clacks-Overhead: GNU Terry Pratchett'`). This should not
be a common requirement, however. It is also not recommended to use this
option for handling language preferences and cookies, as the dedicated
options `--lang` and `--cookie` will take care of the specific behavior of
these headers.


### Testing links

newslinkrss has an option `--test` that will skip the feed generation step
and just print the links and titles that were captured for a particular set
of options to stdout. That's a simple way to check if a pattern is working
as intended.


### Logging

Things **will** go wrong when experimenting with ugly regexes and confusing
XPath expressions or when fighting unexpected changes in some website's DOM.
Simplest way to see how newslinkrss is reacting internally is to increase
output verbosity with option `--log`; default value is "warning", but "info"
and "debug" will give more information like which element a XPath expression
found, if a regex matched or how some date was interpreted.

This information is always printed to stderr so it will not affect the feed
output written to stdout; when debugging in the terminal, remember to
redirect the output to a file with the shell or command line option `-o`.


### Error reporting

By default, newslinkrss writes exceptions and error messages to the feed
output itself. This is a very practical way to report errors to the user, as
this program is intended to work mostly on the background of the actual
user-facing application. It is possible to disable this behavior with option
`--no-exception-feed` (shortcut `-E`).

Notice that the program always return a non-zero status code on failures. Some
news readers (e.g. Liferea) won't process the output in these cases and
discard the feed entries with the error reports. You may need to override the
status code with something like `newslinkrss YOUR_OPTIONS; exit 0`.


### Writing output to a file

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

