---
name: new-tool
description: Build a new automation tool (blog post generator, newsletter, Instagram posts...) on the shared framework. Interviews the developer, scaffolds tools/<name>/ from templates/tool/, fills its manifest, instructions, writer and test channel, then checks it.
argument-hint: <tool-name>
disable-model-invocation: true
---

# /new-tool

Tool name: **$ARGUMENTS**

## Needs
Studio mode (`/load-studio`). Paths are relative to the repo root.

## Steps

1. **Name.** If no name was given, ask. It is a folder name: lowercase letters, digits, hyphens (e.g. `blog`, `newsletter`); not `shared`, `root` or `studio`. Run `python studio/factory.py list` and stop if it exists.

2. **Interview the developer.** Ask in small groups (2–4 questions per message) and wait for answers. Suggest sensible defaults for the platform. Check any platform limit you propose (character caps, hashtag caps) with a web search, and say where the number came from.
   1. What is one **item** (post, article, issue...) and one **channel** (page, blog, segment...)? Where does a human publish it (the **platform**)?
   2. One research note per item, or several (`notes_per_item`: `one` or `many`)?
   3. The **sections** of an item, in order: which are required, which is the main reader-facing one, and any limits (`max_chars`, `max_hashtags`, `min_words`, `max_words`). Hard platform limits are errors; word targets are warnings.
   4. Extra **frontmatter**: item types, other fields and their allowed values. Does an item need an **image** (`rules.image`: `none`, `optional`, `required`)?
   5. Export formats for copy-paste publishing (`txt`, `md`, `html`) and which sections they include.
   6. How engagement data is exported, if at all (for `/import-insights`).
   7. **MCP servers**: should a workflow use one, e.g. save finalized items to Google Drive, or read a content calendar? Show `python studio/factory.py mcp`. For each server, note which workflow step uses it and how. Publishing, scheduling and Meta properties stay out of bounds.

3. **Scaffold.** Run:
   ```
   python studio/factory.py new-tool <name>
   ```

4. **Fill the tool** in `tools/<name>/`, replacing every `TODO`:
   - `tool.json`: from the interview. Keys and allowed values are in `docs/framework-architecture.md` §5. `mcp` lists the server names from question 7, or stays `[]`.
   - `templates/item.md`: one `## Section` per entry in `sections`; frontmatter with the core keys plus the tool's keys; every value a `<placeholder>`.
   - `CLAUDE.md`: title, Words table, Format notes, Publishing checklist, Insights export (delete that section if there is none), MCP servers (say "None." if `mcp` is empty).
   - `.claude/agents/writer.md`: description, the first line, and one bullet per section. Keep its tools as they are; they match the root proxy `.claude/agents/writer.md`.
   - `templates/channel/`: adjust the `profile.md` questions to the platform if needed (e.g. a newsletter has segments and send days instead of hashtags).
   - Tool-only commands: `python studio/factory.py new-command <command> --in <name>`, then fill the template. The names must not match a shared workflow, or the tool's copy would replace it.
   - A new project MCP server goes in `.mcp.json`, with secrets only as `${VAR}`.

5. **Test channel.** Run `python tools/<name>/run.py new-channel _test --name "Test channel"`, then fill its `profile.md` and `sources.md` with a fictional but realistic channel (no `TODO`s). Write fixtures by hand in `tools/<name>/channels/_test/fixtures/`:
   - `valid/YYYY-MM-DD-<slug>.md`: one item that passes every rule
   - `invalid/YYYY-MM-DD-<slug>.md`: one item that breaks several rules; list them in its reviewer notes
   - a `README.md` saying what the fixtures are (copy `tools/facebook/channels/_test/fixtures/README.md`)

6. **Check.** Run `/check-tool <name>` and fix everything it reports.

7. **Report** what was created. Add the new tool to the tool table in `README.md`. The next step: `/clear`, `/load-tool <name>`, then `/research _test` and `/generate _test 1`.
