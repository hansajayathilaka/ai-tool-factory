---
name: mark-posted
description: Record that a finalized post was published manually on Facebook. Sets its posted date and moves it from finalized/ to posted/.
argument-hint: <finalized-file> [YYYY-MM-DD]
disable-model-invocation: true
---

# /mark-posted

Arguments: **$ARGUMENTS**. The first word is the finalized post (a path or filename); the optional second word is the date it was posted.

## Steps

1. **Find the post.** Accept a path or bare filename, and search `facebook_pages/*/finalized/`. If it is in `drafts/`, explain that it must go through `/finalize-post` first. If it is already in `posted/`, say so and stop.

2. **Date.** Use the given date. If none was given, use today's date and say which date you used. A posted date must not be in the future.

3. **Check the caption.** Ask the operator whether they changed the caption on Facebook when posting. If they did, ask them to paste the posted text. Update `## Caption` so it matches what went out. This keeps insights matching and duplicate checks accurate. Leave `fact_check` as it is, but add a reviewer note: `Caption edited at posting time YYYY-MM-DD`.

4. **Move.** Run:
   ```
   python utils/move_post.py posted <file> --date YYYY-MM-DD
   ```

5. **Confirm** the new path and date. When a few weeks of posts have built up, remind the operator to export engagement data and run `/import-insights <slug> <csv>`.
