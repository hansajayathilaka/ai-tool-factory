---
name: help
description: Show the commands available right now - for the active mode (tool, studio or studio-dev), or the root commands before a mode is loaded. With a topic, explain one command or concept. Replaces Claude Code's built-in /help in this project.
argument-hint: [command or topic]
---

# /help

Topic: **$ARGUMENTS**

## Steps

1. **Work out the active mode**, as the root `CLAUDE.md` defines it: none, `tool · <name>`, `studio` or `studio-dev`.

2. **If a topic was given**, answer it in 3–8 lines and stop:
   - **A command** (with or without `/`): read its `SKILL.md`. Look in `.claude/skills/`, then `studio/.claude/skills/`, `tools/.claude/skills/`, and the loaded tool's `tools/<tool>/.claude/skills/`. Say what it does, its arguments (`argument-hint`), which mode it needs, and give one example.
   - **A concept** (mode, tool, channel, item, lifecycle, manifest, MCP, proxy agents…): answer from `README.md` or `docs/framework-architecture.md`. Link the section.
   - **Unknown**: say so and list the commands for the current mode.

3. **With no topic**, show:
   - **Always**: the root commands: `/start`, `/help [topic]`, `/load-tool <tool>`, `/load-studio [tool]`, `/build-studio [goal]`. Add the reminder: one mode per session; `/clear` before switching.
   - **No mode yet**: the next step is `/start`.
   - **Tool mode**: the workflow table from the tool's `CLAUDE.md`, in the tool's words; the channels; and the helpers from `python tools/<tool>/run.py --help`.
   - **Studio mode**: `/new-tool <name>`, `/update-tool <name>`, `/check-tool <name|all>`, and the commands from `python studio/factory.py --help`.
   - **Studio-dev mode**: the factory commands (`test`, `check-studio`, `check-tool`, `new-command`, `mcp`) and the "Done when" list from `/build-studio`.

4. **End** with one line: Claude Code's own help is `claude --help` in a terminal, or https://code.claude.com/docs.

## Rules
- Change no files. `/help` only reads.
