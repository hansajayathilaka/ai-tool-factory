# AI Automation Framework — studio

This file serves both studio modes. Claude Code is launched at the **repo root**, and every path here is relative to the root.

| Mode | Loaded by | For |
|---|---|---|
| **studio** | `/load-studio [tool]` | Building a new tool or updating an existing one |
| **studio-dev** | `/build-studio [goal]` | Improving the studio itself: `core/`, `studio/`, `templates/`, shared workflows, root commands, MCP support |

Each mode's command sets which files it may change. This file holds what both modes share. The design is in [../docs/framework-architecture.md](../docs/framework-architecture.md); read it before making structural changes.

## What the project is
A personal tool factory. Each tool lives in `tools/<tool>/` and researches topics and writes items (posts, articles, issues) for its channels (pages, blogs, segments). A human reviews every item and publishes it manually. Nothing in this repo publishes to any platform or scrapes Meta properties. Tools today: `facebook`.

## How sessions load things
Claude Code is launched at the repo root, so at startup it loads only the root `CLAUDE.md`, `.claude/` (commands, proxy agents, settings) and `.mcp.json`. Everything else loads **on demand**:
- A subfolder's `CLAUDE.md`, and the commands in its `.claude/skills/`, load the first time Claude reads a file in that folder. Reading `studio/CLAUDE.md` makes `/new-tool`, `/update-tool` and `/check-tool` available. Reading a file under `tools/` makes the shared workflows available.
- **Subagents are found only by walking up from the launch folder**, never down. Every agent under `tools/` therefore has a **root proxy** in `.claude/agents/` with the same name and tools. The proxy reads `tools/<tool>/.claude/agents/<name>.md`, or the shared `tools/.claude/agents/<name>.md`. Callers start the prompt with `tool: <name>`. `check-tool` and `check-studio` keep the proxies in sync.
- **Settings and `.mcp.json` are read only from the launch folder**, so the root `.claude/settings.json` holds the permissions for every mode, and `.mcp.json` holds every project MCP server.

Rules that keep this working:
1. **The root `CLAUDE.md` stays a short, mode-neutral router.** Mode rules live in the mode commands. No `CLAUDE.md` in `tools/` itself, because it would load in every tool session.
2. **Command names are unique** across the root, studio and shared commands, and a tool-only command must not reuse one. A same-named command in a tool folder replaces the shared one, and clashes between nested folders show up as directory-qualified names. `check-studio` and `check-tool` flag clashes.
3. Auto memory is off (`"autoMemoryEnabled": false` in the root and tool settings). Channel knowledge belongs in channel files (`profile.md`, `insights/`), not in Claude's memory.
4. A tool still works when Claude Code is launched inside `tools/<tool>/`: the shared workflows and agents are tool-relative, and each tool keeps its own `.claude/settings.json`. Root launch is the documented way.

## Where things live
- `CLAUDE.md`, `.claude/skills/` (`/start`, `/help`, `/load-tool`, `/load-studio`, `/build-studio`), `.claude/agents/` (proxies), `.claude/settings.json`, `.mcp.json`: the root session
- `core/`: the stdlib Python engine. `tool.py` (manifest loading and checks), `validate.py` (schema-driven item checks), `lifecycle.py` (status moves), `frontmatter.py`, `topics.py`, `insights.py`, `sources/` (RSS, Reddit), `scaffold.py`, `export.py`, `mcp.py` (`.mcp.json` checks, tool MCP status), `cli.py` (tool commands), `factory.py` (studio commands)
- `studio/factory.py`: `python studio/factory.py new-tool | check-tool | check-studio | new-command | mcp | list | test`
- `studio/.claude/skills/`: `/new-tool`, `/update-tool`, `/check-tool`
- `tools/.claude/skills/`: shared workflows (`/new-channel`, `/research`, `/generate`, `/rewrite`, `/finalize`, `/mark-published`, `/import-insights`)
- `tools/.claude/agents/`: shared subagents (`researcher`, `fact-checker`)
- `tools/shared/`: `style_guide.md`, `research_note.md`, `research_cache/`
- `tools/<tool>/`: `tool.json`, `CLAUDE.md`, `run.py`, `.claude/settings.json`, `.claude/agents/writer.md`, `templates/item.md`, `templates/channel/`, `channels/_test/`
- `templates/tool/`: skeleton copied by `/new-tool`; `templates/command/SKILL.md`: skeleton for every new command

## Writing commands (skills) and subagents
- **New commands start from the template**: `python studio/factory.py new-command <name> --in <root|studio|shared|tool>`, then replace every `TODO`. `check-studio` fails while one is left.
- Frontmatter: `name` (same as the folder), `description`, and `argument-hint` whenever the body uses `$ARGUMENTS`. Set `disable-model-invocation: true` on commands with side effects that only the operator should trigger: status moves, mode loads, interviews that create files.
- Every command says which mode it **needs**, gives steps rather than essays, and ends with a report and the next command.
- Shared workflows stay tool-agnostic and tool-relative. They say *item* and *channel*, read the tool's details from `python run.py info` and from the tool `CLAUDE.md` sections "Words", "Format notes", "Publishing checklist", "Insights export" and "MCP servers", and call only `python run.py …`. If a workflow needs a new per-tool fact, add it to `tool.json` (and `core/tool.py`'s checks) or to those `CLAUDE.md` sections, never a tool name inside a shared workflow.
- Subagents: frontmatter with `name`, `description`, `tools` and `model`. Give each one the fewest tools that work. `researcher` and `fact-checker` must stay read-only: no `Write`, `Edit` or `Bash`. Each tool's `writer` has `Read, Glob, Grep, Write, Edit` and no `Bash`. Its root proxy must list the same tools.
- Any file operation that changes an item's status goes through `python run.py move`, never a raw `mv`.
- Keep an item's format in sync in three places: the tool's `templates/item.md`, its `tool.json`, and (for the core keys `channel`, `topic`, `created`, `published`, `sources`, `fact_check`) `core/validate.py`.

## MCP servers
- Project servers go in the root `.mcp.json`. Secrets are only `${VAR}` references, never values; `check-studio` rejects a literal value under a secret-looking name and any Meta host. Claude Code expands `${VAR}` from its own environment, not from `.env`, so set those variables before launching.
- claude.ai connectors (Gmail, Google Drive, …) need no entry. They are named by their server name, which starts with `claude_ai_` (e.g. `claude_ai_Google_Drive`).
- A tool declares the servers its workflows may use in `tool.json` → `"mcp": [...]`. It describes when and how to use each one in its `CLAUDE.md` section "MCP servers". `python studio/factory.py mcp` shows each server's status.
- No MCP server may publish, schedule or post, or reach a Meta property.

## `core/` conventions
- Python 3.10+, **standard library only**, so operators need no `pip install`. If a dependency ever becomes unavoidable, add `core/requirements.txt` and document it here.
- `core` is a package. Tools reach it through `tools/<tool>/run.py`, the studio through `studio/factory.py`. Each command module has `register(sub, tool)` (adds its subcommand) and a `run(tool, args)`; every command has `--help`.
- Resolve paths from the `Tool` object (`tool.dir`, `tool.channels_dir`) or `core.common` (`REPO_DIR`, `TOOLS_DIR`, `SHARED_DIR`, `STUDIO_DIR`, `MCP_CONFIG`), never from the current directory.
- `cli.main` and `factory.main` call `common.utf8_stdout()` first: channels may be in Sinhala or Tamil, and the Windows console defaults to a legacy code page.
- Secrets (e.g. `REDDIT_CLIENT_ID`) come from environment variables or a gitignored `.env` file (tool folder or repo root), loaded with `common.load_env(tool.dir)`.
- Messages use the tool's nouns (`tool.nouns["item"]`), so the Facebook tool says "post" and "page".
- Unit tests live in `core/tests/`. Run them with `python studio/factory.py test`.

## Testing a change
A change is not done until:
1. `python studio/factory.py test` passes, `python studio/factory.py check-tool all` passes, and `python studio/factory.py check-studio` passes if commands, agents, settings or MCP changed.
2. The operator has run the affected workflow in **tool mode** (`/clear`, then `/load-tool <tool>`) against `channels/_test/`, and the output files pass `python tools/<tool>/run.py check --channel _test`.

Clean up test drafts and research notes afterwards. Intentional fixtures go in `channels/_test/fixtures/`, never in the status folders.
