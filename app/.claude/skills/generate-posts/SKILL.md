---
name: generate-posts
description: Write Facebook post drafts for a page from its unused research notes, following the page profile, its post formats and the shared style guide. Output goes to the page's drafts/ folder.
argument-hint: <page-slug> [number-of-posts]
---

# /generate-posts

Arguments: **$ARGUMENTS**. The first word is the page slug; the optional second word is the number of posts.

## Steps

1. **Load the page.** Read `facebook_pages/<slug>/profile.md`, `shared/style_guide.md` and the files in `facebook_pages/<slug>/templates/`. If the number of posts is not given, use the profile's posts per week.

2. **Pick research.** List the notes in `facebook_pages/<slug>/research/` with `status: new`:
   ```
   python utils/posted_topics.py <slug> --status research
   ```
   If there are fewer notes than posts requested, tell the operator, and offer `/research <slug>` or to continue with what exists.

3. **Duplicate check.** Run the command below and skip any note whose topic is already in drafts, finalized or posted, unless the note has a clearly new angle. Flag that case to the operator.
   ```
   python utils/posted_topics.py <slug>
   ```
   Stale news (a `kind: news` note created more than 7 days ago) needs a refresh through `/research` first.

4. **Plan the batch.** Assign each note a post type from the profile. Balance pillars and post types across the batch, and favour what the profile's "What works" section recommends. Show the plan (note · pillar · post type · language) in one short table and continue; the operator reviews the drafts afterwards.

5. **Write.** For each planned post, run the `writer` subagent. Posts are independent, so launch them in parallel. Give each one:
   - page slug and today's date
   - the research note path (and its `cache:` note, if set)
   - the post type and the format file `facebook_pages/<slug>/templates/<post_type>.md`, if it exists
   - the output path: `facebook_pages/<slug>/drafts/YYYY-MM-DD-<topic-slug>.md`. If that name is taken, add `-2`.
   - any extra instructions from the operator

6. **Validate.** Run the command below on the new files. Fix every error (ask the writer, or edit directly). Review the warnings, especially engagement bait and AI image labels.
   ```
   python utils/check_post.py <files...>
   ```

7. **Update research notes.** Set each used note's `status: used`, and add the draft's filename under `used_in:` as a list item.

8. **Report.** For each draft, show: file, topic, pillar, post type, language, image kind (with an AI-label note), the caption's first line, and its reviewer notes. Remind the operator of the next steps: review, then `/rewrite-post <file> <instructions>` or `/finalize-post <file>`.

## Rules
- Drafts are written only to `facebook_pages/<slug>/drafts/`.
- Every new draft has `fact_check: pending` and an empty `posted:` field.
