---
name: rewrite
description: Rewrite a draft item (tone, length, angle, language or hook) following the operator's instructions, while keeping its sources and facts traceable.
argument-hint: <draft-file> <instructions>
---

# /rewrite

Arguments: **$ARGUMENTS**. The first word is the item file (a path or filename); the rest are the operator's instructions.

## Steps

1. **Find the item.** Accept a full path or a bare filename, and search `channels/*/drafts/` and `channels/*/finalized/`.
   - In `drafts/`: continue.
   - In `finalized/`: tell the operator that changing it means fact-checking it again. If they agree, run `python run.py move reopen <file>` and work on the file in `drafts/`.
   - In `published/`: don't edit it. It is the record of what went out. Offer to create a new draft instead.
   - If no instructions were given, ask for them.

2. **Load context.** Run `python run.py info` for the format and limits. Read the channel's `profile.md`, `../shared/style_guide.md`, the channel's format file for the item's `item_type`, and the research note(s) the draft came from (look for the draft's filename under `used_in:` in `research/`).

3. **Rewrite.** Apply the instructions to every section meant for readers (everything except `## Reviewer notes`). For a large change (a new language, a new item type, or a full re-angle), run the tool's `writer` subagent with the draft path, the research note and the instructions. Otherwise edit the file directly.
   - **Keep facts traceable.** Use only facts already in `sources`, or in the research note. If the new version needs a new fact, find a source with WebFetch, add it to `sources`, and map it in reviewer notes. Remove sources the new text no longer uses.
   - Language change: update the `language` field. Write natively, not word for word. List unsure phrasing in reviewer notes.
   - Item type change: update `item_type`.
   - Keep the filename unless the topic itself changed. In that case, ask before renaming.

4. **Reset the check.** Set `fact_check: pending`. Update reviewer notes: keep the claim → source map current, and add a line `Rewritten YYYY-MM-DD: <instructions summary>`.

5. **Validate.** Run the command below and fix any errors.
   ```
   python run.py check <file>
   ```

6. **Show** the new main section (and the other reader-facing sections that changed), plus a one-line summary of what changed. Next step: more `/rewrite`, or `/finalize <file>`.
