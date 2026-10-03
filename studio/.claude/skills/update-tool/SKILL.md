---
name: update-tool
description: Change an existing tool - its item format and limits, voice and format notes, writer, channel template, tool-only commands or MCP servers - keeping its manifest, item template, fixtures and test channel in sync, then check it.
argument-hint: <tool-name> [what to change]
disable-model-invocation: true
---

# /update-tool

Arguments: **$ARGUMENTS**. The first word is the tool; the rest is the change.

## Needs
Studio mode (`/load-studio`). Paths are relative to the repo root.

## Steps

1. **Load the tool.** If no tool was given, or it does not exist, run `python studio/factory.py list` and ask. Read `tools/<tool>/tool.json`, `CLAUDE.md`, `.claude/agents/writer.md` and `templates/item.md`, then run `python studio/factory.py check-tool <tool>` for a baseline.

2. **Pin down the change.** If it was not given, or is vague, ask. Check any platform limit you add with a web search, and say where the number came from. If the change needs something the framework lacks (a new `tool.json` key, a validator rule, a shared workflow change), stop and say it needs `/build-studio`.

3. **Plan the edits.** Show the files you will change and why, and wait for a yes. One change often touches several files:

   | Change | Files |
   |---|---|
   | a section, a limit, a frontmatter field or an item type | `tool.json`, `templates/item.md`, `writer.md`, the `_test` fixtures, `export.sections` if it is exported |
   | voice, platform rules or the publishing checklist | `CLAUDE.md` ("Format notes", "Publishing checklist"), `writer.md` |
   | channel interview questions | `templates/channel/` (existing channels keep their profile; say so) |
   | a tool-only command | `python studio/factory.py new-command <command> --in <tool>`, then fill it |
   | an MCP server | `tool.json` → `mcp`, `CLAUDE.md` → "MCP servers", and `.mcp.json` if it is a new project server (secrets only as `${VAR}`) |
   | a tool-only agent | `tools/<tool>/.claude/agents/<name>.md`, plus a root proxy in `.claude/agents/` with the same name and tools |

4. **Edit**, keeping the format in sync between `tool.json`, `templates/item.md` and the writer. Real channels (not `_test`) are the operator's: never edit their items. If the change makes their existing drafts invalid, list the affected files with `python tools/<tool>/run.py check --channel <slug>` and tell the operator.

5. **Check.** Run `/check-tool <tool>` and fix everything it reports.

6. **Report** what changed, file by file. If the writer, the format or a workflow changed, the next step is the tool-mode test: `/clear`, `/load-tool <tool>`, `/generate _test 1`.
