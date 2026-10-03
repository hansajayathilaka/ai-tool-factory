"""Move a post between status folders. The folder is the post's status.

  finalize <draft>      drafts/    -> finalized/  (needs fact_check: passed and --approved)
  posted <finalized>    finalized/ -> posted/     (sets posted: date)
  reopen <finalized>    finalized/ -> drafts/     (resets fact_check: pending)

A post can be given as a path or as a bare filename.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import common

TRANSITIONS = {
    "finalize": ("drafts", "finalized"),
    "posted": ("finalized", "posted"),
    "reopen": ("finalized", "drafts"),
}


def move(src: Path, text: str, dest_status: str) -> Path:
    dest = src.parent.parent / dest_status / src.name
    if dest.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {dest}")
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(text, encoding="utf-8", newline="")
    src.unlink()
    return dest


def main() -> None:
    common.utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=TRANSITIONS)
    parser.add_argument("post", help="post file path or filename")
    parser.add_argument("--approved", action="store_true",
                        help="finalize only: the operator explicitly approved this post")
    parser.add_argument("--date", default=None, help="posted only: posting date YYYY-MM-DD (default today)")
    args = parser.parse_args()

    src_status, dest_status = TRANSITIONS[args.action]
    src = common.find_post(args.post, src_status)
    slug, status = common.page_of(src)
    if status != src_status:
        raise SystemExit(f"{args.action} expects a post in {src_status}/, but it is in {status}/")

    text = src.read_text(encoding="utf-8")
    fm, _ = common.read_post(src)

    if args.action == "finalize":
        if not args.approved:
            raise SystemExit("Refusing to finalize without --approved (operator approval is required)")
        errors, _ = common.validate_post(src)
        if errors:
            raise SystemExit("Fix these before finalizing:\n  - " + "\n  - ".join(errors))
        if fm.get("fact_check") != "passed":
            raise SystemExit(f"fact_check is {fm.get('fact_check')!r}; it must be 'passed' (run /finalize-post)")
    elif args.action == "posted":
        posted = args.date or common.today()
        if not common.is_iso_date(posted):
            raise SystemExit(f"Invalid date {posted!r}: use YYYY-MM-DD")
        if posted < str(fm.get("created") or ""):
            raise SystemExit(f"Posted date {posted} is before the post was created ({fm.get('created')})")
        text = common.set_field(text, "posted", posted)
    elif args.action == "reopen":
        text = common.set_field(text, "fact_check", "pending")

    dest = move(src, text, dest_status)
    print(f"{slug}: {src_status}/{src.name} -> {dest_status}/{dest.name}")


if __name__ == "__main__":
    main()
