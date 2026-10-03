---
name: load-tool
description: Load one tool into this root session for generate mode - its instructions, item format, workflows and agents - so the operator can research, write and finalize items without launching Claude Code inside tools/<tool>/.
argument-hint: <tool-name>
disable-model-invocation: true
---

# /load-tool

Tool: **$ARGUMENTS**

## Needs
A session launched at the repo root (the folder that holds `core/`, `tools/` and `.mcp.json`). If the working directory is anywhere else, stop and tell the operator to restart Claude Code from the repo root.

## Steps

1. **Pick the tool.** Run `python studio/factory.py list`. If no tool was given, or the name is not in the table, show the table and ask which one. `shared` is not a tool.

2. **Load it.** In this order:
   - Read `tools/<tool>/CLAUDE.md`: the tool's words, rules, format notes and publishing checklist. Reading a file under `tools/` also makes the shared workflows (`tools/.claude/skills/`) and the tool's own workflows available as slash commands.
   - Read `tools/shared/style_guide.md`.
   - Run `python tools/<tool>/run.py info`: item format, limits, channels and MCP servers.
   - List the folders in `tools/.claude/skills/` and `tools/<tool>/.claude/skills/`. Each folder name is a workflow.

3. **MCP servers.** If `info` lists any, run `python studio/factory.py mcp` and report each server's status. Remind the operator that `/mcp` shows whether a server is connected right now. A missing server does not block loading: a workflow step that needs it says so and is skipped.

4. **Report** in the tool's words:
   - the banner **`Mode: tool · <tool>`**
   - the channels (leave out `_test` unless it is the only one)
   - the workflow table from the tool's `CLAUDE.md`
   - the next command: `/new-channel <name>` if there is no real channel yet, otherwise `/research <slug>`

## How to work in this mode
These rules hold until the session is cleared.

**Paths.** The tool's `CLAUDE.md`, the workflows and the agents give paths relative to the tool folder. Translate them:

| Written | Means, from the repo root |
|---|---|
| `channels/…`, `templates/…`, `tool.json` | `tools/<tool>/channels/…`, `tools/<tool>/templates/…`, `tools/<tool>/tool.json` |
| `../shared/…` | `tools/shared/…` |
| `python run.py <command>` | `python tools/<tool>/run.py <command>` |

Item arguments to `run.py` can be a path relative to the tool folder (`channels/<slug>/drafts/<file>.md`) or a bare filename. Other file arguments, such as a CSV or `--out`, are relative to the repo root.

**Workflows.** `/new-channel`, `/research`, `/generate`, `/rewrite`, `/finalize`, `/mark-published` and `/import-insights`, plus any of the tool's own. If one is not in the `/` menu yet, or the operator asks in plain words, read `tools/<tool>/.claude/skills/<name>/SKILL.md` if it exists (the tool's copy wins), otherwise `tools/.claude/skills/<name>/SKILL.md`, and follow its steps with the operator's arguments.

**Subagents.** `researcher`, `fact-checker` and `writer` are root proxies that load the tool's real definitions. **Start every subagent prompt with `tool: <tool>`**, then give the inputs the workflow lists.

**MCP servers.** Use only the servers on `info`'s "MCP servers" line, and only the way the "MCP servers" section of the tool's `CLAUDE.md` describes. Never use one to publish, schedule or post, or to reach a Meta property.

**Scope.** Create and change files only in `tools/<tool>/channels/` and `tools/shared/research_cache/`, and only as the workflows describe. Other files belong to other modes:
- the tool's definition (`tool.json`, `CLAUDE.md`, agents, templates, workflows): `/load-studio`
- the framework: `/build-studio`

If the operator asks for a change in those files, name the mode to switch to (`/clear`, then that command).

The "Hard rules" in the tool's `CLAUDE.md` apply in full.
