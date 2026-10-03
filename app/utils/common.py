"""Shared helpers for the utils scripts. Standard library only."""
from __future__ import annotations

import os
import re
import sys
from datetime import date
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PAGES_DIR = APP_DIR / "facebook_pages"
TEMPLATES_DIR = APP_DIR / "templates"

STATUS_FOLDERS = ("drafts", "finalized", "posted")
SLUG_RE = re.compile(r"^_?[a-z0-9]+(?:-[a-z0-9]+)*$")
POST_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED_POST_KEYS = (
    "page", "topic", "pillar", "post_type", "language",
    "created", "sources", "image", "fact_check",
)
IMAGE_KINDS = ("none", "own-photo", "stock", "ai-generated")
FACT_CHECK_VALUES = ("pending", "passed", "failed")
REQUIRED_SECTIONS = ("Caption", "Hashtags", "Reviewer notes")

# Lower-cased phrases that signal engagement bait (see shared/style_guide.md §4).
ENGAGEMENT_BAIT = (
    "comment yes", "type yes", "type amen", "comment amen", "like if",
    "share if", "tag a friend", "tag someone", "share before", "like and share",
    "share this post", "you won't believe", "comment below if",
)

PLACEHOLDER_RE = re.compile(r"<(?:page-slug|short topic|content pillar[^>]*|post text|source title|"
                            r"tip \|[^>]*|description[^>]*|optional:[^>]*|claims to double-check[^>]*)>")


def utf8_stdout() -> None:
    """Make stdout/stderr UTF-8 so Sinhala/Tamil text prints on Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def load_env() -> None:
    """Load KEY=VALUE pairs from .env in app/ or the repo root without overriding real env vars."""
    for path in (APP_DIR / ".env", APP_DIR.parent / ".env"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def page_dir(slug: str) -> Path:
    if not SLUG_RE.match(slug):
        raise SystemExit(f"Invalid page slug: {slug!r} (use lowercase letters, digits and hyphens)")
    path = PAGES_DIR / slug
    if not path.is_dir():
        raise SystemExit(f"Page not found: {path}")
    return path


def today() -> str:
    return date.today().isoformat()


def is_iso_date(value) -> bool:
    if not isinstance(value, str) or not DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


# --- Frontmatter -----------------------------------------------------------
# A small YAML subset: top-level scalars, one level of nested mapping, and
# lists of scalars or of flat mappings. That covers post and research files.

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(.*)\Z", re.S)
KV_RE = re.compile(r"^([A-Za-z_][\w-]*):(?:\s+(.*))?$")


def split_frontmatter(text: str) -> tuple[str, str]:
    m = FRONTMATTER_RE.match(text.lstrip("﻿"))
    if not m:
        raise ValueError("file does not start with a --- frontmatter block")
    return m.group(1), m.group(2)


def _scalar(raw: str | None):
    if raw is None:
        return None
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    value = re.sub(r"\s+#.*$", "", value)
    if value in ("", "~", "null"):
        return None
    if value in ("true", "false"):
        return value == "true"
    if value == "[]":
        return []
    return value


def parse_frontmatter(block: str) -> dict:
    data: dict = {}
    key = None          # top-level key that owns the current nested block
    item = None         # current list item (dict) inside data[key]
    dash_indent = -1    # indent of the "- " that started `item`
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            m = KV_RE.match(line)
            if not m:
                raise ValueError(f"cannot parse frontmatter line: {raw!r}")
            item = None
            if m.group(2) is None or m.group(2).strip() == "":
                data[m.group(1)] = None
                key = m.group(1)
            else:
                data[m.group(1)] = _scalar(m.group(2))
                key = None
            continue
        if key is None:
            raise ValueError(f"unexpected indented line: {raw!r}")
        if line == "-" or line.startswith("- "):
            if data[key] is None:
                data[key] = []
            if not isinstance(data[key], list):
                raise ValueError(f"mixed list and mapping under {key!r}")
            rest = line[1:].strip()
            m = KV_RE.match(rest)
            if m:
                item = {m.group(1): _scalar(m.group(2))}
                dash_indent = indent
                data[key].append(item)
            else:
                item = None
                data[key].append(_scalar(rest))
            continue
        m = KV_RE.match(line)
        if not m:
            raise ValueError(f"cannot parse frontmatter line: {raw!r}")
        if isinstance(data[key], list):
            if item is None or indent <= dash_indent:
                raise ValueError(f"unexpected line in list {key!r}: {raw!r}")
            item[m.group(1)] = _scalar(m.group(2))
        else:
            if data[key] is None:
                data[key] = {}
            data[key][m.group(1)] = _scalar(m.group(2))
    return data


def read_post(path: Path) -> tuple[dict, str]:
    """Return (frontmatter, body) of a post or research note."""
    text = path.read_text(encoding="utf-8")
    block, body = split_frontmatter(text)
    return parse_frontmatter(block), body


def set_field(text: str, key: str, value: str) -> str:
    """Set a top-level scalar frontmatter field, keeping the rest of the file untouched."""
    block, body = split_frontmatter(text)
    line_re = re.compile(rf"^{re.escape(key)}:[^\n]*$", re.M)
    new_line = f"{key}: {value}".rstrip()
    if line_re.search(block):
        block = line_re.sub(lambda _: new_line, block, count=1)
    else:
        block = f"{block}\n{new_line}"
    newline = "\r\n" if "\r\n" in text else "\n"
    return f"---{newline}{block}{newline}---{newline}{body}"


def sections(body: str) -> dict[str, str]:
    """Map '## Heading' → text under it."""
    result: dict[str, str] = {}
    current = None
    lines: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current is not None:
                result[current] = "\n".join(lines).strip()
            current, lines = m.group(1), []
        elif current is not None:
            lines.append(line)
    if current is not None:
        result[current] = "\n".join(lines).strip()
    return result


def page_of(path: Path) -> tuple[str, str]:
    """Return (page_slug, status_folder) for a post path inside facebook_pages/."""
    path = path.resolve()
    try:
        rel = path.relative_to(PAGES_DIR.resolve())
    except ValueError:
        raise SystemExit(f"Not inside facebook_pages/: {path}")
    if len(rel.parts) != 3:
        raise SystemExit(f"Expected facebook_pages/<page>/<status>/<file>.md, got: {rel}")
    return rel.parts[0], rel.parts[1]


def find_post(arg: str, status: str | None = None) -> Path:
    """Resolve a post given as a path, or as a bare filename searched across pages."""
    path = Path(arg)
    candidates = [path, APP_DIR / path]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    folders = (status,) if status else STATUS_FOLDERS
    matches = [p for f in folders for p in PAGES_DIR.glob(f"*/{f}/{path.name}")]
    if len(matches) == 1:
        return matches[0].resolve()
    if not matches:
        raise SystemExit(f"Post not found: {arg}")
    raise SystemExit("Ambiguous post name, matches:\n  " + "\n  ".join(str(m) for m in matches))


def validate_post(path: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a post file."""
    errors: list[str] = []
    warnings: list[str] = []
    if not POST_NAME_RE.match(path.name):
        errors.append("filename must be YYYY-MM-DD-<topic-slug>.md (lowercase, hyphens)")
    try:
        text = path.read_text(encoding="utf-8")
        block, body = split_frontmatter(text)
        fm = parse_frontmatter(block)
    except (ValueError, UnicodeDecodeError) as exc:
        return [f"cannot read frontmatter: {exc}"], warnings

    for key in REQUIRED_POST_KEYS:
        if fm.get(key) in (None, "", []):
            errors.append(f"missing frontmatter field: {key}")

    try:
        slug, status = page_of(path)
    except SystemExit:
        slug, status = None, None
        warnings.append("file is not inside facebook_pages/<page>/<status>/")
    if slug and fm.get("page") and fm["page"] != slug:
        errors.append(f"page: {fm['page']!r} does not match folder {slug!r}")
    if status and status not in STATUS_FOLDERS:
        errors.append(f"post is in {status}/, expected one of {', '.join(STATUS_FOLDERS)}")

    if fm.get("created") and not is_iso_date(fm["created"]):
        errors.append("created must be YYYY-MM-DD")
    if status == "posted" and not is_iso_date(fm.get("posted")):
        errors.append("posted/ file needs posted: YYYY-MM-DD")
    if status in ("drafts", "finalized") and fm.get("posted"):
        warnings.append(f"posted date is set but file is still in {status}/")

    sources = fm.get("sources")
    if sources is not None:
        if not isinstance(sources, list) or not all(isinstance(s, dict) and s.get("url") for s in sources):
            errors.append("each source needs a url")
        else:
            for i, s in enumerate(sources, 1):
                if not str(s["url"]).startswith(("http://", "https://")):
                    errors.append(f"source [{i}] url is not http(s)")
                elif "example.com" in s["url"]:
                    errors.append(f"source [{i}] is still the template placeholder")
                if "facebook.com" in s["url"]:
                    errors.append(f"source [{i}] is a Facebook URL; Facebook is not a research source")

    image = fm.get("image")
    if image is not None:
        if not isinstance(image, dict):
            errors.append("image must be a mapping with kind / idea / needs_ai_label")
        else:
            if image.get("kind") not in IMAGE_KINDS:
                errors.append(f"image.kind must be one of {', '.join(IMAGE_KINDS)}")
            if not isinstance(image.get("needs_ai_label"), bool):
                errors.append("image.needs_ai_label must be true or false")
            if image.get("kind") == "ai-generated" and image.get("needs_ai_label") is False:
                warnings.append("AI-generated image with needs_ai_label: false; OK only if it is clearly not realistic")
            if image.get("kind") != "none" and not image.get("idea"):
                errors.append("image.idea is required unless kind is none")

    if fm.get("fact_check") not in FACT_CHECK_VALUES:
        errors.append(f"fact_check must be one of {', '.join(FACT_CHECK_VALUES)}")
    if status in ("finalized", "posted") and fm.get("fact_check") != "passed":
        errors.append(f"post in {status}/ must have fact_check: passed")

    secs = sections(body)
    for name in REQUIRED_SECTIONS:
        if not secs.get(name):
            errors.append(f"missing or empty section: ## {name}")

    if PLACEHOLDER_RE.search(text):
        errors.append("template placeholder left in file: " + PLACEHOLDER_RE.search(text).group(0))

    caption = (secs.get("Caption") or "").lower()
    for phrase in ENGAGEMENT_BAIT:
        if phrase in caption:
            warnings.append(f"possible engagement bait in caption: {phrase!r}")
    return errors, warnings
