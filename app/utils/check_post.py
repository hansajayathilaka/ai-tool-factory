"""Validate post files against templates/post.md and shared/style_guide.md.

Usage:
  python utils/check_post.py <file> [<file> ...]
  python utils/check_post.py --page <slug> [--status drafts|finalized|posted]

Exit code 1 if any file has errors. Warnings do not fail the check.
"""
from __future__ import annotations

import argparse
import sys

import common


def main() -> None:
    common.utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="post files (path or filename)")
    parser.add_argument("--page", help="check every post of this page")
    parser.add_argument("--status", choices=common.STATUS_FOLDERS, help="with --page: only this folder")
    args = parser.parse_args()

    paths = [common.find_post(f) for f in args.files]
    if args.page:
        page = common.page_dir(args.page)
        for status in ([args.status] if args.status else common.STATUS_FOLDERS):
            paths.extend(sorted((page / status).glob("*.md")))
    if not paths and not args.page:
        parser.error("no post files given (pass files or --page)")

    failed = 0
    for path in paths:
        errors, warnings = common.validate_post(path)
        rel = path.relative_to(common.APP_DIR) if path.is_relative_to(common.APP_DIR) else path
        print(f"{'FAIL' if errors else 'OK  '} {rel.as_posix()}")
        for e in errors:
            print(f"     error:   {e}")
        for w in warnings:
            print(f"     warning: {w}")
        failed += bool(errors)
    print(f"\n{len(paths)} checked, {failed} with errors")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
