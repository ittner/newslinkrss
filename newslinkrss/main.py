#!/usr/bin/env python3

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

import sys
import os
import datetime
import copy
import locale
import logging
import traceback
import http.cookiejar
import http.cookies
import urllib3

import dateutil.parser
import PyRSS2Gen
import requests

import lxml.html
import lxml.html.clean
import lxml.etree
import lxml.cssselect
import cssselect


from .defs import USER_LOG_LEVELS, DEFAULT_USER_AGENT
from . import cliargs
from . import parsers
from . import utils


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def set_log_level(args):
    if not args.log:
        return
    level = args.log.upper()
    if level not in USER_LOG_LEVELS:
        raise ValueError("Bad log level string %s" % args.log)
    numlevel = getattr(logging, level, None)
    if not isinstance(numlevel, int):
        raise ValueError("Log level %s not defined" % args.log)
    utils.get_top_level_logger().setLevel(numlevel)
    logger.info("Log level set to %d (%s)", numlevel, level)


def make_clean_title(args, title):
    clean_title = utils.get_regex_first_group(args.title_regex, title) or title
    return clean_title[: args.max_title_length]


def post_process_item_body(args, body):
    if args.body_remove_tag:
        lxml.etree.strip_tags(body, *args.body_remove_tag)
    if args.body_remove_xpath:
        for expr in args.body_remove_xpath:
            res = body.xpath(expr)
            if res:
                for elem in res:
                    logger.debug(
                        "body-remove-xpath %s matched: deleting element %s", expr, elem
                    )
                    elem.getparent().remove(elem)
    if args.body_remove_csss:
        for expr in args.body_remove_csss:
            res = body.cssselect(expr)
            if res:
                for elem in res:
                    logger.debug(
                        "body-remove-csss %s matched: deleting element %s", expr, elem
                    )
                    elem.getparent().remove(elem)
    if args.body_rename_tag:
        for old_tag, new_tag in args.body_rename_tag:
            for e in body.iter(old_tag):
                e.tag = new_tag
    if args.body_rename_attr:
        for tag, old_attr_name, new_attr_name in args.body_rename_attr:
            for e in body.iter(tag):
                if old_attr_name in e.attrib:
                    e.attrib[new_attr_name] = e.attrib[old_attr_name]
                    del e.attrib[old_attr_name]


def make_item_body(args, page_text, tree):
    bodyhtml = None
    try:
        lst = None
        if args.body_xpath:
            lst = tree.xpath(args.body_xpath)
        if (not lst) and args.body_csss:
            lst = tree.cssselect(args.body_csss)
        if not args.body_xpath and not args.body_csss:
            lst = tree.xpath("/html/body/*")
        if lst:
            if len(lst) > 1:
                body = lxml.html.Element("div")
                body.extend(lst)
            else:
                body = lst[0]
            body = copy.deepcopy(body)
            post_process_item_body(args, body)
            cleaner = lxml.html.clean.Cleaner()
            body = cleaner.clean_html(body)
            if isinstance(body, str):
                bodyhtml = body
            else:
                bodyhtml = lxml.html.tostring(
                    body, pretty_print=False, encoding="unicode"
                )
    except (
        lxml.etree.ParserError,
        cssselect.parser.SelectorSyntaxError,
        lxml.etree.XPathEvalError,
    ):
        logger.exception("When trying to get document body")

    return bodyhtml


def find_item_title(args, attr_parser, request, tree, anchor_text, base_attrs):
    title = None
    if not title and args.title_from_xpath and tree is not None:
        try:
            for res in tree.xpath(args.title_from_xpath):
                if res:
                    title = str(res)
                    break
        except lxml.etree.XPathEvalError:
            logger.exception("When trying to find title from XPath")
    if not title and args.title_from_csss and tree is not None:
        try:
            for res in tree.cssselect(args.title_from_csss):
                etext = res.text_content()
                if etext:
                    title = etext
                    break
        except (cssselect.parser.SelectorSyntaxError, lxml.etree.XPathEvalError):
            logger.exception("When trying to find title from CSS selector")
    if not title:
        title = attr_parser.title or anchor_text or attr_parser.canonical or request.url
    return make_clean_title(args, title)


def find_item_date(args, attr_parser, request, tree, anchor_text, orig_url):
    """Try to get a meaningful last modification date for an item.
    Only argument 'args' is required, everything else can be set to None and
    will be tried according to availability.
    """
    date = None
    if not date and args.date_from_xpath and tree is not None:
        try:
            for res in tree.xpath(args.date_from_xpath):
                logger.debug("date-from-xpath found candidate text: '%s'", res)
                date = utils.try_date_from_str(
                    res, args.xpath_date_regex, args.xpath_date_fmt
                )
                if date:
                    logger.debug("Found date from XPath %s", date)
                    break
        except lxml.etree.XPathEvalError:
            pass
    if not date and args.date_from_csss and tree is not None:
        try:
            for res in tree.cssselect(args.date_from_csss):
                etext = res.text_content()
                if etext is None:
                    continue
                logger.debug("date-from-csss found candidate text: '%s'", etext)
                date = utils.try_date_from_str(
                    etext, args.csss_date_regex, args.csss_date_fmt
                )
                if date:
                    logger.debug("Found date from CSS Selector %s", date)
                    break
        except (cssselect.parser.SelectorSyntaxError, lxml.etree.XPathEvalError):
            logger.exception("When handling a CSS selector")
    if not date and args.date_from_text and anchor_text:
        date = utils.try_date_from_str(
            anchor_text, args.date_from_text, args.text_date_fmt
        )
    if not date and args.date_from_url and orig_url:
        date = utils.try_date_from_str(orig_url, args.date_from_url, args.url_date_fmt)
    if not date and attr_parser and attr_parser.changed:
        date = attr_parser.changed
    if not date and request and ("Last-Modified" in request.headers):
        last_mod = request.headers["Last-Modified"]
        try:
            date = dateutil.parser.parse(last_mod)
            logger.debug(
                "No date was found but an HTTP header 'Last-Modified' was. "
                "Assuming its value %s as the date %s",
                last_mod,
                date,
            )
        except dateutil.parser.ParserError:
            logger.exception('Invalid date in HTTP header "Last-modified"')
    return date


def find_item_author(args, attr_parser, tree):
    """Try to get the author of an item.

    Finds the author from explicitly requested elements and falls back to
    metadata if these are not available.
    """
    author = None
    if not author and args.author_from_xpath and tree is not None:
        try:
            for res in tree.xpath(args.author_from_xpath):
                if res:
                    author = utils.get_regex_first_group(
                        args.xpath_author_regex, str(res)
                    )
                    break
        except lxml.etree.XPathEvalError:
            logger.exception("When trying to find author from XPath")

    if not author and args.author_from_csss and tree is not None:
        try:
            for res in tree.cssselect(args.author_from_csss):
                text = res.text_content()
                if text is not None:
                    author = utils.get_regex_first_group(
                        args.csss_author_regex, str(text)
                    )
                    break
        except (cssselect.parser.SelectorSyntaxError, lxml.etree.XPathEvalError):
            logger.exception("When trying to find author from a CSS selector")
    return author or attr_parser.author


def find_item_categories(args, attr_parser, tree):
    """Try to get the list of categories of an item.

    Finds the categories from explicitly requested elements or falls back to
    metadata if these are not available.
    """
    categories = []

    if not categories and args.categories_from_xpath and tree is not None:
        try:
            categories = [
                str(res) for res in tree.xpath(args.categories_from_xpath) if res
            ]
        except lxml.etree.XPathEvalError:
            logger.exception("When trying to find categories from XPath")

    if not categories and args.categories_from_csss and tree is not None:
        try:
            categories = [
                res.text_content()
                for res in tree.cssselect(args.categories_from_csss)
                if res is not None
            ]
        except (cssselect.parser.SelectorSyntaxError, lxml.etree.XPathEvalError):
            logger.exception("When trying to find categories from a CSS selector")

    if not categories and attr_parser.tags:
        categories = attr_parser.tags

    if not categories and attr_parser.section:
        categories = [attr_parser.section]

    if categories and args.split_categories:
        new_categories = []
        for curr_categ in categories:
            split_categs = curr_categ.split(args.split_categories)
            for tmp in split_categs:
                new_categories.append(tmp)
        categories = new_categories

    # Clean-up bogus categories (too long, empty ...)
    valid_categories = []
    for categ in categories:
        categ = categ.strip()[:128].strip()
        if categ != "":
            valid_categories.append(categ)
    if len(valid_categories) > 50:
        logger.warning("Item with %d categories! Pruning.", len(valid_categories))
        valid_categories = valid_categories[:50]

    return valid_categories


def do_session_http_get(session, url, timeout=2, max_len_kb=0, encoding=None):
    """Do a HTTP(S) GET request for the URL in the context of session,
    subjected to the limits imposed for timeout (in seconds), max_len_kb
    (in kilobytes) and using the given encoding to return the resulting page
    as a *text* string.

    Returns the text and the request object. For exceptions, the text will be
    None and more error information must be inferred from the request object.
    """
    page_text = None
    req = None
    try:
        logger.info("Following URL %s", url)
        req = session.get(url, timeout=timeout, stream=True)
        logger.debug("Request returned status code: %d", req.status_code)
        logger.debug("Request headers: %s", req.request.headers)
        logger.debug("Response headers: %s", req.headers)
        logger.debug("Cookies: %s", session.cookies)
        if encoding:
            req.encoding = encoding
        chunk_size = 1024 * min(100, max_len_kb)
        if req.status_code == 200:
            page_text = ""
            consumed_size = 0
            for chunk in req.iter_content(chunk_size=chunk_size, decode_unicode=True):
                if consumed_size >= 1024 * max_len_kb:
                    break
                consumed_size += len(chunk)
                if type(chunk) == bytes:
                    logger.warning("Unexpected binary return, trying to fix.")
                    chunk = chunk.decode("utf-8")
                page_text += chunk
    except (
        urllib3.exceptions.ReadTimeoutError,
        requests.exceptions.Timeout,
    ):
        logger.exception("When downloading %s", url)
        # We should handle this somehow.
        page_text = None
    finally:
        if req:
            req.close()
    return page_text, req


def make_feed_item_follow(session, url, used_urls, args, link_text, base_attrs):
    page_text, req = do_session_http_get(
        session, url, args.http_timeout, args.max_page_length, args.encoding
    )
    if not page_text:
        return None
    if req.url in used_urls:
        return None

    used_urls.add(req.url)
    attr_parser = parsers.CollectAttributesParser()
    description = ""
    if req.status_code == 200:
        attr_parser.feed(page_text)
    else:
        description += "Page returned status code %d<br/>" % req.status_code
    if attr_parser.description:
        description = attr_parser.description
    else:
        description = link_text

    item_url = attr_parser.canonical or req.url
    tree = None
    try:
        tree = lxml.html.document_fromstring(page_text)
    except lxml.etree.ParserError:
        logger.exception(
            "Failed to parse document, some information won't be available"
        )

    title = find_item_title(args, attr_parser, req, tree, link_text, base_attrs)
    date = find_item_date(args, attr_parser, req, tree, link_text, item_url)
    if args.require_dates and not date:
        # We need a date but the page have none. Skip this entry.
        logger.info("Ignoring feed entry without date %s", url)
        return None
    author = find_item_author(args, attr_parser, tree)
    if args.with_body and tree is not None:
        bodyhtml = make_item_body(args, page_text, tree)
        if bodyhtml:
            description = bodyhtml
    categories = find_item_categories(args, attr_parser, tree)
    if date:
        # PyRSS2Gen ignores tzinfos and requires the date to be explicitly in UTC.
        date = datetime.datetime.fromtimestamp(date.timestamp(), datetime.timezone.utc)
    return PyRSS2Gen.RSSItem(
        title=title,
        link=item_url,
        author=author,
        description=description,
        guid=PyRSS2Gen.Guid(req.url),
        categories=categories,
        pubDate=date,
    )


def make_feed_item_nofollow(url, used_urls, args, link_text, base_attrs):
    if url in used_urls:
        return None
    used_urls.add(url)
    clean_title = make_clean_title(args, link_text)
    date = find_item_date(args, None, None, None, link_text, url)
    # We need a date but the page have none. Skip this entry.
    if args.require_dates and not date:
        logger.info("Ignoring feed entry without date %s", url)
        return None

    if date:
        # PyRSS2Gen ignores tzinfos and requires the date to be explicitly in UTC.
        date = datetime.datetime.fromtimestamp(date.timestamp(), datetime.timezone.utc)
    return PyRSS2Gen.RSSItem(
        title=clean_title,
        link=url,
        description=link_text,
        guid=PyRSS2Gen.Guid(url),
        pubDate=date,
    )


def write_feed(rss, args):
    if args.output:
        logger.debug("Writing feed to %s", args.output)
        with open(args.output, "w", encoding="utf-8") as fp:
            rss.write_xml(fp, encoding="utf-8")
    else:
        logger.debug("Writing feed to stdout")
        rss.write_xml(sys.stdout, encoding="utf-8")


def make_exception_feed(exc, args=None):
    logger.warning("Writing exception information to an exception feed.")
    cmdline = " ".join(sys.argv)
    stack_trace = traceback.format_exc()
    msg = (
        "An error occurred when generating this feed."
        + "<br/> <br/>"
        + "<strong>Command line:</strong> <code>"
        + cmdline
        + "</code>"
        + "<br /><br />"
        + "<strong>Exception:</strong> "
        + str(exc)
        + "<br /><br />"
        + "<strong>Stack trace:</strong> <pre>"
        + stack_trace
        + "\n</pre>"
    )

    itm = PyRSS2Gen.RSSItem(
        title="newslinkrss error: " + str(exc)[:64],
        link="data:" + cmdline,
        description=msg,
    )

    rss = PyRSS2Gen.RSS2(
        title="Error: " + cmdline,
        link=args.urls[0] if args else None,
        description="Failed to generate feed.",
        # PyRSS2Gen ignores tzinfos and requires the date to be explicitly in UTC.
        lastBuildDate=datetime.datetime.now(datetime.timezone.utc),
        items=[itm],
    )
    write_feed(rss, args)


def test_links(link_grabber, args):
    args.no_exception_feed = True
    if link_grabber.limit_reached:
        print("# Limit of %d links was reached." % (link_grabber.max_items))
    for itm in link_grabber.links:
        print("- " + itm[0])
        if itm[1] and itm[1] != "":
            print("    text: " + itm[1])
        if args.date_from_url:
            date = utils.try_date_from_str(
                itm[0], args.date_from_url, args.url_date_fmt
            )
            if date:
                print("    url-date:  " + str(date))
        if itm[1] and args.date_from_text:
            date = utils.try_date_from_str(
                itm[1], args.date_from_text, args.text_date_fmt
            )
            if date:
                print("    text-date: " + str(date))
        print("")


def get_start_page(args, session, base_attrs, link_grabber, base_url):
    logger.info("Downloading start URL %s", base_url)
    page_content, req = do_session_http_get(
        session, base_url, args.http_timeout, args.max_first_page_length, args.encoding
    )

    base_attrs.reset_parser()
    base_attrs.feed(page_content)

    link_grabber.reset_parser()
    link_grabber.base_url = base_attrs.base or req.url
    link_grabber.feed(page_content)

    return req


def make_accept_language_header(args):
    """Build a acceptable Accept-Language HTTP header."""
    langs = []
    if args.lang:
        for lang in args.lang:
            normalized = utils.normalize_rfc1766_lang_tag(lang)
            langs.append(normalized if normalized else lang)

    if not langs:
        locale_name = os.getenv("LANG")
        if locale_name:
            locale_name = locale_name.split(".")[0]
            normalized = utils.normalize_rfc1766_lang_tag(locale_name)
            if normalized:
                langs.append(normalized)

    q = 0.8
    qualified = []
    for lang in langs:
        qualified.append("%s;q=%.01f" % (lang, q))
        if q > 0.3:
            q -= 0.2

    if qualified:
        return ",".join(qualified)
    else:
        return None


def make_default_http_headers(args):
    headers = {
        "User-Agent": args.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "TE": "trailers",
    }

    accept_language = make_accept_language_header(args)
    if accept_language:
        headers["Accept-Language"] = accept_language

    if args.header:
        for header_value in args.header:
            pair = header_value.split(":", 1)
            value = pair[1].lstrip() if len(pair) == 2 else ""
            headers[pair[0].strip()] = value

    return headers


class ControlledCookiePolicy(http.cookiejar.DefaultCookiePolicy):
    """A cookie policy with a simple read-only/read-write switch."""

    def __init__(self):
        self.read_only = False
        http.cookiejar.DefaultCookiePolicy.__init__(self)

    def set_ok(self, cookie, request):
        if self.read_only:
            return False
        return http.cookiejar.DefaultCookiePolicy.set_ok(self, cookie, request)


def set_cookie_options_for_session(session, args):
    """Set the cookie options for the session."""

    policy = ControlledCookiePolicy()
    session.cookies = requests.cookies.RequestsCookieJar(policy=policy)

    if args.cookie:
        policy.read_only = False
        for cookie_spec in args.cookie:
            c = http.cookies.SimpleCookie(cookie_spec)
            logger.info("New custom cookie parsed as %s", repr(c))
            for key, value in c.items():
                session.cookies[key] = value

    policy.read_only = bool(args.no_cookies)


def make_feed(args):
    session = requests.Session()
    session.headers = make_default_http_headers(args)
    set_cookie_options_for_session(session, args)

    base_attrs = parsers.CollectAttributesParser()
    link_grabber = parsers.CollectLinksParser(
        args.link_pattern, args.ignore_pattern, args.max_links, None
    )
    link_grabber.qs_cleanup_rx_list = args.qs_remove_param

    for curr_url in args.urls:
        req = get_start_page(args, session, base_attrs, link_grabber, curr_url)
        if link_grabber.limit_reached:
            break
        if not "Referer" in session.headers:
            session.headers["Referer"] = req.url

    # Handle fetch metadata headers according to
    # https://w3c.github.io/webappsec-fetch-metadata/
    if "Sec-Fetch-Site" in session.headers:
        session.headers["Sec-Fetch-Site"] = "same-origin"

    if args.test:
        test_links(link_grabber, args)
        return

    # URLs that where already processed (considering redirects).
    used_urls = set()
    base_links = link_grabber.links

    rss_items = []
    for itm in base_links:
        if args.follow:
            ret_item = make_feed_item_follow(
                session, itm[0], used_urls, args, itm[1], base_attrs
            )
        else:
            ret_item = make_feed_item_nofollow(
                itm[0], used_urls, args, itm[1], base_attrs
            )
        if ret_item:
            rss_items.append(ret_item)

    title = base_attrs.title or ", ".join(args.urls)
    title = title[: args.max_title_length]

    rss = PyRSS2Gen.RSS2(
        title=args.title or title,
        link=args.urls[0],
        description=base_attrs.description
        or base_attrs.title
        or base_attrs.canonical
        or ", ".join(args.urls),
        # PyRSS2Gen ignores tzinfos and requires the date to be explicitly in UTC.
        lastBuildDate=datetime.datetime.now(datetime.timezone.utc),
        language=base_attrs.language,
        items=rss_items,
    )
    write_feed(rss, args)


def set_locale(args):
    """Set locale for this application, using both the default "best effort"
    approach and the explicit locale from command line.
    """

    if args.locale:
        locale.setlocale(locale.LC_TIME, args.locale)
        return

    loc = None
    candidates = ["LC_ALL", "LC_TIME", "LANG"]
    for cand in candidates:
        loc = os.getenv(cand)
        if loc:
            break
    if loc:
        try:
            locale.setlocale(locale.LC_TIME, loc)
        except locale.Error:
            logger.warning("Ignoring wrong/unknown locale %s", loc)


def main():
    parser = cliargs.make_parser()
    args = parser.parse_args()
    set_log_level(args)
    set_locale(args)

    logger.debug("URL accept pattern: %s", args.link_pattern)
    logger.debug("URL ignore pattern: %s", args.ignore_pattern)

    try:
        make_feed(args)
    except Exception as exc:
        logger.exception("Unhandled exception")
        if args.no_exception_feed:
            raise exc
        make_exception_feed(exc, args)
        return 1
    return 0
