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

import datetime
import logging
import re
import urllib
import dateutil.parser

logger = logging.getLogger(__name__)


def first_valid_attr_in_list(attrs, name):
    """Interpret an attribute list from HtmlParser.handle_starttag and get the
    value of the first attribute with the given name.  It should be only one
    but, of course, nobody can force people to only write sane HTML.
    """
    for itm in attrs:
        if (len(itm) > 1) and (itm[0] == name):
            return itm[1]
    return None


def normalize_rfc1766_lang_tag(loc):
    """RSS2 and HTML use RFC 1766 language codes (with an "-"), while Open
    Graph and "LANG" environment variable use a "_". This function fixes
    this difference and normalizes cases, spaces, etc.

    Notice that RFC 1766 is not case-sensitive, capitalization is just a
    convention. This function capitalizes country codes for easy reading.

    Returns None for (some) nonsensical values.
    """
    loc = loc.strip().lower().replace("_", "-")
    if len(loc) > 32:
        return None
    lst = loc.split("-", 1)
    if len(lst) == 2 and len(lst[1]) == 2:
        loc = lst[0] + "-" + lst[1].upper()
    return loc


def clean_url_query_string(rx_list, url):
    """Remove unwanted parameters from the URL query string.

    If the URL has a query string, remove all name/value pairs with names
    matching any of the regular expressions given in list 'rx_list'.
    Return the URL, possibly modified.
    """

    if not rx_list:
        return url

    u = urllib.parse.urlparse(url)
    query_lst = urllib.parse.parse_qsl(u.query, keep_blank_values=True)
    for rx in rx_list:
        nlst = []
        for itm in query_lst:
            if not re.match(rx, itm[0]):
                nlst.append(itm)
        query_lst = nlst

    query_str = urllib.parse.urlencode(query_lst) if query_lst else None
    new_url = urllib.parse.urlunparse(
        (u.scheme, u.netloc, u.path, u.params, query_str, u.fragment)
    )
    if new_url != url:
        logger.debug("query string cleanup: URL %s rewritten to %s", url, new_url)
    return new_url


def try_date_from_str(src, date_rx, date_fmt):
    rdate = None
    try:
        m = re.match(date_rx, src, re.M | re.S)
        if not m:
            return None
        date_txt = m.group(1)
        logger.debug(
            "date regex matched: src=%s, rx=%s, result=%s", src, date_rx, date_txt
        )
        if date_fmt:
            rdate = datetime.datetime.strptime(date_txt, date_fmt)
        else:
            # No date format, use dateutil's best guess.
            rdate = dateutil.parser.parse(date_txt)
    except (AttributeError, IndexError, ValueError, dateutil.parser.ParserError):
        logger.exception(
            "when parsing date with src=%s, fmt=%s, rx=%s", src, date_fmt, date_rx
        )

    return rdate


def get_regex_first_group(regex, srcstr):
    """If a regex with one capture group is given and it matches the source
    string, returns this group. Otherwise, returns None. This is used for a
    few "clean up" filters through the code.

    regex: regular expression string or None
    srcstr: source string or None
    """
    if regex and srcstr:
        m = re.match(regex, srcstr, re.M | re.S)
        if m:
            try:
                return m[1]
            except IndexError:
                pass
    return None


def get_top_level_logger():
    """Get a logger for the top level module name."""
    return logging.getLogger(__name__.split(".", 1)[0])
