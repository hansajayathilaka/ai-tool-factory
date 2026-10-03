---
name: finalize-post
description: Quality gate for a draft. Runs the fact-checker, records the result, and, only with the operator's explicit approval, moves the post from drafts/ to finalized/.
argument-hint: <draft-file>
disable-model-invocation: true
---

# /finalize-post

Draft: **$ARGUMENTS**

## Steps

1. **Find the draft.** Accept a path or bare filename, and search `facebook_pages/*/drafts/`. If the file is not in `drafts/`, stop and explain why (a post in `finalized/` or `posted/` is already past this step).

2. **Structure check.** Run the command below. If there are errors, fix the purely structural ones (e.g. a missing `accessed` date) and show the operator what you changed. If a fix would change the content, stop and suggest `/rewrite-post`.
   ```
   python utils/check_post.py <file>
   ```

3. **Duplicate check.** Run the command below. If the same topic is already in `finalized/` or `posted/`, warn the operator, and continue only if they confirm the repeat is deliberate. Record that in reviewer notes.
   ```
   python utils/posted_topics.py <slug>
   ```

4. **Fact-check.** Run the `fact-checker` subagent with the post path, the page slug, and today's date. It returns `VERDICT: PASS` or `VERDICT: FAIL` with a claim table.

5. **Record the result.**
   - Set `fact_check: passed` or `fact_check: failed` in the frontmatter.
   - Append to `## Reviewer notes`: `Fact-check YYYY-MM-DD: PASS/FAIL. <n> claims checked.` followed by any issues or suggestions, one per line.

6. **If FAIL:** show the unsupported or contradicted claims with the checker's suggested fixes, and stop. The operator can run `/rewrite-post` and then `/finalize-post` again.

7. **If PASS:** show the operator exactly what will be posted:
   - the caption and hashtags, as they will appear
   - image: kind and idea. If `needs_ai_label: true`, add: **"Turn on the AI label when posting."** For `stock`, add: "Use a licensed image only."
   - remaining reviewer notes and any fact-checker suggestions

   Then ask: **"Approve this post and move it to finalized/?"**

8. **Move only on an explicit yes** from the operator in this conversation (e.g. "yes", "approve"). Anything else, including silence, edits or questions, is not approval. Then run:
   ```
   python utils/move_post.py finalize <file> --approved
   ```
   If the operator asks for changes instead, leave the post in `drafts/` and suggest `/rewrite-post`.

9. **Report** the new path. Remind the operator: post it manually on Facebook, then run `/mark-posted <file> [YYYY-MM-DD]`.
