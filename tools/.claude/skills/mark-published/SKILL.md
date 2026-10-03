---
name: mark-published
description: Record that a finalized item was published manually on its platform. Sets its published date and moves it from finalized/ to published/.
argument-hint: <finalized-file> [YYYY-MM-DD]
disable-model-invocation: true
---

# /mark-published

Arguments: **$ARGUMENTS**. The first word is the finalized item (a path or filename); the optional second word is the date it was published.

## Steps

1. **Find the item.** Accept a path or bare filename, and search `channels/*/finalized/`. If it is in `drafts/`, explain that it must go through `/finalize` first. If it is already in `published/`, say so and stop.

2. **Date.** Use the given date. If none was given, use today's date and say which date you used. A published date must not be in the future.

3. **Check the text.** Ask the operator whether they changed the text on the platform when publishing. If they did, ask them to paste the published text, and update the matching sections so they match what went out. This keeps insights matching and duplicate checks accurate. Leave `fact_check` as it is, but add a reviewer note: `Edited at publishing time YYYY-MM-DD`.

4. **Move.** Run:
   ```
   python run.py move publish <file> --date YYYY-MM-DD
   ```

5. **Confirm** the new path and date. When a few weeks of items have built up, remind the operator to export engagement data (see "Insights export" in the tool's `CLAUDE.md`) and run `/import-insights <slug> <csv>`.
