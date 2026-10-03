"""Markdown files with a --- frontmatter block: parse, edit one field, split into sections.

A small YAML subset: top-level scalars, one level of nested mapping, and lists of
scalars or of flat mappings. That covers item and research note files.
"""
from __future__ import annotations

import re
from pathlib import Path

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


def read_item(path: Path) -> tuple[dict, str]:
    """Return (frontmatter, body) of an item or research note."""
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
