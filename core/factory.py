"""Studio commands for building and checking tools. studio/factory.py calls main().

  new-tool <name>               copy templates/tool/ to tools/<name>/
  check-tool <name>             manifest, required files, leftover TODOs, _test fixtures, MCP servers
  check-studio                  root files, every command's frontmatter, unique names, proxy agents, .mcp.json
  new-command <name> --in <at>  copy templates/command/ to root, studio, shared or a tool's .claude/skills/
  mcp                           project MCP servers and which tools use them
  list                          every tool with its item and channel nouns
  test                          run the core unit tests
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from . import mcp
from .common import (COMMAND_TEMPLATE, REPO_DIR, ROOT_CLAUDE_DIR, STATUS_FOLDERS, STUDIO_DIR, TOOL_NAME_RE,
                     TOOLS_DIR, utf8_stdout)
from .frontmatter import parse_frontmatter, split_frontmatter
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
# What a root launch needs: the router, the permissions for every mode, MCP servers and the root commands.
ROOT_FILES = ("CLAUDE.md", ".claude/settings.json", ".mcp.json",
              *(f".claude/skills/{c}/SKILL.md" for c in ("start", "help", "load-studio", "load-tool", "build-studio")))
GLOBAL_SCOPES = ("root", "studio", "shared")
ARGUMENTS_RE = re.compile(r"\$(?:ARGUMENTS|\d)")


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

    servers, _ = mcp.load_config()
    problems += mcp.tool_problems(tool, servers)
    problems += proxy_problems(tool_dir / ".claude/agents")

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


def _frontmatter(path: Path) -> dict | None:
    try:
        return parse_frontmatter(split_frontmatter(path.read_text(encoding="utf-8"))[0])
    except ValueError:
        return None


def skill_roots() -> dict[str, Path]:
    """Where commands live: root (every mode), studio, shared (every tool), then one entry per tool."""
    roots = {"root": ROOT_CLAUDE_DIR / "skills", "studio": STUDIO_DIR / ".claude/skills",
             "shared": TOOLS_DIR / ".claude/skills"}
    roots.update({d.name: d / ".claude/skills" for d in tool_dirs()})
    return roots


def check_skill(path: Path) -> list[str]:
    """Return every problem with one command's SKILL.md."""
    meta = _frontmatter(path)
    if meta is None:
        return ["does not start with a --- frontmatter block"]
    text = path.read_text(encoding="utf-8")
    problems = []
    if meta.get("name") != path.parent.name:
        problems.append(f"name must match its folder ({path.parent.name})")
    if not meta.get("description"):
        problems.append("description is required")
    if ARGUMENTS_RE.search(text) and not meta.get("argument-hint"):
        problems.append("uses $ARGUMENTS but has no argument-hint")
    if TODO_RE.search(text):
        problems.append("still contains TODO")
    return problems


def agent_signature(path: Path) -> tuple[str | None, frozenset[str]]:
    meta = _frontmatter(path) or {}
    return meta.get("name"), frozenset(t.strip() for t in str(meta.get("tools") or "").split(",") if t.strip())


def proxy_problems(agents_dir: Path) -> list[str]:
    """Every agent under tools/ needs a same-named proxy with the same tools in the root .claude/agents/:
    a session launched at the repo root finds agents only there (Claude Code walks up, never down)."""
    problems = []
    for path in sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []:
        name, tools = agent_signature(path)
        rel = path.relative_to(REPO_DIR).as_posix() if path.is_relative_to(REPO_DIR) else path.name
        proxy = ROOT_CLAUDE_DIR / "agents" / f"{name}.md"
        if not name:
            problems.append(f"{rel}: frontmatter needs a name")
        elif not proxy.is_file():
            problems.append(f"{rel}: no root proxy .claude/agents/{name}.md, so root sessions cannot run it")
        elif agent_signature(proxy) != (name, tools):
            problems.append(f"{rel}: root proxy .claude/agents/{name}.md must have name {name!r} "
                            f"and tools: {', '.join(sorted(tools))}")
    return problems


def check_studio() -> list[str]:
    """Return every problem with the studio itself; an empty list means root sessions will work."""
    problems = [f"missing file: {f}" for f in ROOT_FILES if not (REPO_DIR / f).is_file()]
    settings = REPO_DIR / ".claude/settings.json"
    if settings.is_file():
        try:
            if json.loads(settings.read_text(encoding="utf-8")).get("autoMemoryEnabled") is not False:
                problems.append(".claude/settings.json must set \"autoMemoryEnabled\": false")
        except json.JSONDecodeError as exc:
            problems.append(f".claude/settings.json: invalid JSON: {exc}")

    owners: dict[str, str] = {}  # command name -> scope, for root, studio and shared commands
    for scope, root in skill_roots().items():
        for path in sorted(root.glob("*/SKILL.md")) if root.is_dir() else []:
            rel = path.relative_to(REPO_DIR).as_posix()
            problems += [f"{rel}: {p}" for p in check_skill(path)]
            name = path.parent.name
            if name in owners:
                problems.append(f"{rel}: /{name} is already a {owners[name]} command; command names must be unique")
            elif scope in GLOBAL_SCOPES:
                owners[name] = scope

    problems += proxy_problems(TOOLS_DIR / ".claude/agents")
    for d in tool_dirs():
        problems += proxy_problems(d / ".claude/agents")
    problems += mcp.load_config()[1]
    return problems


def new_command(name: str, where: str) -> Path:
    roots = skill_roots()
    if where not in roots:
        raise SystemExit(f"Unknown place {where!r}: use one of {', '.join(roots)}")
    if not TOOL_NAME_RE.match(name):
        raise SystemExit(f"Invalid command name {name!r}: use lowercase letters, digits and hyphens")
    taken = {p.parent.name: s for s, r in roots.items() if r.is_dir() for p in r.glob("*/SKILL.md")}
    if name in taken:
        raise SystemExit(f"/{name} already exists ({taken[name]}); command names must be unique")
    dest = roots[where] / name / "SKILL.md"
    dest.parent.mkdir(parents=True)
    dest.write_text(COMMAND_TEMPLATE.read_text(encoding="utf-8").replace("{{name}}", name), encoding="utf-8")
    return dest


def run_new_command(args: argparse.Namespace) -> None:
    dest = new_command(args.name, args.where)
    print(f"Created {dest.relative_to(REPO_DIR).as_posix()}: replace every TODO, then run check-studio.")


def run_check_studio(args: argparse.Namespace) -> None:
    problems = check_studio()
    for p in problems:
        print(f"- {p}")
    print("OK: studio is consistent" if not problems else f"\n{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


def run_mcp(args: argparse.Namespace) -> None:
    servers, problems = mcp.load_config()
    print("## Project MCP servers (.mcp.json)\n")
    if servers:
        print("| Server | Type | Runs |\n|---|---|---|")
        for name, s in servers.items():
            if isinstance(s, dict):
                print(f"| {name} | {mcp.server_type(s)} | {mcp.target(s)} |")
    else:
        print("none configured")
    print("\n## Servers each tool may use (tool.json mcp)\n")
    print("| Tool | Server | Status |\n|---|---|---|")
    for d in tool_dirs():
        tool = Tool.load(d)
        for name in tool.mcp_servers:
            print(f"| {tool.name} | {name} | {mcp.status(name, servers)} |")
        if not tool.mcp_servers:
            print(f"| {tool.name} | - | none declared |")
        problems += mcp.tool_problems(tool, servers)
    if problems:
        print("\n" + "\n".join(f"- {p}" for p in problems))
    print("\nConnection state: run /mcp inside Claude Code.")
    sys.exit(1 if problems else 0)


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
    parser = argparse.ArgumentParser(prog="python studio/factory.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    p = sub.add_parser("new-tool", help="copy templates/tool/ to tools/<name>/")
    p.add_argument("name", help="tool folder name: lowercase letters, digits, hyphens")
    p.set_defaults(func=run_new_tool)
    p = sub.add_parser("check-tool", help="check a tool is complete and its _test fixtures behave")
    p.add_argument("name", help="tool name, or 'all'")
    p.set_defaults(func=run_check_tool)
    sub.add_parser("check-studio", help="check root files, commands, proxy agents and .mcp.json"
                   ).set_defaults(func=run_check_studio)
    p = sub.add_parser("new-command", help="create a command from templates/command/")
    p.add_argument("name", help="command name: lowercase letters, digits, hyphens")
    p.add_argument("--in", dest="where", required=True,
                   help="root (every mode), studio, shared (every tool) or a tool name")
    p.set_defaults(func=run_new_command)
    sub.add_parser("mcp", help="list project MCP servers and which tools use them").set_defaults(func=run_mcp)
    sub.add_parser("list", help="list tools").set_defaults(func=run_list)
    p = sub.add_parser("test", help="run the core unit tests")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=run_test)
    args = parser.parse_args(argv)
    args.func(args)
