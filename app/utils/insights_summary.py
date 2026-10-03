"""Summarize a Meta Business Suite post-performance CSV export for one page.

Usage:
  python utils/insights_summary.py <slug> <export.csv> [--out insights/<date>-summary.md]
  (relative CSV and --out paths may be given relative to facebook_pages/<slug>/)
  python utils/insights_summary.py <slug> <export.csv> --map reach="Post reach" --map caption="Message"

Columns are detected by name (Meta renames them now and then). If detection fails,
the script lists the CSV's headers; pass --map field="Header" to fix it.
Posts are matched to files in posted/ by caption, so results can be grouped by
pillar and post type.
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

import common

FIELDS = {
    "publish_time": ["publish time", "published", "post published", "publish date", "date", "created"],
    "caption": ["description", "post message", "message", "caption", "title"],
    "permalink": ["permalink", "post link", "link"],
    "meta_type": ["post type", "type"],
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


def detect_columns(headers: list[str], overrides: dict[str, str]) -> dict[str, str]:
    by_norm = {h.strip().lower(): h for h in headers}
    cols = {}
    for field, candidates in FIELDS.items():
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


def load_posted(slug: str) -> list[dict]:
    posts = []
    for path in sorted((common.page_dir(slug) / "posted").glob("*.md")):
        try:
            fm, body = common.read_post(path)
        except ValueError:
            continue
        caption = common.sections(body).get("Caption", "")
        posts.append({"file": path.name, "fm": fm, "key": norm_text(caption)})
    return posts


def match_post(caption: str, posted: list[dict]) -> dict | None:
    key = norm_text(caption)
    if not key:
        return None
    best, best_score = None, 0.0
    for p in posted:
        if not p["key"]:
            continue
        score = SequenceMatcher(None, key, p["key"]).ratio()
        if score > best_score:
            best, best_score = p, score
    return best if best_score >= MATCH_THRESHOLD else None


def read_rows(csv_path: Path, overrides: dict[str, str], posted: list[dict]) -> list[dict]:
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        cols = detect_columns(reader.fieldnames or [], overrides)
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
            match = match_post(caption, posted)
            fm = match["fm"] if match else {}
            rows.append({
                "time": when,
                "caption": caption,
                "permalink": raw.get(cols.get("permalink", ""), ""),
                "reach": reach,
                "engagement": engagement,
                "rate": (engagement / reach) if engagement is not None and reach else None,
                "clicks": get("clicks"),
                "file": match["file"] if match else None,
                "pillar": fm.get("pillar") or "(unmatched)",
                "post_type": fm.get("post_type") or (raw.get(cols["meta_type"], "") if "meta_type" in cols else "")
                or "(unknown)",
                "language": fm.get("language") or "",
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


def post_list(rows: list[dict], title: str) -> list[str]:
    out = [f"## {title}", "", "| Date | Reach | Eng. rate | Pillar | Type | Caption start |", "|---|---|---|---|---|---|"]
    for r in rows:
        cap = one_line(r["caption"], 70).replace("|", "/")
        out.append(f"| {r['time']:%Y-%m-%d} | {fmt_num(r['reach'])} | {fmt_rate(r['rate'])} | "
                   f"{r['pillar']} | {r['post_type']} | {cap} |")
    return out + [""]


def summarize(slug: str, csv_path: Path, rows: list[dict]) -> str:
    if not rows:
        raise SystemExit("No data rows found in the CSV")
    times = [r["time"] for r in rows]
    matched = sum(1 for r in rows if r["file"])
    rated = [r for r in rows if r["rate"] is not None]
    lines = [
        f"# Insights summary — {slug}",
        "",
        f"- **Export:** `{csv_path.name}`",
        f"- **Generated:** {common.today()}",
        f"- **Period:** {min(times):%Y-%m-%d} to {max(times):%Y-%m-%d}",
        f"- **Posts:** {len(rows)} ({matched} matched to files in posted/)",
        f"- **Median reach:** {fmt_num(med(r['reach'] for r in rows))}",
        f"- **Median engagement (reactions + comments + shares):** {fmt_num(med(r['engagement'] for r in rows))}",
        f"- **Median engagement rate (engagement ÷ reach):** {fmt_rate(med(r['rate'] for r in rows))}",
        "",
    ]
    lines += group_table(rows, lambda r: r["pillar"], "By pillar")
    lines += group_table(rows, lambda r: r["post_type"], "By post type")
    lines += group_table(rows, lambda r: WEEKDAYS[r["time"].weekday()], "By weekday")
    lines += group_table(rows, lambda r: time_block(r["time"].hour), "By time of day")
    ranked = sorted(rated, key=lambda r: r["rate"], reverse=True)
    lines += post_list(ranked[:5], "Top 5 posts by engagement rate")
    if len(ranked) > 5:
        lines += post_list(list(reversed(ranked[-5:])), "Bottom 5 posts by engagement rate")
    unmatched = [r for r in rows if not r["file"]]
    if unmatched:
        lines += [f"## Unmatched posts ({len(unmatched)})", "",
                  "These were not found in posted/ (posted outside this tool, or caption edited on Facebook):", ""]
        lines += [f"- {r['time']:%Y-%m-%d}: {one_line(r['caption'], 80)}" for r in unmatched[:20]]
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    common.utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out", type=Path, help="write the summary here (relative paths are inside the page folder)")
    parser.add_argument("--map", action="append", default=[], metavar='FIELD="Header"',
                        help=f"override a column; fields: {', '.join(FIELDS)}")
    parser.add_argument("--json", action="store_true", help="print rows as JSON instead of a summary")
    args = parser.parse_args()

    overrides = {}
    for item in args.map:
        field, sep, header = item.partition("=")
        if not sep or field not in FIELDS:
            parser.error(f"bad --map {item!r}")
        overrides[field] = header.strip('"')

    page = common.page_dir(args.slug)
    if not args.csv.is_file() and (page / args.csv).is_file():
        args.csv = page / args.csv  # allow paths relative to the page folder, like --out
    if not args.csv.is_file():
        raise SystemExit(f"CSV not found: {args.csv}")
    rows = read_rows(args.csv, overrides, load_posted(args.slug))

    if args.json:
        print(json.dumps(rows, default=str, ensure_ascii=False, indent=2))
        return
    report = summarize(args.slug, args.csv, rows)
    if args.out:
        out = args.out if args.out.is_absolute() else page / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report + "\n", encoding="utf-8")
        print(f"Wrote {out.relative_to(common.APP_DIR) if out.is_relative_to(common.APP_DIR) else out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
