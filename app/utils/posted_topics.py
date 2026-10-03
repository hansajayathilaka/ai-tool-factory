"""List topics a page has already covered, for duplicate-topic checks.

Usage: python utils/posted_topics.py <slug> [--status posted|finalized|drafts|research|all] [--json]

Default: posted, finalized and drafts. 'research' lists research notes and their status
(new / used / dropped); 'all' includes everything.
"""
from __future__ import annotations

import argparse
import json

import common

FOLDERS = (*common.STATUS_FOLDERS, "research")


def collect(slug: str, folders: tuple[str, ...]) -> list[dict]:
    page = common.page_dir(slug)
    rows = []
    for folder in folders:
        for path in sorted((page / folder).glob("*.md")):
            try:
                fm, _ = common.read_post(path)
            except ValueError as exc:
                rows.append({"folder": folder, "file": path.name, "error": str(exc)})
                continue
            rows.append({
                "folder": folder,
                "date": fm.get("posted") or fm.get("created") or path.name[:10],
                "topic": fm.get("topic") or "",
                "pillar": fm.get("pillar") or "",
                "type": fm.get("post_type") or fm.get("kind") or "",
                "status": fm.get("status") if folder == "research" else folder,
                "file": path.name,
            })
    rows.sort(key=lambda r: r.get("date", ""), reverse=True)
    return rows


def main() -> None:
    common.utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug")
    parser.add_argument("--status", choices=(*FOLDERS, "all"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.status == "all":
        folders = FOLDERS
    elif args.status:
        folders = (args.status,)
    else:
        folders = common.STATUS_FOLDERS
    rows = collect(args.slug, folders)

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    if not rows:
        print(f"No files in {', '.join(folders)} for {args.slug}")
        return
    print("| Date | Status | Topic | Pillar | Type | File |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        if "error" in r:
            print(f"| ? | {r['folder']} | (unreadable: {r['error']}) | | | {r['file']} |")
        else:
            print(f"| {r['date']} | {r['status']} | {r['topic']} | {r['pillar']} | {r['type']} | {r['file']} |")


if __name__ == "__main__":
    main()
