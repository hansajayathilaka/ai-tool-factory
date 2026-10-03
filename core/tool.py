"""A tool is one Claude Code workspace in tools/<name>/, described by its tool.json manifest."""
from __future__ import annotations

import json
import re
from functools import cached_property
from pathlib import Path

from .common import SLUG_RE, STATUS_FOLDERS, TOOL_NAME_RE

NOUN_KEYS = ("item", "items", "channel", "channels", "publish_verb", "platform")
SECTION_LIMITS = ("max_chars", "max_hashtags", "min_words", "max_words")
IMAGE_RULES = ("none", "optional", "required")
EXPORT_FORMATS = ("txt", "md", "html")
TOP_LEVEL_KEYS = ("name", "description", "nouns", "notes_per_item", "main_section", "frontmatter",
                  "sections", "rules", "insights", "export", "mcp")
PLACEHOLDER_RE = re.compile(r"<(?!https?:|!--)[^<>\n]+>")
MCP_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _str_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value)


def check_manifest(m) -> list[str]:
    """Return every problem in a tool.json manifest; an empty list means it is valid."""
    if not isinstance(m, dict):
        return ["tool.json must be a JSON object"]
    problems = [f"unknown key: {k}" for k in m if k not in TOP_LEVEL_KEYS]

    if not isinstance(m.get("name"), str) or not TOOL_NAME_RE.match(m["name"]):
        problems.append("name must be lowercase letters, digits and hyphens")
    if not isinstance(m.get("description"), str) or not m["description"].strip():
        problems.append("description is required")

    nouns = m.get("nouns")
    if not isinstance(nouns, dict):
        problems.append(f"nouns must be an object with {', '.join(NOUN_KEYS)}")
    else:
        problems += [f"nouns.{k} must be a non-empty string" for k in NOUN_KEYS
                     if not isinstance(nouns.get(k), str) or not nouns[k].strip()]
        problems += [f"unknown key: nouns.{k}" for k in nouns if k not in NOUN_KEYS]

    if m.get("notes_per_item") not in ("one", "many"):
        problems.append('notes_per_item must be "one" or "many"')

    fm = m.get("frontmatter", {})
    if not isinstance(fm, dict):
        problems.append("frontmatter must be an object")
        fm = {}
    problems += [f"unknown key: frontmatter.{k}" for k in fm if k not in ("required", "enums", "booleans")]
    if not _str_list(fm.get("required", [])):
        problems.append("frontmatter.required must be a list of key names")
    enums = fm.get("enums", {})
    if not isinstance(enums, dict) or not all(_str_list(v) and v for v in enums.values()):
        problems.append("frontmatter.enums must map each key to a non-empty list of allowed values")
    if not _str_list(fm.get("booleans", [])):
        problems.append("frontmatter.booleans must be a list of key names")

    sections = m.get("sections")
    names: list[str] = []
    if not isinstance(sections, list) or not sections:
        problems.append("sections must be a non-empty list")
    else:
        for i, s in enumerate(sections, 1):
            if not isinstance(s, dict) or not isinstance(s.get("name"), str) or not s["name"].strip():
                problems.append(f"sections[{i}] needs a name")
                continue
            names.append(s["name"])
            for k, v in s.items():
                if k == "required":
                    if not isinstance(v, bool):
                        problems.append(f"sections[{i}].required must be true or false")
                elif k in SECTION_LIMITS:
                    if not isinstance(v, int) or isinstance(v, bool) or v < 1:
                        problems.append(f"sections[{i}].{k} must be a positive whole number")
                elif k != "name":
                    problems.append(f"unknown key: sections[{i}].{k}")
        if len(set(names)) != len(names):
            problems.append("section names must be unique")
    if m.get("main_section") not in names:
        problems.append("main_section must be the name of one of the sections")

    rules = m.get("rules", {})
    if not isinstance(rules, dict):
        problems.append("rules must be an object")
        rules = {}
    problems += [f"unknown key: rules.{k}" for k in rules if k not in ("image", "blocked_domains", "banned_phrases")]
    if rules.get("image", "none") not in IMAGE_RULES:
        problems.append(f"rules.image must be one of {', '.join(IMAGE_RULES)}")
    for k in ("blocked_domains", "banned_phrases"):
        if not _str_list(rules.get(k, [])):
            problems.append(f"rules.{k} must be a list of strings")

    insights = m.get("insights", {})
    if not isinstance(insights, dict):
        problems.append("insights must be an object")
        insights = {}
    problems += [f"unknown key: insights.{k}" for k in insights if k not in ("group_by", "columns")]
    if not _str_list(insights.get("group_by", [])):
        problems.append("insights.group_by must be a list of frontmatter keys")
    columns = insights.get("columns", {})
    if not isinstance(columns, dict) or not all(_str_list(v) for v in columns.values()):
        problems.append("insights.columns must map each field to a list of CSV header names")

    export = m.get("export", {})
    if not isinstance(export, dict):
        problems.append("export must be an object")
        export = {}
    problems += [f"unknown key: export.{k}" for k in export if k not in ("formats", "sections")]
    formats = export.get("formats", [])
    if not _str_list(formats) or any(f not in EXPORT_FORMATS for f in formats):
        problems.append(f"export.formats must be a list drawn from {', '.join(EXPORT_FORMATS)}")
    if not _str_list(export.get("sections", [])) or any(s not in names for s in export.get("sections", [])):
        problems.append("export.sections must list names from sections")

    mcp = m.get("mcp", [])
    if not _str_list(mcp) or any(not MCP_NAME_RE.match(s) for s in mcp):
        problems.append("mcp must be a list of MCP server names (letters, digits, _ and -)")
    return problems


class Tool:
    """One tool folder plus its parsed manifest. Every path is resolved from the tool folder."""

    def __init__(self, tool_dir: Path, manifest: dict):
        self.dir = Path(tool_dir).resolve()
        self.manifest = manifest

    @classmethod
    def load(cls, tool_dir: Path) -> "Tool":
        path = Path(tool_dir) / "tool.json"
        if not path.is_file():
            raise SystemExit(f"No tool.json in {tool_dir}")
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}: invalid JSON: {exc}")
        problems = check_manifest(manifest)
        if problems:
            raise SystemExit(f"{path} has problems:\n  - " + "\n  - ".join(problems))
        return cls(tool_dir, manifest)

    # --- Manifest accessors ------------------------------------------------
    @property
    def name(self) -> str:
        return self.manifest["name"]

    @property
    def nouns(self) -> dict[str, str]:
        return self.manifest["nouns"]

    @property
    def sections(self) -> list[dict]:
        return self.manifest["sections"]

    @property
    def main_section(self) -> str:
        return self.manifest["main_section"]

    @property
    def frontmatter_rules(self) -> dict:
        return self.manifest.get("frontmatter", {})

    @property
    def rules(self) -> dict:
        return self.manifest.get("rules", {})

    @property
    def insights(self) -> dict:
        return self.manifest.get("insights", {})

    @property
    def export(self) -> dict:
        return self.manifest.get("export", {})

    @property
    def mcp_servers(self) -> list[str]:
        """MCP servers this tool's workflows may use: names from .mcp.json or claude.ai connectors."""
        return self.manifest.get("mcp", [])

    def label(self, key: str) -> str:
        """Human name for a frontmatter key, in the tool's own words (item_type → 'post type')."""
        if key == "item_type":
            return f"{self.nouns['item']} type"
        return key.replace("_", " ")

    # --- Paths -------------------------------------------------------------
    @property
    def channels_dir(self) -> Path:
        return self.dir / "channels"

    @property
    def templates_dir(self) -> Path:
        return self.dir / "templates"

    @cached_property
    def placeholders(self) -> tuple[str, ...]:
        """Every <placeholder> in templates/item.md; an item still containing one is unfinished."""
        template = self.templates_dir / "item.md"
        if not template.is_file():
            return ()
        return tuple(dict.fromkeys(PLACEHOLDER_RE.findall(template.read_text(encoding="utf-8"))))

    def channel_dir(self, slug: str) -> Path:
        noun = self.nouns["channel"]
        if not SLUG_RE.match(slug):
            raise SystemExit(f"Invalid {noun} slug: {slug!r} (use lowercase letters, digits and hyphens)")
        path = self.channels_dir / slug
        if not path.is_dir():
            raise SystemExit(f"{noun.capitalize()} not found: {path}")
        return path

    def locate(self, path: Path) -> tuple[str, str]:
        """Return (channel_slug, status_folder) for an item path inside channels/."""
        path = Path(path).resolve()
        try:
            rel = path.relative_to(self.channels_dir.resolve())
        except ValueError:
            raise SystemExit(f"Not inside channels/: {path}")
        if len(rel.parts) != 3:
            raise SystemExit(f"Expected channels/<{self.nouns['channel']}>/<status>/<file>.md, got: {rel}")
        return rel.parts[0], rel.parts[1]

    def find_item(self, arg: str, status: str | None = None) -> Path:
        """Resolve an item given as a path, or as a bare filename searched across channels."""
        path = Path(arg)
        for c in (path, self.dir / path):
            if c.is_file():
                return c.resolve()
        folders = (status,) if status else STATUS_FOLDERS
        matches = [p for f in folders for p in self.channels_dir.glob(f"*/{f}/{path.name}")]
        if len(matches) == 1:
            return matches[0].resolve()
        if not matches:
            raise SystemExit(f"{self.nouns['item'].capitalize()} not found: {arg}")
        raise SystemExit("Ambiguous name, matches:\n  " + "\n  ".join(str(m) for m in matches))

    def rel(self, path: Path) -> str:
        """Path for printing: relative to the tool folder when inside it."""
        path = Path(path).resolve()
        return (path.relative_to(self.dir) if path.is_relative_to(self.dir) else path).as_posix()
