---
name: new-tool
description: Build a new automation tool (blog post generator, newsletter, Instagram posts...) on the shared framework. Interviews the developer, scaffolds tools/<name>/ from templates/tool/, fills its manifest, instructions, writer and test channel, then checks it.
argument-hint: <tool-name>
disable-model-invocation: true
---

# /new-tool

Tool name: **$ARGUMENTS**

Read `../docs/framework-architecture.md` §2 and §5 first if you have not this session, and look at `../tools/facebook/` as the worked example.

## Steps

1. **Name.** If no name was given, ask. It is a folder name: lowercase letters, digits, hyphens (e.g. `blog`, `newsletter`). Run `python factory.py list` and stop if it exists.

2. **Interview the developer.** Ask in small groups (2–4 questions per message) and wait for answers. Suggest sensible defaults for the platform, but check any platform limit you propose (character caps, hashtag caps) with a web search, and say where the number came from.
   1. What is one **item** (post, article, issue...) and one **channel** (page, blog, segment...)? Where does a human publish it (the **platform**)?
   2. One research note per item, or several (`notes_per_item`: `one` or `many`)?
   3. The **sections** of an item, in order: which are required, which is the main reader-facing one, and any limits (`max_chars`, `max_hashtags`, `min_words`, `max_words`). Hard platform limits are errors; word targets are warnings.
   4. Extra **frontmatter**: item types, other fields and their allowed values. Does an item need an **image** (`rules.image`: `none`, `optional`, `required`)?
   5. Export formats for copy-paste publishing (`txt`, `md`, `html`) and which sections they include.
   6. How engagement data is exported, if at all (for `/import-insights`).

3. **Scaffold.** Run:
   ```
   python factory.py new-tool <name>
   ```

4. **Fill the tool** in `../tools/<name>/`, replacing every `TODO`:
   - `tool.json`: from the interview. Keys and allowed values are in the architecture doc §5.
   - `templates/item.md`: one `## Section` per entry in `sections`; frontmatter with the core keys plus the tool's keys; every value a `<placeholder>`.
   - `CLAUDE.md`: title, Words table, Format notes, Publishing checklist, Insights export (delete that section if there is none).
   - `.claude/agents/writer.md`: description, the first line, and one bullet per section. Keep its tools as they are.
   - `templates/channel/`: adjust `profile.md` questions to the platform if needed (e.g. a newsletter has segments and send days instead of hashtags).
   - Tool-only skills go in `.claude/skills/` with names that **don't** match a shared skill: a same-named skill in the tool folder replaces the shared one.

5. **Test channel.** From `../tools/<name>/` run `python run.py new-channel _test --name "Test channel"`, then fill its `profile.md` and `sources.md` with a fictional but realistic channel (no `TODO`s). Write fixtures by hand in `channels/_test/fixtures/`:
   - `valid/YYYY-MM-DD-<slug>.md`: one item that passes every rule
   - `invalid/YYYY-MM-DD-<slug>.md`: one item that breaks several rules; list them in its reviewer notes
   - a `README.md` saying what the fixtures are (copy `../tools/facebook/channels/_test/fixtures/README.md`)

6. **Check.** Run `/check-tool <name>` and fix everything it reports.

7. **Report** what was created, and the next step: `cd ../tools/<name> && claude`, then `/new-channel`, `/research _test`, `/generate _test 1`. Add the new tool to the README's tool table.
