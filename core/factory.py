"""Studio commands for building and checking tools. studio/factory.py calls main().

  new-tool <name>       copy templates/tool/ to tools/<name>/
  check-tool <name>     manifest, required files, leftover TODOs, _test fixtures
  list                  every tool with its item and channel nouns
  test                  run the core unit tests
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from .common import REPO_DIR, STATUS_FOLDERS, TOOLS_DIR, utf8_stdout
from .scaffold import run_new_tool
from .tool import Tool, check_manifest
from .validate import report, validate_item

REQUIRED_FILES = (
    "tool.json", "CLAUDE.md", "run.py", ".claude/settings.json", ".claude/agents/writer.md",
    "templates/item.md", "templates/channel/profile.md", "templates/channel/sources.md",
    "channels/_test/profile.md", "channels/_test/sources.md",
)
# Files that must not keep the template's TODO markers once a tool is built.
# (Channel templates keep theirs: /new-channel fills them per channel.)
NO_TODO_FILES = ("tool.json", "CLAUDE.md", ".claude/agents/writer.md", "templates/item.md")
FIXTURES = "channels/_test/fixtures"
TODO_RE = re.compile(r"(?<!`)\bTODO\b(?!`)")  # `TODO` in backticks is a mention, not a marker


def tool_dirs() -> list[Path]:
    return sorted(p for p in TOOLS_DIR.iterdir() if (p / "tool.json").is_file())


def check_tool(tool_dir: Path, verbose: bool = False) -> list[str]:
    """Return every problem with a tool; an empty list means it is ready to use."""
    problems = [f"missing file: {f}" for f in REQUIRED_FILES if not (tool_dir / f).is_file()]
    if not (tool_dir / "tool.json").is_file():
        return problems
    try:
        manifest = json.loads((tool_dir / "tool.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return problems + [f"tool.json: invalid JSON: {exc}"]
    manifest_problems = check_manifest(manifest)
    if manifest_problems:
        return problems + [f"tool.json: {p}" for p in manifest_problems]
    tool = Tool(tool_dir, manifest)
    if tool.name != tool_dir.name:
        problems.append(f"tool.json name {tool.name!r} does not match folder {tool_dir.name!r}")

    for f in NO_TODO_FILES:
        path = tool_dir / f
        if path.is_file() and TODO_RE.search(path.read_text(encoding="utf-8")):
            problems.append(f"{f} still contains TODO")

    settings = tool_dir / ".claude/settings.json"
    if settings.is_file():
        try:
            if json.loads(settings.read_text(encoding="utf-8")).get("autoMemoryEnabled") is not False:
                problems.append(".claude/settings.json must set \"autoMemoryEnabled\": false")
        except json.JSONDecodeError as exc:
            problems.append(f".claude/settings.json: invalid JSON: {exc}")
    if (tool_dir / ".claude/skills").is_dir() and (TOOLS_DIR / ".claude/skills").is_dir():
        shared = {p.name for p in (TOOLS_DIR / ".claude/skills").iterdir()}
        clash = sorted(p.name for p in (tool_dir / ".claude/skills").iterdir() if p.name in shared)
        if clash:
            problems.append(f"tool skills reuse shared skill names (the tool's copy would win): {', '.join(clash)}")

    if not tool.placeholders:
        problems.append("templates/item.md has no <placeholders>; unfinished items could not be detected")
    else:
        template_errors, _ = validate_item(tool, tool.templates_dir / "item.md", ("_test", "drafts"))
        if not any("placeholder" in e for e in template_errors):
            problems.append("an unedited copy of templates/item.md passes validation")

    results = []
    valid = sorted((tool_dir / FIXTURES / "valid").glob("*.md"))
    invalid = sorted((tool_dir / FIXTURES / "invalid").glob("*.md"))
    if not valid:
        problems.append(f"no valid fixture in {FIXTURES}/valid/")
    if not invalid:
        problems.append(f"no invalid fixture in {FIXTURES}/invalid/")
    for path in valid:
        errors, warnings = validate_item(tool, path, ("_test", "drafts"))
        results.append((path, errors, warnings))
        if errors:
            problems.append(f"valid fixture fails: {path.name}: {errors[0]}")
    for path in invalid:
        errors, warnings = validate_item(tool, path, ("_test", "drafts"))
        results.append((path, errors, warnings))
        if not errors:
            problems.append(f"invalid fixture passes: {path.name}")
    for status in STATUS_FOLDERS:
        for path in sorted((tool_dir / "channels/_test" / status).glob("*.md")):
            errors, warnings = validate_item(tool, path)
            results.append((path, errors, warnings))
            if errors:
                problems.append(f"_test item fails: {status}/{path.name}: {errors[0]}")
    if verbose and results:
        report(tool, results)
        print()
    return problems


def run_check_tool(args: argparse.Namespace) -> None:
    names = [p.name for p in tool_dirs()] if args.name == "all" else [args.name]
    failed = 0
    for name in names:
        tool_dir = TOOLS_DIR / name
        if not tool_dir.is_dir():
            raise SystemExit(f"No tool folder: {tool_dir}")
        print(f"## {name}\n")
        problems = check_tool(tool_dir, verbose=True)
        for p in problems:
            print(f"- {p}")
        print("OK: ready to use\n" if not problems else f"\n{len(problems)} problem(s)\n")
        failed += bool(problems)
    sys.exit(1 if failed else 0)


def run_list(args: argparse.Namespace) -> None:
    print("| Tool | Item | Channel | Platform | Channels |")
    print("|---|---|---|---|---|")
    for d in tool_dirs():
        tool = Tool.load(d)
        channels = sorted(p.name for p in tool.channels_dir.iterdir() if p.is_dir()) if tool.channels_dir.is_dir() else []
        print(f"| {tool.name} | {tool.nouns['item']} | {tool.nouns['channel']} | {tool.nouns['platform']} | "
              f"{', '.join(channels) or '-'} |")


def run_test(args: argparse.Namespace) -> None:
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "core/tests"] + (["-v"] if args.verbose else [])
    sys.exit(subprocess.call(cmd, cwd=REPO_DIR))


def main(argv: list[str] | None = None) -> None:
    utf8_stdout()
    parser = argparse.ArgumentParser(prog="python factory.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    p = sub.add_parser("new-tool", help="copy templates/tool/ to tools/<name>/")
    p.add_argument("name", help="tool folder name: lowercase letters, digits, hyphens")
    p.set_defaults(func=run_new_tool)
    p = sub.add_parser("check-tool", help="check a tool is complete and its _test fixtures behave")
    p.add_argument("name", help="tool name, or 'all'")
    p.set_defaults(func=run_check_tool)
    sub.add_parser("list", help="list tools").set_defaults(func=run_list)
    p = sub.add_parser("test", help="run the core unit tests")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=run_test)
    args = parser.parse_args(argv)
    args.func(args)
