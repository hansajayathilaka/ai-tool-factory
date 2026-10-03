"""Paths, constants and small helpers shared by every core module."""
from __future__ import annotations

import os
import re
import sys
from datetime import date
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_DIR / "tools"
SHARED_DIR = TOOLS_DIR / "shared"
TOOL_TEMPLATE_DIR = REPO_DIR / "templates" / "tool"

# A file's folder is its status. Items move between these only through lifecycle.py.
STATUS_FOLDERS = ("drafts", "finalized", "published")
CHANNEL_FOLDERS = ("research", *STATUS_FOLDERS, "insights")

SLUG_RE = re.compile(r"^_?[a-z0-9]+(?:-[a-z0-9]+)*$")
TOOL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ITEM_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def utf8_stdout() -> None:
    """Make stdout/stderr UTF-8 so Sinhala/Tamil text prints on Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def load_env(tool_dir: Path | None = None) -> None:
    """Load KEY=VALUE pairs from .env in the tool folder or the repo root without overriding real env vars."""
    candidates = [tool_dir / ".env"] if tool_dir else []
    for path in (*candidates, REPO_DIR / ".env"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


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
