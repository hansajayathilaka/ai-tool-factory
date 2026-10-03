# AI Automation Framework — build mode

This is the **build-mode** instructions file. You are helping a developer build and improve the framework (`core/`, `templates/tool/`, the shared workflows) and the tools built on it (`tools/<tool>/`). The design is in [../docs/framework-architecture.md](../docs/framework-architecture.md); the overview is in [../README.md](../README.md). Read the architecture doc before making structural changes.

## What the project is
A personal tool factory. Each tool is a Claude Code workspace in `tools/<tool>/` that researches topics and writes items (posts, articles, issues) for its channels (pages, blogs, segments). A human reviews every item and publishes it manually. Nothing in this repo publishes to any platform or scrapes Meta properties. Tools today: `facebook`.

## Two modes, kept apart by the folder layout
| | Build mode (you, now) | Generate mode |
|---|---|---|
| Launch folder | `studio/` | `tools/<tool>/` |
| Instructions | this file | `tools/<tool>/CLAUDE.md` |
| Skills | `studio/.claude/skills/` (`/new-tool`, `/check-tool`) | `tools/.claude/skills/` (shared) + `tools/<tool>/.claude/` |

Claude Code loads `CLAUDE.md`, `.claude/skills/` and `.claude/agents/` from the launch folder **and every parent folder**. `studio/` is a sibling of `tools/`, never a parent, so nothing here leaks into a tool session. Do not break this:
1. **No `CLAUDE.md` and no `.claude/` at the repo root or in `tools/`** (except `tools/.claude/`, which holds the shared workflows on purpose). A unit test enforces it.
2. **A tool-only skill must not reuse a shared skill's name.** The tool's copy would replace the shared one for that tool (verified 2026-10-03). `check-tool` flags it.
3. Each tool's `.claude/settings.json` sets `"autoMemoryEnabled": false`. Channel knowledge belongs in channel files (`profile.md`, `insights/`), not Claude's memory.

When you open files under `tools/<tool>/`, Claude Code also loads that tool's `CLAUDE.md`. That is intended: read it to understand how the tool behaves, but follow *this* file for how to work.

## Where things live
- `core/`: the stdlib Python engine. `tool.py` (manifest loading and checks), `validate.py` (schema-driven item checks), `lifecycle.py` (status moves), `frontmatter.py`, `topics.py`, `insights.py`, `sources/` (RSS, Reddit), `scaffold.py`, `export.py`, `cli.py` (tool commands), `factory.py` (studio commands)
- `tools/.claude/skills/`: shared workflows (`/new-channel`, `/research`, `/generate`, `/rewrite`, `/finalize`, `/mark-published`, `/import-insights`)
- `tools/.claude/agents/`: shared subagents (`researcher`, `fact-checker`)
- `tools/shared/`: `style_guide.md`, `research_note.md`, `research_cache/`
- `tools/<tool>/`: `tool.json`, `CLAUDE.md`, `run.py`, `.claude/agents/writer.md`, `templates/item.md`, `templates/channel/`, `channels/_test/`
- `templates/tool/`: skeleton copied by `/new-tool`
- `studio/factory.py`: `python factory.py new-tool | check-tool | list | test`

## Writing skills and subagents
- Skills: YAML frontmatter with `name`, `description` and `argument-hint`. Use `$ARGUMENTS` for the operator's input. Set `disable-model-invocation: true` on workflows with side effects that only the operator should trigger (moving items between status folders).
- Shared skills stay tool-agnostic. They say *item* and *channel*, read the tool's details from `python run.py info` and from the tool `CLAUDE.md` sections "Words", "Format notes", "Publishing checklist" and "Insights export", and call only `python run.py …`. If a skill needs a new per-tool fact, add it to `tool.json` (and `core/tool.py`'s checks) or to those `CLAUDE.md` sections, never a tool name inside a shared skill.
- Subagents: frontmatter with `name`, `description`, `tools` and `model`. Give each one the fewest tools that work. `researcher` and `fact-checker` must stay read-only: no `Write`, `Edit` or `Bash`. Each tool's `writer` has `Read, Glob, Grep, Write, Edit` and no `Bash`.
- Skills give steps, not essays. Any file operation that changes an item's status goes through `python run.py move`, never a raw `mv`.
- Keep an item's format in sync in three places: the tool's `templates/item.md`, its `tool.json`, and (for the core keys `channel`, `topic`, `created`, `published`, `sources`, `fact_check`) `core/validate.py`.

## `core/` conventions
- Python 3.10+, **standard library only**, so operators need no `pip install`. If a dependency ever becomes unavoidable, add `core/requirements.txt` and document it here.
- `core` is a package. Tools reach it through `tools/<tool>/run.py`, the studio through `studio/factory.py`. Each command module has `register(sub, tool)` (adds its subcommand) and a `run(tool, args)`; every command has `--help`.
- Resolve paths from the `Tool` object (`tool.dir`, `tool.channels_dir`) or `core.common` (`REPO_DIR`, `TOOLS_DIR`, `SHARED_DIR`), never from the current directory.
- `cli.main` and `factory.main` call `common.utf8_stdout()` first: channels may be in Sinhala or Tamil, and the Windows console defaults to a legacy code page.
- Secrets (e.g. `REDDIT_CLIENT_ID`) come from environment variables or a gitignored `.env` file (tool folder or repo root), loaded with `common.load_env(tool.dir)`.
- Messages use the tool's nouns (`tool.nouns["item"]`), so the Facebook tool says "post" and "page".
- Unit tests live in `core/tests/`. Run them with `python factory.py test` from here.

## Testing a change
A change is not done until:
1. `python factory.py test` passes, and `python factory.py check-tool all` passes (or `/check-tool`).
2. You have run the affected workflow in **generate mode** (launch Claude Code from `tools/<tool>/`) against `channels/_test/`, and the output files pass `python run.py check --channel _test`.
3. In that session, `/memory` lists only that tool's `CLAUDE.md`, never this file.

Clean up test drafts and research notes afterwards. Intentional fixtures go in `channels/_test/fixtures/`, never in the status folders.
