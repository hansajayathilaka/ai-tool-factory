"""Move an item between status folders. The folder is the item's status.

  move finalize <draft>       drafts/    -> finalized/  (needs fact_check: passed and --approved)
  move publish <finalized>    finalized/ -> published/  (sets published: date)
  move reopen <finalized>     finalized/ -> drafts/     (resets fact_check: pending)

An item can be given as a path or as a bare filename.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .common import is_iso_date, today
from .frontmatter import read_item, set_field
from .tool import Tool
from .validate import validate_item

TRANSITIONS = {
    "finalize": ("drafts", "finalized"),
    "publish": ("finalized", "published"),
    "reopen": ("finalized", "drafts"),
}


def _write_moved(src: Path, text: str, dest_status: str) -> Path:
    dest = src.parent.parent / dest_status / src.name
    if dest.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {dest}")
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(text, encoding="utf-8", newline="")
    src.unlink()
    return dest


def move(tool: Tool, action: str, item: str, approved: bool = False, when: str | None = None) -> Path:
    src_status, dest_status = TRANSITIONS[action]
    src = tool.find_item(item, src_status)
    slug, status = tool.locate(src)
    if status != src_status:
        raise SystemExit(f"{action} expects a {tool.nouns['item']} in {src_status}/, but it is in {status}/")

    text = src.read_text(encoding="utf-8")
    fm, _ = read_item(src)

    if action == "finalize":
        if not approved:
            raise SystemExit("Refusing to finalize without --approved (operator approval is required)")
        errors, _ = validate_item(tool, src)
        if errors:
            raise SystemExit("Fix these before finalizing:\n  - " + "\n  - ".join(errors))
        if fm.get("fact_check") != "passed":
            raise SystemExit(f"fact_check is {fm.get('fact_check')!r}; it must be 'passed' (run /finalize)")
    elif action == "publish":
        published = when or today()
        if not is_iso_date(published):
            raise SystemExit(f"Invalid date {published!r}: use YYYY-MM-DD")
        if published > today():
            raise SystemExit(f"Published date {published} is in the future")
        if published < str(fm.get("created") or ""):
            raise SystemExit(f"Published date {published} is before the {tool.nouns['item']} was created ({fm.get('created')})")
        text = set_field(text, "published", published)
    elif action == "reopen":
        text = set_field(text, "fact_check", "pending")

    dest = _write_moved(src, text, dest_status)
    print(f"{slug}: {src_status}/{src.name} -> {dest_status}/{dest.name}")
    return dest


def run(tool: Tool, args: argparse.Namespace) -> None:
    move(tool, args.action, args.item, approved=args.approved, when=args.date)


def register(sub, tool: Tool) -> None:
    p = sub.add_parser("move", help=f"move a {tool.nouns['item']} to its next status folder",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("action", choices=TRANSITIONS)
    p.add_argument("item", help=f"{tool.nouns['item']} file path or filename")
    p.add_argument("--approved", action="store_true",
                   help=f"finalize only: the operator explicitly approved this {tool.nouns['item']}")
    p.add_argument("--date", default=None, help="publish only: publishing date YYYY-MM-DD (default today)")
    p.set_defaults(func=run)
