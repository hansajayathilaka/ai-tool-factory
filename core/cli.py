"""Entry point for a tool's commands. Each tool's run.py calls main(tool_dir=<that tool's folder>)."""
from __future__ import annotations

import argparse
from pathlib import Path

from . import export, insights, lifecycle, scaffold, topics, validate
from .common import STATUS_FOLDERS, utf8_stdout
from .sources import reddit, rss
from .tool import Tool

COMMANDS = (validate, lifecycle, topics, rss, reddit, insights, scaffold, export)


def info(tool: Tool, args: argparse.Namespace) -> None:
    """Print what the shared skills need to know about this tool, from tool.json."""
    m, n = tool.manifest, tool.nouns
    print(f"# {tool.name}: {m['description']}\n")
    print(f"- item: {n['item']} ({n['items']}); channel: {n['channel']} ({n['channels']})")
    print(f"- published by hand on {n['platform']} (verb: {n['publish_verb']})")
    print(f"- notes per item: {m['notes_per_item']}; main section: {m['main_section']}")
    print(f"- status folders: {' -> '.join(STATUS_FOLDERS)}")
    fm = tool.frontmatter_rules
    print(f"- required frontmatter: {', '.join(('channel', 'topic', 'created', 'sources', 'fact_check', *fm.get('required', [])))}")
    for key, values in fm.get("enums", {}).items():
        print(f"  - {key}: {' | '.join(values)}")
    print(f"- image: {tool.rules.get('image', 'none')}")
    print("- sections:")
    for s in tool.sections:
        limits = ", ".join(f"{k} {v}" for k, v in s.items() if k not in ("name", "required"))
        print(f"  - ## {s['name']} ({'required' if s.get('required') else 'optional'}{', ' + limits if limits else ''})")
    if tool.rules.get("blocked_domains") or tool.rules.get("banned_phrases"):
        print(f"- extra blocked domains: {', '.join(tool.rules.get('blocked_domains', [])) or 'none'}")
        print(f"- extra banned phrases: {', '.join(tool.rules.get('banned_phrases', [])) or 'none'}")
    print(f"- export: {', '.join(tool.export.get('formats', [])) or 'none'}")
    print(f"- MCP servers: {', '.join(tool.mcp_servers) or 'none'}")
    channels = sorted(p.name for p in tool.channels_dir.iterdir() if p.is_dir()) if tool.channels_dir.is_dir() else []
    print(f"- {n['channels']}: {', '.join(channels) or 'none yet'}")


def main(tool_dir: Path, argv: list[str] | None = None) -> None:
    utf8_stdout()
    tool = Tool.load(tool_dir)
    parser = argparse.ArgumentParser(prog="python run.py", description=f"{tool.name}: {tool.manifest['description']}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    p = sub.add_parser("info", help="summary of tool.json: nouns, sections, limits, channels")
    p.set_defaults(func=info)
    for module in COMMANDS:
        module.register(sub, tool)
    args = parser.parse_args(argv)
    args.func(tool, args)
