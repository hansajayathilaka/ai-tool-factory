---
name: build-studio
description: Load the studio's own code into this root session to improve it - core/ (the Python engine), studio/ (the factory and studio commands), templates/, the shared workflows and agents in tools/, the root commands, the proxy agents and MCP support. Not for building or changing a tool (that is /load-studio).
argument-hint: [what to improve]
disable-model-invocation: true
---

# /build-studio

Goal (optional): **$ARGUMENTS**

## Needs
A session launched at the repo root (the folder that holds `core/`, `tools/` and `.mcp.json`). If the working directory is anywhere else, stop and tell the operator to restart Claude Code from the repo root.

## Steps

1. **Load the design.** Read `studio/CLAUDE.md`, `docs/framework-architecture.md` (all of it), `core/README.md` and `README.md`.

2. **Map the commands and agents.** List:
   - `.claude/skills/` (root commands) and `.claude/agents/` (proxy agents)
   - `studio/.claude/skills/` (studio commands)
   - `tools/.claude/skills/` and `tools/.claude/agents/` (shared workflows and agents)
   - `templates/`

3. **Baseline.** Run the commands below, and note anything that already fails so it is not blamed on your change:
   ```
   python studio/factory.py test
   python studio/factory.py check-studio
   python studio/factory.py check-tool all
   ```

4. **The goal**, if one was given: find and read the files it touches. If the change is structural (folders, `tool.json` keys, command names, mode rules, permissions), propose a short plan and wait for a yes before editing.

5. **Report**:
   - the banner **`Mode: studio-dev`**
   - the baseline results
   - the plan, or a question about what to improve

## Scope
These rules hold until the session is cleared.

**May change:** `core/`, `studio/`, `templates/`, `tools/.claude/`, `tools/shared/` (not the notes in `research_cache/`), the root `CLAUDE.md`, `.claude/`, `.mcp.json`, `docs/`, `README.md` and `.gitignore`.

**Tool folders** (`tools/<tool>/`): change them only when a framework change needs every tool updated, such as a renamed `tool.json` key or a new required `CLAUDE.md` section. Make the same change in every tool and list it in your report. Never touch real channel content. Building or reshaping one tool is `/load-studio` work.

## Rules
- **Keep the modes working.** The root `CLAUDE.md` stays a short router, and each mode's rules live in its command. Create a new command only with `python studio/factory.py new-command <name> --in <root|studio|shared|tool>`. Command names must be unique across root, studio and shared.
- **Every agent under `tools/` needs a root proxy** in `.claude/agents/` with the same name and the same tools. A root session finds agents only there.
- **Shared workflows and agents stay tool-relative**: paths relative to the tool folder, and `python run.py`. `/load-tool` translates them, and they also still work in a session launched inside a tool folder. Studio files and root commands use repo-root paths.
- The `core/` conventions and the skill and agent conventions in `studio/CLAUDE.md` apply.

## Done when
1. `python studio/factory.py test`, `check-studio` and `check-tool all` all pass.
2. If you changed a shared workflow, an agent or `core/` behaviour that a workflow uses, the operator has run that workflow in tool mode (`/clear`, `/load-tool facebook`) against `_test`, and the output passes `python tools/facebook/run.py check --channel _test`.
3. `README.md`, `docs/framework-architecture.md` and `core/README.md` match the change.
