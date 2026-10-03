"""Validate item files against the tool's tool.json and the shared style guide.

  check <file> [<file> ...]
  check --channel <slug> [--status drafts|finalized|published]

Exit code 1 if any file has errors. Warnings do not fail the check.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

from .common import ITEM_NAME_RE, STATUS_FOLDERS, is_iso_date
from .frontmatter import parse_frontmatter, sections, split_frontmatter
from .tool import Tool

# Keys every item has, whatever the tool. tool.json → frontmatter.required adds to these.
CORE_KEYS = ("channel", "topic", "created", "sources", "fact_check")
FACT_CHECK_VALUES = ("pending", "passed", "failed")
# Never research sources, for any tool (README non-goals). tool.json → rules.blocked_domains adds to these.
BLOCKED_DOMAINS = ("facebook.com", "instagram.com", "threads.net")
# Lower-cased phrases that signal engagement bait (see tools/shared/style_guide.md §4).
ENGAGEMENT_BAIT = (
    "comment yes", "type yes", "type amen", "comment amen", "like if",
    "share if", "tag a friend", "tag someone", "share before", "like and share",
    "share this post", "you won't believe", "comment below if",
)
HASHTAG_RE = re.compile(r"(?<!\w)#\w+")


def _lookup(fm: dict, key: str):
    """Return (parent_ok, value) for 'key' or 'parent.child'. parent_ok is False when the parent is absent."""
    if "." not in key:
        return True, fm.get(key)
    parent, child = key.split(".", 1)
    if not isinstance(fm.get(parent), dict):
        return False, None
    return True, fm[parent].get(child)


def _blocked(url: str, domains) -> str | None:
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return next((d for d in domains if host == d or host.endswith("." + d)), None)


def validate_item(tool: Tool, path: Path, location: tuple[str, str] | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for an item file.

    location overrides the (channel, status) taken from the path, for fixtures kept outside the status folders.
    """
    errors: list[str] = []
    warnings: list[str] = []
    item = tool.nouns["item"]
    if not ITEM_NAME_RE.match(path.name):
        errors.append("filename must be YYYY-MM-DD-<topic-slug>.md (lowercase, hyphens)")
    try:
        text = path.read_text(encoding="utf-8")
        block, body = split_frontmatter(text)
        fm = parse_frontmatter(block)
    except (ValueError, UnicodeDecodeError) as exc:
        return [f"cannot read frontmatter: {exc}"], warnings

    fm_rules = tool.frontmatter_rules
    for key in dict.fromkeys((*CORE_KEYS, *fm_rules.get("required", []))):
        _, value = _lookup(fm, key)
        if value in (None, "", []):
            errors.append(f"missing frontmatter field: {key}")

    if location is None:
        try:
            location = tool.locate(path)
        except SystemExit:
            location = (None, None)
            warnings.append(f"file is not inside channels/<{tool.nouns['channel']}>/<status>/")
    slug, status = location
    if slug and fm.get("channel") and fm["channel"] != slug:
        errors.append(f"channel: {fm['channel']!r} does not match folder {slug!r}")
    if status and status not in STATUS_FOLDERS:
        errors.append(f"{item} is in {status}/, expected one of {', '.join(STATUS_FOLDERS)}")

    if fm.get("created") and not is_iso_date(fm["created"]):
        errors.append("created must be YYYY-MM-DD")
    if status == "published" and not is_iso_date(fm.get("published")):
        errors.append("published/ file needs published: YYYY-MM-DD")
    if status in ("drafts", "finalized") and fm.get("published"):
        warnings.append(f"published date is set but file is still in {status}/")

    sources = fm.get("sources")
    if sources is not None:
        if not isinstance(sources, list) or not all(isinstance(s, dict) and s.get("url") for s in sources):
            errors.append("each source needs a url")
        else:
            blocked = (*BLOCKED_DOMAINS, *tool.rules.get("blocked_domains", []))
            for i, s in enumerate(sources, 1):
                url = str(s["url"])
                if not url.startswith(("http://", "https://")):
                    errors.append(f"source [{i}] url is not http(s)")
                elif "example.com" in url:
                    errors.append(f"source [{i}] is still the template placeholder")
                domain = _blocked(url, blocked)
                if domain:
                    errors.append(f"source [{i}] is on {domain}, which is never a research source")

    nested = {k.split(".", 1)[0] for k in (*fm_rules.get("enums", {}), *fm_rules.get("booleans", [])) if "." in k}
    for parent in sorted(nested):
        if fm.get(parent) is not None and not isinstance(fm[parent], dict):
            errors.append(f"{parent} must be a mapping")
    for key, allowed in fm_rules.get("enums", {}).items():
        parent_ok, value = _lookup(fm, key)
        if parent_ok and ("." in key or value is not None) and value not in allowed:
            errors.append(f"{key} must be one of {', '.join(allowed)}")
    for key in fm_rules.get("booleans", []):
        parent_ok, value = _lookup(fm, key)
        if parent_ok and ("." in key or value is not None) and not isinstance(value, bool):
            errors.append(f"{key} must be true or false")

    image_rule = tool.rules.get("image", "none")
    image = fm.get("image")
    if image_rule != "none" and isinstance(image, dict):
        kind = image.get("kind")
        if image_rule == "required" and kind == "none":
            errors.append(f"image.kind cannot be none: every {item} needs an image")
        if kind == "ai-generated" and image.get("needs_ai_label") is False:
            warnings.append("AI-generated image with needs_ai_label: false; OK only if it is clearly not realistic")
        if kind != "none" and not image.get("idea"):
            errors.append("image.idea is required unless kind is none")
    elif image_rule == "required" and image is None and "image" not in fm_rules.get("required", []):
        errors.append(f"missing frontmatter field: image (every {item} needs an image)")

    if fm.get("fact_check") not in FACT_CHECK_VALUES:
        errors.append(f"fact_check must be one of {', '.join(FACT_CHECK_VALUES)}")
    if status in ("finalized", "published") and fm.get("fact_check") != "passed":
        errors.append(f"{item} in {status}/ must have fact_check: passed")

    secs = sections(body)
    for spec in tool.sections:
        name = spec["name"]
        content = secs.get(name)
        if not content:
            if spec.get("required"):
                errors.append(f"missing or empty section: ## {name}")
            continue
        if "max_chars" in spec and len(content) > spec["max_chars"]:
            errors.append(f"## {name} is {len(content)} characters; the limit is {spec['max_chars']}")
        if "max_hashtags" in spec:
            count = len(HASHTAG_RE.findall(content))
            if count > spec["max_hashtags"]:
                errors.append(f"## {name} has {count} hashtags; the limit is {spec['max_hashtags']}")
        words = len(content.split())
        if "min_words" in spec and words < spec["min_words"]:
            warnings.append(f"## {name} is {words} words; the target is at least {spec['min_words']}")
        if "max_words" in spec and words > spec["max_words"]:
            warnings.append(f"## {name} is {words} words; the target is at most {spec['max_words']}")

    left = next((p for p in tool.placeholders if p in text), None)
    if left:
        errors.append("template placeholder left in file: " + left)

    main = (secs.get(tool.main_section) or "").lower()
    for phrase in (*ENGAGEMENT_BAIT, *(p.lower() for p in tool.rules.get("banned_phrases", []))):
        if phrase in main:
            warnings.append(f"possible engagement bait in {tool.main_section}: {phrase!r}")
    return errors, warnings


def report(tool: Tool, results: list[tuple[Path, list[str], list[str]]]) -> int:
    """Print results; return the number of files with errors."""
    failed = 0
    for path, errors, warnings in results:
        print(f"{'FAIL' if errors else 'OK  '} {tool.rel(path)}")
        for e in errors:
            print(f"     error:   {e}")
        for w in warnings:
            print(f"     warning: {w}")
        failed += bool(errors)
    print(f"\n{len(results)} checked, {failed} with errors")
    return failed


def run(tool: Tool, args: argparse.Namespace) -> None:
    paths = [tool.find_item(f) for f in args.files]
    if args.channel:
        channel = tool.channel_dir(args.channel)
        for status in ([args.status] if args.status else STATUS_FOLDERS):
            paths.extend(sorted((channel / status).glob("*.md")))
    if not paths and not args.channel:
        raise SystemExit("no files given (pass files or --channel)")
    failed = report(tool, [(p, *validate_item(tool, p)) for p in paths])
    sys.exit(1 if failed else 0)


def register(sub, tool: Tool) -> None:
    p = sub.add_parser("check", help=f"validate {tool.nouns['items']} against tool.json",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="*", help=f"{tool.nouns['item']} files (path or filename)")
    p.add_argument("--channel", help=f"check every {tool.nouns['item']} of this {tool.nouns['channel']}")
    p.add_argument("--status", choices=STATUS_FOLDERS, help="with --channel: only this folder")
    p.set_defaults(func=run)
