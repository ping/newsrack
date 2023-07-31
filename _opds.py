# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0

# Helpers to generate opds xml - extremely minimal
from datetime import datetime
from typing import Dict, Optional
from xml.dom import minidom

extension_contenttype_map = {
    ".epub": "application/epub+zip",
    ".mobi": "application/x-mobipocket-ebook",
    ".azw": "application/x-mobipocket-ebook",
    ".azw3": "application/x-mobi8-ebook",
    ".pdf": "application/pdf",
}


def simple_tag(
    doc_root: minidom.Document,
    tag: str,
    value: Optional[str] = None,
    attributes: Optional[Dict] = None,
) -> minidom.Element:
    new_tag = doc_root.createElement(tag)
    if value:
        new_tag.appendChild(doc_root.createTextNode(value))
    if attributes:
        for k, v in attributes.items():
            new_tag.setAttribute(k, v)
    return new_tag


def init_feed(
    doc: minidom.Document, publish_site: str, feed_id: str, title: str
) -> minidom.Element:
    feed = simple_tag(
        doc,
        "feed",
        attributes={
            "xmlns": "http://www.w3.org/2005/Atom",
            "xmlns:dc": "http://purl.org/dc/terms/",
            "xmlns:opds": "http://opds-spec.org/2010/catalog",
        },
    )
    doc.appendChild(feed)
    feed.appendChild(simple_tag(doc, "id", feed_id))
    feed.appendChild(simple_tag(doc, "title", title))
    feed.appendChild(simple_tag(doc, "updated", f"{datetime.now():%Y-%m-%dT%H:%M:%SZ}"))
    feed_author = doc.createElement("author")
    feed_author.appendChild(simple_tag(doc, "name", publish_site))
    feed_author.appendChild(simple_tag(doc, "uri", publish_site))
    feed.appendChild(feed_author)
    return feed
