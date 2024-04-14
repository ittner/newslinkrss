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


import argparse
import logging

from .defs import USER_LOG_LEVELS, DEFAULT_USER_AGENT


logger = logging.getLogger(__name__)


def make_parser():
    """Make the command line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "newslinkrss generates RSS feeds for websites that do not "
            "provide their own. This is done by loading URLs and collecting "
            "links that matches patterns to the of feed items, given as "
            "regular expressions, and optionally visiting them to get more "
            "details and even processing the target pages with XPath and CSS "
            "Selectors if required. It basically works as a purpose specific "
            "crawler or scraper."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-n",
        "--max-links",
        action="store",
        default=50,
        metavar="NUMBER",
        type=int,
        help="Maximum number of links to follow.",
    )

    parser.add_argument(
        "-l",
        "--max-title-length",
        action="store",
        default=150,
        metavar="NUMBER",
        type=int,
        help="Maximum length of a feed title, in characters.",
    )

    parser.add_argument(
        "-p",
        "--link-pattern",
        action="append",
        default=None,
        metavar="REGEX",
        help=(
            "A regular expression to filter the URLs of links that the "
            "script will follow or capture to generate every feed item. "
            "This option can be used multiple times, a URL matching any "
            "expression will be accepted."
        ),
    )

    parser.add_argument(
        "-i",
        "--ignore-pattern",
        action="append",
        default=None,
        metavar="REGEX",
        help=(
            "A regular expression used to ignore URLs even if they match "
            "--link-pattern. This may be used to prevent unwanted items "
            "from appearing in the feed while keeping the link pattern "
            "simpler (i.e. no need to make that regex excessively complex "
            "by embedding the ignored patterns in it). This option can be "
            "used multiple times, a URL matching any expression will be "
            "ignored."
        ),
    )

    parser.add_argument(
        "-T",
        "--title",
        action="store",
        metavar="ALTERNATE_TITLE",
        default=None,
        help=(
            "Use this alternate title for the feed instead of the one "
            "discovered from the URL."
        ),
    )

    parser.add_argument(
        "--title-regex",
        action="store",
        default=None,
        metavar="REGEX",
        help=(
            "Use this regular expression to select only part of the original "
            "title as the item title. This can be used to remove redundant "
            "or irrelevant parts from the title.Regex must have at least one "
            "group and, if it matches, the content of the first group will "
            "be used as the title. If it does not match, the original title "
            "will be used."
        ),
    )

    parser.add_argument(
        "--title-from-xpath",
        action="store",
        default=None,
        metavar="XPATH_EXPRESSION",
        help=(
            "Capture the title from the element given by this XPath "
            "expression in the target document instead of using the usual "
            "document title. This may be useful for sites where the title is "
            "too polluted but there is an alternate element with a "
            "descriptive title readily available. This requires the document "
            "body, so it will only work if used with option --follow."
        ),
    )

    parser.add_argument(
        "--title-from-csss",
        action="store",
        default=None,
        metavar="CSS_SELECTOR",
        help=(
            "Capture the title from the element given by this CSS Selector "
            "in the target document instead of using the usual document "
            "title. This may be useful for sites where the title is too "
            "polluted but there is an alternate element with a descriptive "
            "title readily available. This requires the document body, so "
            "it will only work if used with option --follow."
        ),
    )

    parser.add_argument(
        "-A",
        "--date-from-url",
        action="store",
        default=None,
        metavar="REGEX",
        help=(
            "Interpret date and time of the feed item from the URL. This can "
            "spare us from downloading the entire target page in some sites "
            "and blogs that put a parseable date in its URL (e.g.: "
            '"https://example.org/posts/2020/09/22/happy-hobbit-day/") or '
            "be our only option if the website provides no date at all. The "
            "argument is a regular expression containing a single capture "
            "group that extracts the date (or date and time) from the URL. "
            "For the previous example, this regex would be "
            '"/posts/(\\d{4}/\\d{2}/\\d{2})/", which will return "2020/09/22"'
            "to be interpreted as year/month/day. For other formats, see "
            "option --url-date-fmt. The date/time will be used only as it "
            "returns at least the year, month and day (this script will use "
            "hours and minutes if they are available, but it is very rare "
            "for sites to put this information in URLs). "
            "When using --follow, the date detected from this option will "
            "only be used if the page provides no date of its own. "
            "KNOWN BUG: Currently the code assumes that the date is in the "
            "same timezone as the system running this script."
        ),
    )

    parser.add_argument(
        "--url-date-fmt",
        action="store",
        default="%Y/%m/%d",
        metavar="DATE_FORMAT",
        help=(
            "The date format to be used with option --date-from-url. This "
            "value is a format string as specified by strftime(), and *must* "
            "contain at least the formats for year, month and date. This "
            "script can use hours and minutes if they are available, but "
            "it is very rare for sites to put this information in URLs. "
            "If this format is empty, the code will try to interpret it as "
            "some common date/time formats."
        ),
    )

    parser.add_argument(
        "-a",
        "--date-from-text",
        action="store",
        default=None,
        metavar="REGEX",
        help=(
            "Interpret date and time of the feed item from the link text. "
            "This can spare us from downloading the entire target page in "
            "some sites and blogs that put a parseable its links or be our "
            "only option if the website provides no date at all. The argument "
            "is a regular expression containing a single capture group that "
            "extracts the date (or date and time) from the text, and the "
            "resulting capture will be interpreted according to the format "
            "given in option --text-date-fmt (unlike --url-date-fmt, there "
            "is no commonly used format, so the default will probably not "
            "work for you). The date/time will be used only as it returns at "
            "least the year, month and day. "
            "When using --follow, the date detected from this option will "
            "only be used if the page provides no date of its own. "
            "KNOWN BUG: Currently the code assumes that the date is in the "
            "same timezone as the system running this script."
        ),
    )

    parser.add_argument(
        "--text-date-fmt",
        action="store",
        default=None,
        metavar="DATE_FORMAT",
        help=(
            "The date format to be used with option --text-from-url. This "
            "value is a format string as specified by strftime(), and *must* "
            "contain at least the formats for year, month and date. "
            "If this format is not given or empty, the code will try to "
            "interpret it as some common date/time formats."
        ),
    )

    parser.add_argument(
        "--date-from-xpath",
        action="store",
        default=None,
        metavar="XPATH_EXPRESSION",
        help=(
            "Use a XPath expression to get the text containing the date "
            "and time the page was published. This allows picking the "
            "date from any element present in the page, but at the cost "
            "of some complexity and *requires* downloading the candidate "
            "pages by passing option --follow (--max-page-length can "
            "also be used to limit the amount of downloaded data, but "
            "if the required element is not in it, the date won't be "
            "available). "
            "Notice that options --date-from-xpath, --xpath-date-regex, "
            "and --xpath-date-fmt work together as a pipeline, first "
            "getting the text from elements in the page, then optionally "
            "selecting a substring from it, and then parsing it as date "
            "and time. "
            "Example: the XPath expression '//span[@class=\"published-date\"]/@datetime' "
            'will pick the date from attribute "datetime" from the first '
            '"span" tag that has an attribute named "class" with value '
            'equal to "published-date".'
        ),
    )

    parser.add_argument(
        "--xpath-date-regex",
        action="store",
        default="(.+)",
        metavar="REGEX",
        help=(
            "A regular expression containing a single group that is used "
            "to select the part of the text returned by --date-from-xpath, "
            "that will then be parsed as a date using the format given "
            "by option --xpath-date-fmt. This option may be useful when "
            "the XPath expression required to select the exact text just "
            "becomes too complicated or verbose and doing it in two steps "
            "just becomes easier. This option can be safely omitted if "
            "this step is not necessary, as the default regex select the "
            "complete input. "
            "Notice that options --date-from-xpath, --xpath-date-regex, "
            "and --xpath-date-fmt work together as a pipeline, first "
            "getting the text from elements in the page, then optionally "
            "selecting a substring from it, and then parsing it as date "
            "and time. "
        ),
    )

    parser.add_argument(
        "--xpath-date-fmt",
        action="store",
        default=None,
        metavar="DATE_FORMAT",
        help=(
            "The date format to be used with option --date-from-xpath. "
            "This value is a format string as specified by strftime(), and "
            "*must* contain at least the formats for year, month and date. "
            "Notice that options --date-from-xpath, --xpath-date-regex, "
            "and --xpath-date-fmt work together as a pipeline, first "
            "getting the text from elements in the page, then optionally "
            "selecting a substring from it, and then parsing it as date "
            "and time. If this format is not given or empty, the code "
            "will try to interpret it as some common date/time formats."
        ),
    )

    parser.add_argument(
        "--date-from-csss",
        action="store",
        default=None,
        metavar="CSS_SELECTOR",
        help=(
            "Use a CSS Selector to get the text containing the date and "
            "time the page was published. This allows picking the date "
            "from any element present in the page, but at the cost of some "
            "complexity and *requires* downloading the candidate pages by "
            "passing option --follow (--max-page-length can also be used "
            "to limit the amount of downloaded data, but if the required "
            "element is not in it, the date won't be available). "
            "Notice that options --date-from-csss, --csss-date-regex, and "
            "--csss-date-fmt work together as a pipeline, first getting the "
            "text from elements in the page, then optionally selecting a "
            "substring from it, and then parsing it as date and time. "
            "Example: the CSS Selector 'span.published-date' will pick the "
            "date from the inner text from the first 'span' tag with class "
            "'published-date' that generates a valid date according to the "
            "regular expression given in option --csss-date-regex and date "
            "format from option --csss-date-fmt."
        ),
    )

    parser.add_argument(
        "--csss-date-regex",
        action="store",
        default="(.+)",
        metavar="REGEX",
        help=(
            "A regular expression containing a single group that is used "
            "to select the part of the text returned by --date-from-csss, "
            "that will then be parsed as a date using the format given "
            "by option --csss-date-fmt. This option may be useful when "
            "the CSS Selector can not select the exact text with the date. "
            "This option can be safely omitted if this step is not "
            "necessary, as the default regex select the complete input. "
            "Notice that options --date-from-csss, --csss-date-regex, "
            "and --csss-date-fmt work together as a pipeline, first "
            "getting the text from elements in the page, then optionally "
            "selecting a substring from it, and then parsing it as date "
            "and time. "
        ),
    )

    parser.add_argument(
        "--csss-date-fmt",
        action="store",
        default=None,
        metavar="DATE_FORMAT",
        help=(
            "The date format to be used with option --date-from-csss. "
            "This value is a format string as specified by strftime(), and "
            "*must* contain at least the formats for year, month and date. "
            "Notice that options --date-from-csss, --csss-date-regex, and "
            "--csss-date-fmt work together as a pipeline, first getting "
            "the text from elements in the page, then optionally selecting "
            "a substring from it, and then parsing it as date and time. If "
            "this format is not given or empty, the code will try to "
            "interpret it as some common date/time formats."
        ),
    )

    parser.add_argument(
        "--author-from-xpath",
        action="store",
        default=None,
        metavar="XPATH_EXPRESSION",
        help=(
            "Use a XPath expression to get the author of an item, allowing to "
            "find authors from any element in the page, which is particularly "
            "useful for sites that do not cite them in the standard metadata. "
            "Notice that options --author-from-xpath and --xpath-author-regex "
            "work together as a pipeline, first getting the author name "
            "from the page and the second filtering optionally selecting a "
            "substring from it."
        ),
    )

    parser.add_argument(
        "--xpath-author-regex",
        action="store",
        default="(.+)",
        metavar="REGEX",
        help=(
            "A regular expression containing a single capture group that "
            "will be used to select the part of the text returned by "
            "--author-from-xpath and then used as the author name. Example: "
            "'by\\s+(.+)' will remove the 'by ' prefix from a byline, "
            "returning only the name."
        ),
    )

    parser.add_argument(
        "--author-from-csss",
        action="store",
        default=None,
        metavar="CSS_SELECTOR",
        help=(
            "Use a CSS Selector to get the author of an item, allowing to "
            "find authors from any element in the page, which is particularly "
            "useful for sites that do not cite them in the standard metadata. "
            "Notice that options --author-from-csss and --csss-author-regex "
            "work together as a pipeline, first getting the author name "
            "from the page and the second filtering optionally selecting a "
            "substring from it."
        ),
    )

    parser.add_argument(
        "--csss-author-regex",
        action="store",
        default="(.+)",
        metavar="REGEX",
        help=(
            "A regular expression containing a single capture group that "
            "will be used to select the part of the text returned by "
            "--author-from-csss then used as the author name. Example: "
            "'by\\s+(.+)' will remove the 'by ' prefix from a byline, "
            "returning only the name."
        ),
    )

    parser.add_argument(
        "--categories-from-xpath",
        action="store",
        default=None,
        metavar="XPATH_EXPRESSION",
        help=(
            "Use this XPath expression to get the list of categories for the "
            "feed item. Expression should return a string."
        ),
    )

    parser.add_argument(
        "--categories-from-csss",
        action="store",
        default=None,
        metavar="CSS_SELECTOR",
        help=("Use this CSS Selector to get the list of categories for the item."),
    )

    parser.add_argument(
        "--split-categories",
        action="store",
        default=None,
        metavar="STRING",
        help=(
            "Post-process the categories of the items, splitting them with "
            "the string given in this option. This is useful for sites that "
            "put categories in a single text element or attribute, separated "
            "by commas or similar, making them very readable for humans but "
            "hard (or impossible) to get them with options "
            "--categories-from-xpath or --categories-from-csss."
        ),
    )

    parser.add_argument(
        "--log",
        action="store",
        type=str,
        default="WARNING",
        metavar="LOG_LEVEL",
        help=("Define a log level. Valid values are " + ", ".join(USER_LOG_LEVELS)),
    )

    parser.add_argument(
        "--test",
        action="store_true",
        default=False,
        help=(
            "Do not generate the feed, but just print to stdout the "
            "information that was discovered and would be used to generate "
            "the feed. Useful for debugging link and date patterns."
        ),
    )

    parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        default=False,
        help=(
            "Follow every link matching the pattern and download the page to "
            "gather more information. It is slower, sends extra requests to "
            "the site and transfers more data (sometimes a lot more!), but "
            "allows higher quality feeds."
        ),
    )

    parser.add_argument(
        "-B",
        "--with-body",
        action="store_true",
        default=False,
        help=(
            "Include the page body in the feed, i.e., build a complete "
            "feed. This option requires --follow to work and some "
            "caution is required as it is pretty easy to generate "
            "gigantic feeds by following too many links or reading too "
            "much data from them. Careful usage of options --max-links "
            "and --max-page-length is required! The program will only "
            "pick the contents of the <body> element of the pages, up to "
            "the point that --max-page-length allowed it to be loaded. "
            "SECURITY: this program does some effort to remove malicious "
            "content (e.g. scripts) inserted by the page, but the output "
            "is still considered unsafe and we understand that feed "
            "readers *must* handle it in the same way they deal with "
            "potentially malicious feeds loaded from the network. If "
            "your feed reader treats feeds generated by local commands "
            "more liberally, please do not use this option."
        ),
    )

    parser.add_argument(
        "--body-xpath",
        action="store",
        type=str,
        default=None,
        metavar="XPATH_EXPRESSION",
        help=(
            "A XPath expression selecting the HTML elements to be included "
            "in the body of the feed entry when option --with-body is used. "
            'By default, newslinkrss will use the entire "body" element, '
            "but sometimes a more restricted selection is welcome, for "
            "example, one that includes only the relevant text of a news "
            "article, leaving out menus, headers, related news, etc. "
            "This option can be used together with --body-csss and any "
            "that matches will be used, with XPath having priority."
        ),
    )

    parser.add_argument(
        "--body-csss",
        action="store",
        type=str,
        default=None,
        metavar="CSS_SELECTOR",
        help=(
            "A CSS Selector to pick the HTML elements to be included in the "
            "body of the feed entry when option --with-body is used. By "
            'default, newslinkrss will use the entire "body" HTML element, '
            "but sometimes a more restricted selection is welcome, for "
            "example, one that includes only the relevant text of a news "
            "article, leaving out menus, headers, related news, etc. "
            "This option can be used together with --body-xpath and any "
            "that matches will be used, with XPath having priority."
        ),
    )

    parser.add_argument(
        "-R",
        "--body-remove-tag",
        action="append",
        type=str,
        default=None,
        metavar="TAG_NAME",
        help=(
            "Remove all occurrences of the given tag from the feed body and "
            "move their child elements to their parents. This only makes "
            "sense if --with-body is used. This option can be used as many "
            "times as required to remove all unwanted elements and all "
            "children elements. For a more complex operations that allow "
            "arbitrary expressions, see --body-remove-csss and "
            "--body-remove-xpath."
        ),
    )

    parser.add_argument(
        "-X",
        "--body-remove-xpath",
        action="append",
        type=str,
        default=None,
        metavar="XPATH_EXPRESSION",
        help=(
            "Delete the elements specified by the XPath argument from the "
            "feed body, including all their children. This only makes sense "
            "if --with-body is used. This option can be used as many times "
            "as required to remove all unwanted elements. For a CSS Selector "
            "equivalent, see --body-remove-csss. For a simpler version, "
            "to only remove tags but preserve child elements, see "
            "--body-remove-tag."
        ),
    )

    parser.add_argument(
        "-C",
        "--body-remove-csss",
        action="append",
        type=str,
        default=None,
        metavar="CSS_SELECTOR",
        help=(
            "Delete the elements specified by the CSS Selector from the "
            "feed body, including all their children. This only makes sense "
            "if --with-body is used. This option can be used as many times "
            "as required to remove all unwanted elements. For a XPath "
            "equivalent, see --body-remove-xpath. For a simpler version, "
            "to only remove tags but preserve child elements, see "
            "--body-remove-tag."
        ),
    )

    parser.add_argument(
        "-N",
        "--body-rename-tag",
        action="append",
        type=str,
        nargs=2,
        default=None,
        metavar=("TAG_NAME", "NEW_NAME"),
        help=(
            "Replace all occurences of the given tag by the new one in "
            "the feed body. All attributes and the structure are preserved. "
            "A typical use case for this is replacing tags amp-img for img "
            'in sites "infected" by AMP, e.g.: "--rename-tag amp-img img". '
            "This option may be used as many times as required."
        ),
    )

    parser.add_argument(
        "--body-rename-attr",
        action="append",
        type=str,
        nargs=3,
        default=None,
        metavar=("TAG_NAME", "OLD_ATTR_NAME", "NEW_ATTR_NAME"),
        help=(
            "Rename attributes from the given tag. This can be used, for "
            "example, to recover images that are subjected to some lazy "
            "loading strategy: assuming that some site has all images src "
            "attributes pointing to a placeholder image while the actual "
            'URL for the image is in attribute "data-src", it is possible '
            'to recover it by doing "--body-rename-attr img data-src src". '
            "This option has no effect if the element does not have the "
            "source attribute. The destination attribute will be overriden "
            "if it already exists. This option may be used as many times "
            "as required."
        ),
    )

    parser.add_argument(
        "-Q",
        "--qs-remove-param",
        action="append",
        type=str,
        default=None,
        metavar="REGEX",
        help=(
            "If a URL captured from the source page has a query string, "
            "remove parameters with names matching the regular expression "
            "given in this option. This allows striping tracking parameters "
            "or detecting duplicate URLs that only differ by irrelevant "
            "parameters. Notice that these are regular expressions matching "
            "only against the *name* or the parameter and be aware of the "
            "anchors required to match prefixes only, example: '^utm_.+' . "
            "This option may be used several times if required."
        ),
    )

    parser.add_argument(
        "--require-dates",
        action="store_true",
        default=False,
        help=(
            "Only include an entry in the feed if it has a valid date found "
            "from any supported method. Very useful when filtering blogs and "
            "news sites."
        ),
    )

    parser.add_argument(
        "-U",
        "--user-agent",
        action="store",
        metavar="UA_STRING",
        default=DEFAULT_USER_AGENT,
        help=(
            "Set the user agent to identify ourselves to the site. Some sites "
            "can send different types of content according to it or just "
            "deny access do unknown UAs, so the best option is just "
            "impersonate a commonly used browser."
        ),
    )

    parser.add_argument(
        "--max-page-length",
        action="store",
        default=2048,
        metavar="NUMBER",
        type=int,
        help=(
            "Maximum amount of data, in kilobytes, to download from a single "
            "HTTP request for the pages followed when using option --follow. "
            "If this limit is exceeded, any remaining data will be discarded. "
            "Very important when following links because any of them can led "
            "us into downloading a DVD ISO or something like. This option "
            'does not applies to the "first" page, i.e. the one which URL '
            "is given in command line and it is used as starting point for "
            "the entire process; for this limit, use option "
            "--max-first-page-length"
        ),
    )

    parser.add_argument(
        "--max-first-page-length",
        action="store",
        default=2048,
        metavar="NUMBER",
        type=int,
        help=(
            "Maximum amount of data, in kilobytes, to download from the "
            "first pages, i.e. the ones which URLs are given in command line "
            "to start the process. This is important because the server can "
            "generate and infinite amount of data, redirect us to a "
            "DVD ISO or anything else. For limiting the pages downloaded "
            "when following links (option --follow), see option "
            "--max-page-length"
        ),
    )

    parser.add_argument(
        "--encoding",
        action="store",
        type=str,
        metavar="CHARSET",
        help="Use this explicit character encoding instead of detecting it "
        "automatically. Usually only required for pages with incorrect "
        "charset information which cause the feed to also be presented "
        'in the wrong encoding (aka "mojibake").',
    )

    parser.add_argument(
        "--lang",
        action="append",
        type=str,
        default=None,
        metavar="LANGUAGE_CODE",
        help=(
            "Ask the site to return the content in this particular language, "
            "if available. Languages must be specified in ISO 639 or RFC 1766 "
            "codes (e.g. en, en-US, pt-BR, de-DE). This option may be used "
            "several times if required and the order in which the options "
            "are given will be the preference order of the languages. If no "
            "option is given and environment variable LANG is set, "
            "newslinkrss will try to get a language code from it. Internally, "
            "this sets the HTTP Accept-Language header to the prescribed "
            "value(s)."
        ),
    )

    parser.add_argument(
        "--cookie",
        action="append",
        type=str,
        default=None,
        metavar="COOKIE_DEFINITION",
        help=(
            "Add an arbitrary HTTP cookie to all requests sent to the server. "
            "These cookies may be overwritten by cookies set by the server "
            "and then the new ones will be sent in subsequent requests (if "
            "--follow is used). These explicitly requested cookies are sent "
            "even if option --no-cookies is used but, in this case, the "
            "server will not be able to change or replace them. "
            "The cookie definition is the same used for the Set-Cookie HTTP "
            "header as defined in RFC 2965 and can be pretty complex. The "
            "simplest form (NAME=VALUE) can be used ofr the majority of "
            "cases, however. "
            "This option may be repeated as many times as necessary."
        ),
    )

    parser.add_argument(
        "-H",
        "--header",
        action="append",
        type=str,
        default=None,
        metavar="HTTP_HEADER",
        help=(
            "Add an arbitrary HTTP header to all requests send to the "
            "destination server. Headers must be specified in format "
            '"Name: Value" and will be passed to destination almost verbatim, '
            "with only basic whitespace stripping. This option may be "
            "repeated as many times as necessary."
        ),
    )

    parser.add_argument(
        "-t",
        "--http-timeout",
        action="store",
        default=2.0,
        type=float,
        metavar="SECONDS",
        help="Timeout for HTTP(S) requests, in seconds",
    )

    parser.add_argument(
        "--no-cookies",
        action="store_true",
        default=False,
        help=(
            "Do not remember cookies among requests. As cookies are never "
            "persisted across invocations of this command, this will only "
            "have any effect when using --follow, typically for sites that "
            "use cookies to detect too many requests in a row."
        ),
    )

    parser.add_argument(
        "--locale",
        action="store",
        type=str,
        default=None,
        help=(
            "Use this locale for parsing dates and times. By default, "
            "newslinkrss will use the locale from environment variables and "
            "ignore any failure. If this option is used, it will use the "
            "given locale and abort in the event of a failure (e.g. locale "
            "not available). If you want to keep the default best-effort "
            "strategy for a non-default locale, set LC_ALL for newslinkrss "
            "(i.e. call with 'LC_ALL=pt_BR.UTF-8 newslinkrss <options>')."
        ),
    )

    parser.add_argument(
        "-E",
        "--no-exception-feed",
        action="store_true",
        default=False,
        help=(
            "Do not generate feed entries for runtime errors. "
            "The default behavior is to have the information about any "
            "failures that happen when processing the feed returned as the "
            "feed itself, so the user will see it there. However, this "
            "option allows disabling this for moments where it makes more "
            "sense, e.g. when debugging."
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        action="store",
        metavar="FILENAME",
        help=(
            "Output file to save the feed. If not given, it will be written "
            "to stdout."
        ),
    )

    parser.add_argument(
        "urls",
        action="store",
        nargs="+",
        metavar="URL",
        help="URL of the website to generate the feed.",
    )

    return parser
