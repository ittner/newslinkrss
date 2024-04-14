#
# newslinkrss - RSS feed generator for generic sites
# Copyright (C) 2020  Alexandre Erwin Ittner <alexandre@ittner.com.br>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#


import logging
from html.parser import HTMLParser
import re

import dateutil.parser
import requests

from . import utils


logger = logging.getLogger(__name__)


class CollectLinksParser(HTMLParser):
    def __init__(self, url_patt=None, ignore_patt=None, max_items=None, base_url=None):
        HTMLParser.__init__(self)
        self.url_patt = url_patt
        self.ignore_patt = ignore_patt
        self.max_items = max_items
        self.base_url = base_url
        self.links = []
        self.limit_reached = False

        # List of regexes with parameters to strip from URL query strings.
        self.qs_cleanup_rx_list = []

        self._found_links = set()
        self._last_link_text = None
        self._grab_link_text = False
        self._last_link = None

    def reset_parser(self):
        """Resets the parser state, but still keeps found links, etc."""
        self._last_link_text = None
        self._grab_link_text = False
        self._last_link = None

    def handle_starttag(self, tag, attrs):
        if (self.max_items is not None) and (len(self.links) >= self.max_items):
            if not self.limit_reached:
                logger.warning("limit of %d links reached", self.max_items)
            self.limit_reached = True
            return

        if tag == "a":
            href = utils.first_valid_attr_in_list(attrs, "href")
            if not href:
                return

            href = href.split("#", 2)[0]  # Strip URL fragment.
            if self.base_url:
                href = requests.compat.urljoin(self.base_url, href)
            href = utils.clean_url_query_string(self.qs_cleanup_rx_list, href)

            # Try to noe follow the same link more than once. We need to
            # repeat this check later due to redirects.
            if href not in self._found_links and self.test_url_patterns(href):
                self._last_link_text = []
                self._grab_link_text = True
                self._last_link = href

    def test_url_patterns(self, url):
        """Return True if url is valid for visiting (i.e. matches at least one
        accept pattern and do not match any ignore pattern.
        """

        if self.ignore_patt and any(re.match(patt, url) for patt in self.ignore_patt):
            return False
        return not self.url_patt or any(re.match(patt, url) for patt in self.url_patt)

    def handle_data(self, data):
        if self._grab_link_text:
            text = data.strip()
            if text != "":
                self._last_link_text.append(text)

    def handle_endtag(self, tag):
        if tag == "a":
            link_text = ""
            if self._grab_link_text:
                self._grab_link_text = False
                link_text = " ".join(self._last_link_text)
            if self._last_link and self._last_link not in self._found_links:
                self._found_links.add(self._last_link)
                self.links.append((self._last_link, link_text))
                logger.info("New link added: %s %s", self._last_link, link_text)
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
    author    - String with a best-guest for the author name or None
    section   - Section where article was published or None
    tags      - Tags attached to the article
    language  - Language code (e.g. en-US) or None
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
        self.author = None
        self.section = None
        self.tags = []
        self.language = None

        # True is a temporary language was found in element <html>. It will
        # be used only until another one is found because too many sites
        # have nonsensical values in it.
        self._html_locale = False

    def reset_parser(self):
        """Reset current parser state, but keep collected data."""
        self._title_lst = None
        self._in_head = False
        self._html_locale = False

    def handle_starttag(self, tag, attrs):
        if tag == "html":
            lang = utils.first_valid_attr_in_list(attrs, "lang")
            if lang and not self.language:
                self.language = utils.normalize_rfc1766_lang_tag(lang)
                self._html_locale = True

        if tag == "head":
            # Will fail on nested heads, but who is insane enough to do this?!
            self._in_head = True

        if self._in_head and tag == "base":
            self.base = utils.first_valid_attr_in_list(attrs, "href")

        if self._in_head and (tag == "title") and (not self.title):
            self._title_lst = []

        if self._in_head and tag == "link":
            # <link rel="xxxx" href="yyyy" />
            rel = utils.first_valid_attr_in_list(attrs, "rel")
            href = utils.first_valid_attr_in_list(attrs, "href")
            if rel == "canonical" and not self.canonical:
                self.canonical = href

        if self._in_head and tag.lower() == "meta":
            # <meta name="xxxx" content="yyyy" />
            # <meta property="xxxx" content="yyyy" />
            name = utils.first_valid_attr_in_list(attrs, "name")
            prop = utils.first_valid_attr_in_list(attrs, "property")
            content = utils.first_valid_attr_in_list(attrs, "content")
            if name:
                name = name.lower()
            if prop:
                prop = prop.lower()
            # Many sites just mix "name" and "property".
            name_or_prop = name or prop

            # Attributes defined by the Open Graph Protocol: A lot of sites
            # which refuse to provide feeds have this nice attributes so their
            # contents appear nicely when linked on Facebook, Twitter and so.
            # These can provide a lot of useful information.

            if name_or_prop in (
                "article:published_time",
                "article:modified_time",
                "og:updated_time",
            ):
                # Content is a date in ISO format.
                # <meta property="article:published_time" content="2020-09-13T20:00:00+00:00" />
                # <meta property="article:modified_time" content="2020-09-13T20:01:42+00:00" />
                try:
                    dt = dateutil.parser.parse(content)
                    if (not self.changed) or (self.changed < dt):
                        self.changed = dt
                        logger.debug("Found new changed date %s", dt)
                except:
                    logger.exception("When parsing changed date")

            if prop == "og:url" and not self.canonical:
                # <meta property="og:url" content="xxxxx">
                self.canonical = content

            if name_or_prop in ("og:description", "twitter:description", "description"):
                if (
                    content
                    and len(content) > 8
                    and (
                        (not self.description) or (len(content) > len(self.description))
                    )
                ):
                    self.description = content

            if not self.author and name_or_prop in ("author", "article:author"):
                self.author = content

            if name_or_prop == "article:tag":
                if content and content not in self.tags:
                    self.tags.append(content)

            if (name_or_prop == "article:section") and content:
                self.section = content

            if (name_or_prop == "og:locale") and content:
                lang = utils.normalize_rfc1766_lang_tag(content)
                if self._html_locale and self.language:
                    self.language = lang
                    self._html_locale = False
                elif not self.language:
                    self.language = lang

    def handle_data(self, data):
        if self._title_lst is not None:
            self._title_lst.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False

        if tag == "title" and self._title_lst is not None:
            self.title = "".join(self._title_lst)
            self._title_lst = None
