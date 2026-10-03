---
name: load-studio
description: Load the studio into this root session to build a new tool or update an existing one - its tool.json, CLAUDE.md, writer, templates, test channel, tool-only commands and MCP servers. Not for changing the framework itself (that is /build-studio).
argument-hint: [tool-name]
disable-model-invocation: true
---

# /load-studio

Tool to work on (optional): **$ARGUMENTS**

## Needs
A session launched at the repo root (the folder that holds `core/`, `tools/` and `.mcp.json`). If the working directory is anywhere else, stop and tell the operator to restart Claude Code from the repo root.

## Steps

1. **Load the studio.** Read `studio/CLAUDE.md`. Reading a file under `studio/` also makes the studio commands available: `/new-tool`, `/update-tool` and `/check-tool`. Then read `docs/framework-architecture.md` §2 (concepts), §5 (the manifest) and §6–7 (shared workflows, building a tool).

2. **See what exists.** Run:
   ```
   python studio/factory.py list
   python studio/factory.py mcp
   ```

3. **Worked example.** Read `tools/facebook/tool.json`, `tools/facebook/CLAUDE.md` and `tools/facebook/.claude/agents/writer.md`. Facebook is the reference tool.

4. **The named tool**, if one was given:
   - If it exists: read its `tool.json`, `CLAUDE.md` and `.claude/agents/writer.md`, then run `python studio/factory.py check-tool <tool>`.
   - If it does not exist: offer `/new-tool <tool>`.

5. **Report**:
   - the banner **`Mode: studio`**
   - the tools table, and any problems `check-tool` or `mcp` found
   - the next command: `/new-tool <name>` or `/update-tool <name>`

## Scope
These rules hold until the session is cleared.

**May change:**
- a tool's definition in `tools/<tool>/`: `tool.json`, `CLAUDE.md`, `.claude/settings.json`, `.claude/agents/`, `.claude/skills/`, `templates/` and `channels/_test/`. `run.py` is a fixed shim; leave it alone.
- tool-only commands, created only with `python studio/factory.py new-command <name> --in <tool>`
- a root proxy in `.claude/agents/` for a new tool-only agent (`check-tool` says when one is missing). Copy `.claude/agents/researcher.md` and change the name, description, tools and file names.
- `.mcp.json`, to add a server a tool needs (secrets only as `${VAR}`)
- the tool table in `README.md`

**Must not change:** `core/`, `studio/`, `templates/`, `tools/.claude/`, `tools/shared/`, the root `CLAUDE.md` and the root commands. These are `/build-studio` work. Real channels (`tools/<tool>/channels/<slug>/` other than `_test`) belong to the operator in `/load-tool` mode.

If a tool needs something the framework does not offer (a new `tool.json` key, a validator rule, a change to a shared workflow), stop. Describe the change and say it needs `/build-studio`.

## Done when
1. `python studio/factory.py check-tool <tool>` passes, and `python studio/factory.py check-studio` passes if you added commands, agents or MCP servers.
2. If you changed the writer, a workflow or the item format, the operator has tested it in tool mode: `/clear`, `/load-tool <tool>`, then `/research _test` and `/generate _test 1`. The output must pass `python tools/<tool>/run.py check --channel _test`. Remind them, and remind them to delete the test drafts and notes afterwards.
