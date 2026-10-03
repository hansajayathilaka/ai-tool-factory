"""Create facebook_pages/<slug>/ from templates/page/.

Usage: python utils/new_page.py <slug> --name "Page Name"
"""
from __future__ import annotations

import argparse
import shutil

import common


def main() -> None:
    common.utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug", help="page folder name: lowercase letters, digits, hyphens")
    parser.add_argument("--name", required=True, help="display name of the Facebook page")
    args = parser.parse_args()

    if not common.SLUG_RE.match(args.slug):
        raise SystemExit(f"Invalid slug {args.slug!r}: use lowercase letters, digits and hyphens")
    dest = common.PAGES_DIR / args.slug
    if dest.exists():
        raise SystemExit(f"Page already exists: {dest}")

    shutil.copytree(common.TEMPLATES_DIR / "page", dest)
    replacements = {"{{slug}}": args.slug, "{{page_name}}": args.name, "{{created}}": common.today()}
    for path in dest.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")

    print(f"Created {dest.relative_to(common.APP_DIR).as_posix()}")
    for path in sorted(dest.rglob("*")):
        if path.is_file():
            print(f"  {path.relative_to(dest).as_posix()}")


if __name__ == "__main__":
    main()
