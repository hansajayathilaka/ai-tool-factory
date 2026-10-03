---
name: check-tool
description: Check that a tool is complete and correct - manifest, required files, no leftover TODOs, MCP servers, root proxy agents, _test fixtures pass or fail as expected - and run the core unit tests and the studio check. Use after changing a tool, core/, templates/ or the commands.
argument-hint: <tool-name | all>
---

# /check-tool

Tool: **$ARGUMENTS** (default `all`).

## Needs
Studio or studio-dev mode. Paths are relative to the repo root.

## Steps

1. **Unit tests.** Run the command below. The tests include one check per tool in `tools/` and the studio check.
   ```
   python studio/factory.py test
   ```

2. **Tool check.** Run:
   ```
   python studio/factory.py check-tool <name>
   ```
   It reports a missing file, an invalid `tool.json`, a leftover `TODO`, a tool command that reuses a shared command's name, an MCP server that is neither in `.mcp.json` nor a claude.ai connector, a tool agent without a matching root proxy, a valid fixture that fails, an invalid fixture that passes, or a `_test` item that fails.

3. **Studio check.** Run:
   ```
   python studio/factory.py check-studio
   ```
   It reports missing root files, a command with bad frontmatter or a leftover `TODO`, duplicate command names, out-of-sync proxy agents, and unsafe `.mcp.json` entries.

4. **Fix** each problem, then repeat steps 1–3 until all pass. If a fixture fails for a reason you did not intend, fix the fixture or the manifest, not the validator, unless the validator is wrong for every tool.

5. **Report** the result. If the change touched a workflow, a command or an agent, remind the developer of the tool-mode test in `studio/CLAUDE.md` ("Testing a change").
