"""Print recent items from a page's RSS/Atom feeds (listed under '## RSS feeds' in sources.md).

Usage:
  python utils/rss_fetch.py <slug> [--days 7] [--limit 15]
  python utils/rss_fetch.py --url <feed-url> [--days 30]     # test a single feed
"""
from __future__ import annotations

import argparse
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import common

USER_AGENT = "ai-automation-rss/1.0 (+content research; contact page owner)"
MAX_BYTES = 5 * 1024 * 1024
ATOM = "{http://www.w3.org/2005/Atom}"
URL_RE = re.compile(r"https?://[^\s)>\]]+")
TRACKING_PREFIXES = ("utm_", "at_", "fbclid", "gclid", "mc_", "ocid")


def feeds_from_sources(slug: str) -> list[tuple[str, str]]:
    """Return (name, url) pairs from the '## RSS feeds' section of sources.md."""
    text = (common.page_dir(slug) / "sources.md").read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    feeds, in_section = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = line[3:].strip().lower().startswith("rss")
            continue
        if in_section:
            m = URL_RE.search(line)
            if m:
                name = line[: m.start()].strip(" -*:\t") or m.group(0)
                feeds.append((name, m.group(0)))
    return feeds


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("feed larger than 5 MB")
    return data


def _text(el) -> str:
    return (el.text or "").strip() if el is not None else ""


def _date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _clean(summary: str, limit: int = 220) -> str:
    summary = html.unescape(re.sub(r"<[^>]+>", " ", summary))
    summary = re.sub(r"\s+", " ", summary).strip()
    return summary if len(summary) <= limit else summary[: limit - 1].rstrip() + "…"


def canonical(url: str) -> str:
    """Drop tracking parameters (utm_*, at_*, fbclid, ...) so posts cite clean URLs."""
    parts = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith(TRACKING_PREFIXES)]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def parse(data: bytes) -> list[dict]:
    root = ET.fromstring(data)
    items = []
    for it in root.iter("item"):  # RSS 2.0
        items.append({
            "title": _text(it.find("title")),
            "link": canonical(_text(it.find("link"))),
            "date": _date(_text(it.find("pubDate")) or _text(it.find("{http://purl.org/dc/elements/1.1/}date"))),
            "summary": _clean(_text(it.find("description"))),
        })
    for entry in root.iter(f"{ATOM}entry"):  # Atom
        link = entry.find(f"{ATOM}link[@rel='alternate']")
        if link is None:  # Elements without children are falsy, so no `or` here
            link = entry.find(f"{ATOM}link")
        items.append({
            "title": _text(entry.find(f"{ATOM}title")),
            "link": canonical(link.get("href", "")) if link is not None else "",
            "date": _date(_text(entry.find(f"{ATOM}published")) or _text(entry.find(f"{ATOM}updated"))),
            "summary": _clean(_text(entry.find(f"{ATOM}summary")) or _text(entry.find(f"{ATOM}content"))),
        })
    return items


def main() -> None:
    common.utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug", nargs="?", help="page slug (reads its sources.md)")
    parser.add_argument("--url", help="fetch this single feed instead")
    parser.add_argument("--days", type=int, default=7, help="only items newer than this (default 7)")
    parser.add_argument("--limit", type=int, default=15, help="max items per feed (default 15)")
    args = parser.parse_args()

    if args.url:
        feeds = [(args.url, args.url)]
    elif args.slug:
        feeds = feeds_from_sources(args.slug)
        if not feeds:
            print(f"No RSS feeds listed in facebook_pages/{args.slug}/sources.md")
            return
    else:
        parser.error("give a page slug or --url")

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    for name, url in feeds:
        print(f"## {name}\n<{url}>\n")
        try:
            items = parse(fetch(url))
        except Exception as exc:  # one bad feed must not stop the others
            print(f"- ERROR: {type(exc).__name__}: {exc}\n")
            continue
        recent = [i for i in items if i["date"] is None or i["date"] >= cutoff]
        recent.sort(key=lambda i: i["date"] or cutoff, reverse=True)
        if not recent:
            print(f"- (no items in the last {args.days} days; {len(items)} older items)\n")
            continue
        for i in recent[: args.limit]:
            when = i["date"].date().isoformat() if i["date"] else "undated"
            print(f"- {when} — [{i['title'] or '(no title)'}]({i['link']})")
            if i["summary"]:
                print(f"  {i['summary']}")
        print()


if __name__ == "__main__":
    main()
