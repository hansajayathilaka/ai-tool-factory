"""Print an item in a copy-paste format for publishing by hand.

  export <item> [--format txt|md|html] [--out <file>]

Exports the sections listed in tool.json -> export.sections. txt is the plain text,
md keeps a "## Section" heading per section, html is md converted to simple HTML.
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from .frontmatter import read_item, sections
from .tool import Tool

INLINE = (
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*(.+?)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])"), r"<em>\1</em>"),
    (re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)"), r'<a href="\2">\1</a>'),
)
LIST_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+")


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    for pattern, repl in INLINE:
        text = pattern.sub(repl, text)
    return text


def markdown_to_html(md: str) -> str:
    """Headings, paragraphs, lists, quotes, bold, italics, code and links. Enough for pasting into a CMS."""
    out = []
    for block in re.split(r"\n\s*\n", md.strip()):
        lines = block.splitlines()
        heading = re.match(r"^(#{1,6})\s+(.*)$", block)
        if heading and len(lines) == 1:
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
        elif all(LIST_RE.match(line) for line in lines):
            tag = "ol" if re.match(r"^\s*\d+\.", lines[0]) else "ul"
            items = "".join(f"<li>{_inline(LIST_RE.sub('', line))}</li>" for line in lines)
            out.append(f"<{tag}>{items}</{tag}>")
        elif all(line.startswith(">") for line in lines):
            inner = "<br>\n".join(_inline(line.lstrip("> ").rstrip()) for line in lines)
            out.append(f"<blockquote><p>{inner}</p></blockquote>")
        else:
            out.append("<p>" + "<br>\n".join(_inline(line) for line in lines) + "</p>")
    return "\n".join(out)


def export_item(tool: Tool, path: Path, fmt: str) -> str:
    _, body = read_item(path)
    secs = sections(body)
    names = tool.export.get("sections") or [tool.main_section]
    parts = [(name, secs.get(name, "").strip()) for name in names]
    parts = [(name, text) for name, text in parts if text]
    if fmt == "txt":
        return "\n\n".join(text for _, text in parts)
    md = "\n\n".join(f"## {name}\n\n{text}" for name, text in parts)
    return md if fmt == "md" else markdown_to_html(md)


def run(tool: Tool, args: argparse.Namespace) -> None:
    formats = tool.export.get("formats") or ["txt"]
    fmt = args.format or formats[0]
    if fmt not in formats:
        raise SystemExit(f"{tool.name} exports {', '.join(formats)}, not {fmt} (tool.json -> export.formats)")
    text = export_item(tool, tool.find_item(args.item), fmt)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(text)


def register(sub, tool: Tool) -> None:
    p = sub.add_parser("export", help=f"print a {tool.nouns['item']} for copy-paste publishing",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("item", help=f"{tool.nouns['item']} file path or filename")
    p.add_argument("--format", choices=("txt", "md", "html"), help="default: the first of export.formats")
    p.add_argument("--out", type=Path, help="write to this file instead of printing")
    p.set_defaults(func=run)
