---
name: generate
description: Write draft items (posts, articles, issues...) for one channel of the current tool from its unused research notes, following the channel profile, its formats, the tool's format and the shared style guide. Output goes to the channel's drafts/ folder.
argument-hint: <channel-slug> [number-of-items]
---

# /generate

Arguments: **$ARGUMENTS**. The first word is the channel slug; the optional second word is the number of items.

## Steps

1. **Load the tool and channel.** Run `python run.py info` for the item format, its limits and `notes per item`. Read `channels/<slug>/profile.md`, `../shared/style_guide.md` and the files in `channels/<slug>/formats/`. If the number of items is not given, use the profile's posting frequency per week.

2. **Pick research.** List the notes in `channels/<slug>/research/` with `status: new`:
   ```
   python run.py topics <slug> --status research
   ```
   If there are too few notes for the batch, tell the operator, and offer `/research <slug>` or to continue with what exists.

3. **Duplicate check.** Run the command below and skip any note whose topic is already in drafts, finalized or published, unless the note has a clearly new angle. Flag that case to the operator.
   ```
   python run.py topics <slug>
   ```
   Stale news (a `kind: news` note created more than 7 days ago) needs a refresh through `/research` first.

4. **Plan the batch.** Show the plan in one short table and continue; the operator reviews the drafts afterwards.
   - **`notes per item: one`**: one note → one item. Assign each note an item type from the profile. Balance pillars and item types across the batch, and favour what the profile's "What works" section recommends. Table: note · pillar · item type · language.
   - **`notes per item: many`**: each item combines several notes (e.g. one newsletter issue with several stories). Group notes into items by the profile's guidance. Table: item · notes · item type · language.

5. **Write.** For each planned item, run the tool's `writer` subagent. Items are independent, so launch them in parallel. Give each one:
   - channel slug and today's date
   - the research note path(s) (and their `cache:` notes, if set)
   - the item type and the format file `channels/<slug>/formats/<item_type>.md`, if it exists
   - the output path: `channels/<slug>/drafts/YYYY-MM-DD-<topic-slug>.md`. If that name is taken, add `-2`.
   - any extra instructions from the operator

6. **Validate.** Run the command below on the new files. Fix every error (ask the writer, or edit directly). Review the warnings, especially engagement bait, length targets and AI image labels.
   ```
   python run.py check <files...>
   ```

7. **Update research notes.** Set each used note's `status: used`, and add the draft's filename under `used_in:` as a list item.

8. **Report.** For each draft, show: file, topic, pillar, item type, language, image kind if the tool has images (with an AI-label note), the first line of the main section, and its reviewer notes. Remind the operator of the next steps: review, then `/rewrite <file> <instructions>` or `/finalize <file>`.

## Rules
- Drafts are written only to `channels/<slug>/drafts/`.
- Every new draft has `fact_check: pending` and an empty `published:` field.
