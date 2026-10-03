"""Print top Reddit posts from a channel's subreddits (listed under '## Reddit' in sources.md).

  reddit <slug> [--period week] [--limit 10]
  reddit --sub gardening --sub srilanka

Uses Reddit's OAuth API when REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are set
(environment or .env); otherwise falls back to the public JSON endpoints, which
are heavily rate-limited. Set REDDIT_USER_AGENT to identify your app.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from ..common import load_env
from ..tool import Tool

SUB_RE = re.compile(r"(?<![\w/])r/([A-Za-z0-9_]{2,21})\b")


def subs_from_sources(tool: Tool, slug: str) -> list[str]:
    text = (tool.channel_dir(slug) / "sources.md").read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    subs, in_section = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = line[3:].strip().lower().startswith("reddit")
        elif in_section:
            subs.extend(SUB_RE.findall(line))
    return subs


def _get_json(url: str, headers: dict, data: bytes | None = None) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def oauth_token(user_agent: str) -> str | None:
    cid, secret = os.environ.get("REDDIT_CLIENT_ID"), os.environ.get("REDDIT_CLIENT_SECRET")
    if not (cid and secret):
        return None
    auth = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    resp = _get_json("https://www.reddit.com/api/v1/access_token",
                     {"Authorization": f"Basic {auth}", "User-Agent": user_agent}, body)
    return resp.get("access_token")


def run(tool: Tool, args: argparse.Namespace) -> None:
    load_env(tool.dir)
    subs = args.sub or (subs_from_sources(tool, args.slug) if args.slug else [])
    if not subs:
        print("No subreddits given or listed in sources.md under '## Reddit communities'")
        return

    user_agent = os.environ.get("REDDIT_USER_AGENT", "script:ai-automation-research:1.0")
    token = oauth_token(user_agent)
    base = "https://oauth.reddit.com" if token else "https://www.reddit.com"
    headers = {"User-Agent": user_agent}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        print("(no Reddit API credentials; using public endpoint, may be rate-limited)\n")

    for sub in subs:
        print(f"## r/{sub} (top, {args.period})\n")
        query = urllib.parse.urlencode({"t": args.period, "limit": args.limit})
        suffix = "" if token else ".json"
        try:
            listing = _get_json(f"{base}/r/{sub}/top{suffix}?{query}", headers)
        except Exception as exc:
            print(f"- ERROR: {type(exc).__name__}: {exc}")
            if not token and getattr(exc, "code", None) in (403, 429):
                print("  Reddit blocks most unauthenticated requests. Create a 'script' app at "
                      "https://www.reddit.com/prefs/apps and set REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET in .env")
            print()
            continue
        for child in listing.get("data", {}).get("children", []):
            p = child.get("data", {})
            when = datetime.fromtimestamp(p.get("created_utc", 0), timezone.utc).date().isoformat()
            print(f"- {when} · ▲{p.get('score', 0)} · 💬{p.get('num_comments', 0)} — "
                  f"[{p.get('title', '').strip()}](https://www.reddit.com{p.get('permalink', '')})")
            if p.get("url") and "reddit.com" not in p["url"]:
                print(f"  links to: {p['url']}")
        print()


def register(sub, tool: Tool) -> None:
    p = sub.add_parser("reddit", help="top posts from the subreddits in sources.md",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("slug", nargs="?", help=f"{tool.nouns['channel']} slug (reads its sources.md)")
    p.add_argument("--sub", action="append", default=[], help="subreddit name (repeatable)")
    p.add_argument("--period", default="week", choices=("day", "week", "month", "year"))
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=run)
