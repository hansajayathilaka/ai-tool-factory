"""Summarize a platform's per-item engagement CSV export for one channel.

  insights <slug> <export.csv> [--out insights/<date>-summary.md]
  (relative CSV and --out paths may be given relative to channels/<slug>/)
  insights <slug> <export.csv> --map reach="Post reach" --map caption="Message"

Columns are detected by name (platforms rename them now and then); tool.json ->
insights.columns adds header names per field. If detection fails, the command lists
the CSV's headers; pass --map field="Header" to fix it. Rows are matched to files in
published/ by the text of the tool's main section, so results can be grouped by the
frontmatter keys in tool.json -> insights.group_by.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from .common import today
from .frontmatter import read_item, sections
from .tool import Tool

FIELDS = {
    "publish_time": ["publish time", "published", "post published", "publish date", "date", "created"],
    "caption": ["description", "post message", "message", "caption", "title"],
    "permalink": ["permalink", "post link", "link"],
    "platform_type": ["post type", "type"],
    "reach": ["reach", "post reach", "lifetime post total reach", "accounts center accounts reached"],
    "impressions": ["impressions", "views", "post impressions", "lifetime post total impressions"],
    "reactions": ["reactions", "likes", "lifetime post reactions"],
    "comments": ["comments"],
    "shares": ["shares"],
    "engagement_total": ["reactions, comments and shares", "engagements", "post engagements"],
    "clicks": ["total clicks", "clicks", "link clicks", "lifetime post consumers"],
}
REQUIRED = ("publish_time", "caption")
DATE_FORMATS = ("%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M", "%m/%d/%Y", "%Y-%m-%d")
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MATCH_THRESHOLD = 0.6


def detect_columns(headers: list[str], overrides: dict[str, str],
                   extra: dict[str, list[str]] | None = None) -> dict[str, str]:
    """Map each field to a CSV header. extra holds tool.json -> insights.columns, tried first."""
    extra = extra or {}
    unknown = [f for f in extra if f not in FIELDS]
    if unknown:
        raise SystemExit(f"tool.json insights.columns: unknown field(s) {', '.join(unknown)} "
                         f"(fields: {', '.join(FIELDS)})")
    by_norm = {h.strip().lower(): h for h in headers}
    cols = {}
    for field, defaults in FIELDS.items():
        candidates = [c.strip().lower() for c in extra.get(field, [])] + defaults
        if field in overrides:
            if overrides[field] not in headers:
                raise SystemExit(f"--map {field}: column {overrides[field]!r} not in CSV")
            cols[field] = overrides[field]
            continue
        for cand in candidates:
            if cand in by_norm:
                cols[field] = by_norm[cand]
                break
    missing = [f for f in REQUIRED if f not in cols]
    if missing or "reach" not in cols and "impressions" not in cols:
        raise SystemExit(
            f"Could not find columns for: {', '.join(missing) or 'reach/impressions'}\n"
            f"CSV headers: {headers}\nUse --map field=\"Header\" (fields: {', '.join(FIELDS)})")
    return cols


def number(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip().replace(",", "")
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return None


def parse_time(value: str) -> datetime | None:
    value = (value or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def norm_text(s: str) -> str:
    s = re.sub(r"#\w+", "", s.lower())
    return re.sub(r"\W+", " ", s).strip()[:200]


def load_published(tool: Tool, slug: str) -> list[dict]:
    items = []
    for path in sorted((tool.channel_dir(slug) / "published").glob("*.md")):
        try:
            fm, body = read_item(path)
        except ValueError:
            continue
        text = sections(body).get(tool.main_section, "")
        items.append({"file": path.name, "fm": fm, "key": norm_text(text)})
    return items


def match_item(caption: str, published: list[dict]) -> dict | None:
    key = norm_text(caption)
    if not key:
        return None
    best, best_score = None, 0.0
    for p in published:
        if not p["key"]:
            continue
        score = SequenceMatcher(None, key, p["key"]).ratio()
        if score > best_score:
            best, best_score = p, score
    return best if best_score >= MATCH_THRESHOLD else None


def read_rows(tool: Tool, csv_path: Path, overrides: dict[str, str], published: list[dict]) -> list[dict]:
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        cols = detect_columns(reader.fieldnames or [], overrides, tool.insights.get("columns"))
        rows = []
        for raw in reader:
            when = parse_time(raw.get(cols["publish_time"], ""))
            if when is None:  # Meta adds a description row under the header; skip non-data rows
                continue
            get = lambda f: number(raw.get(cols[f])) if f in cols else None  # noqa: E731
            reactions, comments, shares = get("reactions"), get("comments"), get("shares")
            if None not in (reactions, comments, shares) and "reactions" in cols:
                engagement = reactions + comments + shares
            else:
                engagement = get("engagement_total")
            reach = get("reach") if "reach" in cols else get("impressions")
            caption = raw.get(cols["caption"], "") or ""
            match = match_item(caption, published)
            fm = match["fm"] if match else {}
            groups = {}
            for key in tool.insights.get("group_by", []):
                value = fm.get(key)
                if not value and key == "item_type" and "platform_type" in cols:
                    value = raw.get(cols["platform_type"], "")
                groups[key] = str(value) if value else ("(unknown)" if match or key == "item_type" else "(unmatched)")
            rows.append({
                "time": when,
                "caption": caption,
                "permalink": raw.get(cols.get("permalink", ""), ""),
                "reach": reach,
                "engagement": engagement,
                "rate": (engagement / reach) if engagement is not None and reach else None,
                "clicks": get("clicks"),
                "file": match["file"] if match else None,
                "groups": groups,
            })
    return rows


def med(values) -> float | None:
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def fmt_num(v) -> str:
    return "–" if v is None else f"{v:,.0f}"


def fmt_rate(v) -> str:
    return "–" if v is None else f"{v * 100:.2f}%"


def group_table(rows: list[dict], key, title: str) -> list[str]:
    groups = defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    out = [f"## {title}", "", "| Group | Posts | Median reach | Median engagement | Median eng. rate |",
           "|---|---|---|---|---|"]
    ordered = sorted(groups.items(), key=lambda kv: med(r["rate"] for r in kv[1]) or -1, reverse=True)
    for name, rs in ordered:
        flag = " ⚠ small sample" if len(rs) < 5 else ""
        out.append(f"| {name}{flag} | {len(rs)} | {fmt_num(med(r['reach'] for r in rs))} | "
                   f"{fmt_num(med(r['engagement'] for r in rs))} | {fmt_rate(med(r['rate'] for r in rs))} |")
    return out + [""]


def time_block(hour: int) -> str:
    if 5 <= hour < 12:
        return "Morning (05–12)"
    if 12 <= hour < 17:
        return "Afternoon (12–17)"
    if 17 <= hour < 22:
        return "Evening (17–22)"
    return "Night (22–05)"


def one_line(text: str, limit: int) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


def item_list(tool: Tool, rows: list[dict], title: str) -> list[str]:
    keys = tool.insights.get("group_by", [])
    head = "".join(f" {tool.label(k).capitalize()} |" for k in keys)
    out = [f"## {title}", "", f"| Date | Reach | Eng. rate |{head} Text start |",
           "|---|---|---|" + "---|" * len(keys) + "---|"]
    for r in rows:
        cap = one_line(r["caption"], 70).replace("|", "/")
        cells = "".join(f" {r['groups'][k]} |" for k in keys)
        out.append(f"| {r['time']:%Y-%m-%d} | {fmt_num(r['reach'])} | {fmt_rate(r['rate'])} |{cells} {cap} |")
    return out + [""]


def summarize(tool: Tool, slug: str, csv_path: Path, rows: list[dict]) -> str:
    if not rows:
        raise SystemExit("No data rows found in the CSV")
    times = [r["time"] for r in rows]
    matched = sum(1 for r in rows if r["file"])
    rated = [r for r in rows if r["rate"] is not None]
    lines = [
        f"# Insights summary — {slug}",
        "",
        f"- **Export:** `{csv_path.name}`",
        f"- **Generated:** {today()}",
        f"- **Period:** {min(times):%Y-%m-%d} to {max(times):%Y-%m-%d}",
        f"- **{tool.nouns['items'].capitalize()}:** {len(rows)} ({matched} matched to files in published/)",
        f"- **Median reach:** {fmt_num(med(r['reach'] for r in rows))}",
        f"- **Median engagement (reactions + comments + shares):** {fmt_num(med(r['engagement'] for r in rows))}",
        f"- **Median engagement rate (engagement ÷ reach):** {fmt_rate(med(r['rate'] for r in rows))}",
        "",
    ]
    for key in tool.insights.get("group_by", []):
        lines += group_table(rows, lambda r, k=key: r["groups"][k], f"By {tool.label(key)}")
    lines += group_table(rows, lambda r: WEEKDAYS[r["time"].weekday()], "By weekday")
    lines += group_table(rows, lambda r: time_block(r["time"].hour), "By time of day")
    ranked = sorted(rated, key=lambda r: r["rate"], reverse=True)
    items = tool.nouns["items"]
    lines += item_list(tool, ranked[:5], f"Top 5 {items} by engagement rate")
    if len(ranked) > 5:
        lines += item_list(tool, list(reversed(ranked[-5:])), f"Bottom 5 {items} by engagement rate")
    unmatched = [r for r in rows if not r["file"]]
    if unmatched:
        lines += [f"## Unmatched {items} ({len(unmatched)})", "",
                  f"These were not found in published/ (published outside this tool, "
                  f"or edited on {tool.nouns['platform']}):", ""]
        lines += [f"- {r['time']:%Y-%m-%d}: {one_line(r['caption'], 80)}" for r in unmatched[:20]]
        lines.append("")
    return "\n".join(lines)


def run(tool: Tool, args: argparse.Namespace) -> None:
    overrides = {}
    for item in args.map:
        field, sep, header = item.partition("=")
        if not sep or field not in FIELDS:
            raise SystemExit(f"bad --map {item!r} (fields: {', '.join(FIELDS)})")
        overrides[field] = header.strip('"')

    channel = tool.channel_dir(args.slug)
    if not args.csv.is_file() and (channel / args.csv).is_file():
        args.csv = channel / args.csv  # allow paths relative to the channel folder, like --out
    if not args.csv.is_file():
        raise SystemExit(f"CSV not found: {args.csv}")
    rows = read_rows(tool, args.csv, overrides, load_published(tool, args.slug))

    if args.json:
        print(json.dumps(rows, default=str, ensure_ascii=False, indent=2))
        return
    summary = summarize(tool, args.slug, args.csv, rows)
    if args.out:
        out = args.out if args.out.is_absolute() else channel / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(summary + "\n", encoding="utf-8")
        print(f"Wrote {tool.rel(out)}")
    else:
        print(summary)


def register(sub, tool: Tool) -> None:
    p = sub.add_parser("insights", help="summarize an engagement CSV export",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("slug", help=f"{tool.nouns['channel']} slug")
    p.add_argument("csv", type=Path)
    p.add_argument("--out", type=Path,
                   help=f"write the summary here (relative paths are inside the {tool.nouns['channel']} folder)")
    p.add_argument("--map", action="append", default=[], metavar='FIELD="Header"',
                   help=f"override a column; fields: {', '.join(FIELDS)}")
    p.add_argument("--json", action="store_true", help="print rows as JSON instead of a summary")
    p.set_defaults(func=run)
