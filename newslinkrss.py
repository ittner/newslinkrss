#!/usr/bin/python3


import requests
from html.parser import HTMLParser
import sys
import re
import logging
import PyRSS2Gen
import datetime
import dateutil.parser
import argparse
import urllib3


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0"
)


def _first_valid_attr_in_list(attrs, name):
    """Interpret an attribute list from HtmlParser.handle_starttag and get the
    value of the first attribute with the given name.  It should be only one
    but, of course, nobody can force people to only write sane HTML.
    """
    for itm in attrs:
        if (len(itm) > 1) and (itm[0] == name):
            return itm[1]
    return None


class CollectLinksParser(HTMLParser):
    def __init__(self, url_patt=None, max_items=None):
        HTMLParser.__init__(self)
        self.url_patt = url_patt
        self.max_items = max_items
        self.links = []
        self._last_link_text = None
        self._grab_link_text = False
        self._last_link = None

    def handle_starttag(self, tag, attrs):
        if (self.max_items != None) and (len(self.links) > self.max_items):
            return

        if tag == "a":
            href = _first_valid_attr_in_list(attrs, "href")
            # Try to noe follow the same link more than once. We need to
            # repeat this check later due to redirects.
            if (
                href
                and href not in self.links
                and (not self.url_patt or re.match(self.url_patt, href))
            ):
                self._last_link_text = []
                self._grab_link_text = True
                self._last_link = href

    def handle_data(self, data):
        if self._grab_link_text:
            self._last_link_text.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "a":
            link_text = ""
            if self._grab_link_text:
                self._grab_link_text = False
                link_text = "".join(self._last_link_text)
            if self._last_link:
                self.links.append((self._last_link, link_text))
            self._last_link = False


class CollectAttributesParser(HTMLParser):
    """A state machine that parses HTML from a web page and extract some
    useful attributes.

    The following properties are set with useful informaiton:
    title     - String with the page title or None
    base      - String with the base URL or None
    canonical - String with the Canonical URL for the page or None
    description - String with a best-guest for a description or None
    changed   - Datetime with a best-guest for the modification time or None
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self._title_lst = None
        self._in_head = False
        self.title = None
        self.base = None
        self.description = None
        self.canonical = None
        self.changed = None

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            # Will fail on nested heads, but who is insane enough to do this?!
            self._in_head = True

        if self._in_head and tag == "base":
            self.base = _first_valid_attr_in_list(attrs, "href")

        if self._in_head and (tag == "title") and (not self.title):
            self._title_lst = []
            self._title = None

        if self._in_head and tag == "link":
            # <link rel="xxxx" href="yyyy" />
            rel = _first_valid_attr_in_list(attrs, "rel")
            href = _first_valid_attr_in_list(attrs, "href")
            if rel == "canonical" and not self.canonical:
                self.canonical = href

        if self._in_head and tag.lower() == "meta":
            # <meta name="xxxx" content="yyyy" />
            # <meta property="xxxx" content="yyyy" />
            name = _first_valid_attr_in_list(attrs, "name")
            prop = _first_valid_attr_in_list(attrs, "property")
            content = _first_valid_attr_in_list(attrs, "content")

            # Attributes defined by the Open Graph Protocol: A lot of sites
            # which refuse to provide feeds have this nice attributes so their
            # contents appear nicely when linked on Facebook, Twitter and so.
            # These can provide a lot of useful information.

            if (
                prop == "article:published_time"
                or prop == "article:modified_time"
                or name == "article:published_time"
                or name == "article:modified_time"
            ):
                # Content is a date in ISO format.
                # <meta property="article:published_time" content="2020-09-13T20:00:00+00:00" />
                # <meta property="article:modified_time" content="2020-09-13T20:01:42+00:00" />
                try:
                    dt = dateutil.parser.parse(content)
                    if (not self.changed) or (self.changed < dt):
                        self.changed = dt
                except:
                    pass

            if prop == "og:url" and not self.canonical:
                # <meta property="og:url" content="xxxxx">
                self.canonical = content

            if prop in ("og:description", "twitter:description") or (
                name and name.lower() == "description"
            ):
                if len(content) > 8 and (
                    (not self.description) or (len(content) > len(self.description))
                ):
                    self.description = content

    def handle_data(self, data):
        if self._title_lst != None:
            self._title_lst.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False

        if tag == "title" and self._title_lst != None:
            self.title = "".join(self._title_lst)
            self._title_lst = None


def make_feed_item_follow(session, url, used_urls, args, link_text, base_attrs):
    try:
        req = session.get(url, timeout=args.http_timeout)
    except (
        urllib3.exceptions.ReadTimeoutError,
        requests.exceptions.ReadTimeout,
    ) as exc:
        # We should handle this somehow.
        return None

    if req.url in used_urls:
        return None

    used_urls.add(req.url)
    attr_parser = CollectAttributesParser()
    description = ""
    if req.status_code == 200:
        if attr_parser.description:
            description = attr_parser.description
        attr_parser.feed(req.text)
    else:
        description += "Page returned status code %d<br/>" % req.status_code

    # Give a meaningful title for this entry.
    clean_title = attr_parser.title or link_text or attr_parser.canonical or req.url
    if clean_title == base_attrs.title:
        # The title is the same as the one from base url, a typical thing
        # from horribly-designed news pages (and also happens on a
        # government site I need to consult from time to time), so
        # replace it with the contents of the link text, which should
        # give a bit more useful information for the reader.
        description += "Original title: %s<br/>" % clean_title
        clean_title = link_text

    description += "Link text: %s" % link_text
    clean_title = clean_title[: args.max_title_length]

    # Try to get a meaningful last modification date.
    date = None
    if attr_parser.changed:
        date = attr_parser.changed

    return PyRSS2Gen.RSSItem(
        title=clean_title,
        link=attr_parser.canonical or req.url,
        description=description,
        guid=PyRSS2Gen.Guid(req.url),
        pubDate=date,
    )


def make_feed_item_nofollow(url, used_urls, args, link_text, base_attrs):
    if url in used_urls:
        return None
    used_urls.add(url)
    clean_title = link_text[: args.max_title_length]
    return PyRSS2Gen.RSSItem(
        title=clean_title,
        link=url,
        description=link_text,
        guid=PyRSS2Gen.Guid(url),
    )


def make_feed(args):

    base_url = args.url
    session = requests.Session()
    session.headers = {
        "User-Agent": args.user_agent,
    }

    req = session.get(base_url, timeout=args.http_timeout)

    # Grab any links of interest from the base URL.
    link_grabber = CollectLinksParser(args.link_pattern, args.max_links)
    link_grabber.feed(req.text)
    base_links = link_grabber.links

    # Get relevant attributes from base URL.
    base_attrs = CollectAttributesParser()
    base_attrs.feed(req.text)

    # From now, we should use req.url because of redirects.
    session.headers["Referer"] = req.url
    request_base = base_attrs.base or req.url

    # URLs that where already processed (considering redirects).
    used_urls = set()

    rss_items = []
    for itm in base_links:
        new_url = requests.compat.urljoin(request_base, itm[0])
        if args.no_follow:
            ret_item = make_feed_item_nofollow(
                new_url, used_urls, args, itm[1], base_attrs
            )
        else:
            ret_item = make_feed_item_follow(
                session, new_url, used_urls, args, itm[1], base_attrs
            )
        if ret_item:
            rss_items.append(ret_item)

    title = base_attrs.title or base_url
    title = title[: args.max_title_length]

    rss = PyRSS2Gen.RSS2(
        title=title,
        link=base_url,
        description=base_attrs.description
        or base_attrs.title
        or base_attrs.canonical
        or base_url,
        lastBuildDate=datetime.datetime.now(),
        items=rss_items,
    )

    using_file = False
    fp = sys.stdout
    if args.output:
        fp = open(args.output, "w")
        using_file = True
    rss.write_xml(fp, encoding="utf-8")
    if using_file:
        fp.close()


def main():
    parser = argparse.ArgumentParser(
        description="Forcibly generate RSS feeds from generic sites"
    )

    parser.add_argument(
        "-n",
        "--max-links",
        action="store",
        default=50,
        type=int,
        help="Maximum number of links to follow.",
    )

    parser.add_argument(
        "-l",
        "--max-title-length",
        action="store",
        default=150,
        type=int,
        help="Maximum length of a feed title, in characters.",
    )

    parser.add_argument(
        "-p",
        "--link-pattern",
        action="store",
        default=".+",
        help="A regex to filter the URLs of links that the script will follow.",
    )

    parser.add_argument(
        "-N",
        "--no-follow",
        action="store_true",
        default=False,
        help=(
            "Do not follow links to generate the feed, just make them with "
            + "the information we can gather from the base URL. It is "
            + "faster and spares the target site from a lot of requests, "
            + "but we can't have any detailed information."
        ),
    )

    parser.add_argument(
        "-U",
        "--user-agent",
        action="store",
        default=DEFAULT_USER_AGENT,
        help="Use an alternate user agent. Default is '%s'" % DEFAULT_USER_AGENT,
    )

    parser.add_argument(
        "-t",
        "--http-timeout",
        action="store",
        default=2.0,
        type=float,
        help="Timeout for HTTP(S) requests, in seconds",
    )

    parser.add_argument(
        "-o",
        "--output",
        action="store",
        help="Output file (stdout if not given)",
    )

    parser.add_argument("url", action="store", help="Base URL to start downloading")

    args = parser.parse_args()
    # print(args)
    make_feed(args)


if __name__ == "__main__":
    main()
