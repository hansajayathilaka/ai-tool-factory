---
name: check-tool
description: Check that a tool is complete and correct - manifest, required files, no leftover TODOs, _test fixtures pass or fail as expected - and run the core unit tests. Use after changing a tool, core/ or templates/tool/.
argument-hint: <tool-name | all>
---

# /check-tool

Tool: **$ARGUMENTS** (default `all`).

## Steps

1. **Unit tests.** Run:
   ```
   python factory.py test
   ```
   They include one check per tool in `tools/`.

2. **Tool check.** Run:
   ```
   python factory.py check-tool <name>
   ```
   It reports a missing file, an invalid `tool.json`, a leftover `TODO`, a tool skill that reuses a shared skill's name, a valid fixture that fails, an invalid fixture that passes, or a `_test` item that fails.

3. **Fix** each problem, then repeat steps 1–2 until both pass. If a fixture fails for a reason you did not intend, fix the fixture or the manifest, not the validator, unless the validator is wrong for every tool.

4. **Report** the result. If the change touched a workflow, a skill or an agent, remind the developer of the generate-mode test in `CLAUDE.md` ("Testing a change").
