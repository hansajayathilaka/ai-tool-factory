"""Create a channel from the tool's templates/channel/, or a tool from templates/tool/.

  new-channel <slug> --name "Channel Name"      (tool command, run.py)
  new-tool <name>                                (studio command, factory.py)
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .common import CHANNEL_FOLDERS, SLUG_RE, TOOL_NAME_RE, TOOL_TEMPLATE_DIR, TOOLS_DIR, today
from .tool import Tool

TEXT_SUFFIXES = (".md", ".json", ".py", ".txt")
SKIP = shutil.ignore_patterns("__pycache__", "*.pyc", ".env")


def _fill(folder: Path, replacements: dict[str, str]) -> None:
    for path in folder.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            for old, new in replacements.items():
                text = text.replace(old, new)
            path.write_text(text, encoding="utf-8")


def _list(folder: Path, base: Path) -> None:
    print(f"Created {folder.relative_to(base).as_posix()}")
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            print(f"  {path.relative_to(folder).as_posix()}")


def new_channel(tool: Tool, slug: str, name: str) -> Path:
    if not SLUG_RE.match(slug):
        raise SystemExit(f"Invalid slug {slug!r}: use lowercase letters, digits and hyphens")
    template = tool.templates_dir / "channel"
    if not template.is_dir():
        raise SystemExit(f"Missing channel template: {template}")
    dest = tool.channels_dir / slug
    if dest.exists():
        raise SystemExit(f"{tool.nouns['channel'].capitalize()} already exists: {dest}")
    shutil.copytree(template, dest, ignore=SKIP)
    for folder in CHANNEL_FOLDERS:
        (dest / folder).mkdir(exist_ok=True)
        if not any((dest / folder).iterdir()):
            (dest / folder / ".gitkeep").touch()
    _fill(dest, {"{{slug}}": slug, "{{channel_name}}": name, "{{created}}": today(), "{{tool}}": tool.name})
    return dest


def new_tool(name: str) -> Path:
    if not TOOL_NAME_RE.match(name) or name in ("shared", "root", "studio"):
        raise SystemExit(f"Invalid tool name {name!r}: use lowercase letters, digits and hyphens "
                         "(not 'shared', 'root' or 'studio')")
    dest = TOOLS_DIR / name
    if dest.exists():
        raise SystemExit(f"Tool already exists: {dest}")
    shutil.copytree(TOOL_TEMPLATE_DIR, dest, ignore=SKIP)
    (dest / "channels").mkdir(exist_ok=True)
    _fill(dest, {"{{tool}}": name, "{{created}}": today()})
    return dest


def run_new_channel(tool: Tool, args: argparse.Namespace) -> None:
    _list(new_channel(tool, args.slug, args.name), tool.dir)


def run_new_tool(args: argparse.Namespace) -> None:
    _list(new_tool(args.name), TOOLS_DIR.parent)


def register(sub, tool: Tool) -> None:
    p = sub.add_parser("new-channel", help=f"create a {tool.nouns['channel']} from templates/channel/",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("slug", help=f"{tool.nouns['channel']} folder name: lowercase letters, digits, hyphens")
    p.add_argument("--name", required=True, help=f"display name of the {tool.nouns['channel']}")
    p.set_defaults(func=run_new_channel)
