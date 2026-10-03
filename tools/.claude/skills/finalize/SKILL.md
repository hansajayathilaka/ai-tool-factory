---
name: finalize
description: Quality gate for a draft item. Runs the fact-checker, records the result, and, only with the operator's explicit approval, moves the item from drafts/ to finalized/.
argument-hint: <draft-file>
disable-model-invocation: true
---

# /finalize

Draft: **$ARGUMENTS**

## Steps

1. **Find the draft.** Accept a path or bare filename, and search `channels/*/drafts/`. If the file is not in `drafts/`, stop and explain why (an item in `finalized/` or `published/` is already past this step). Files under `channels/_test/fixtures/` are validator fixtures: refuse them.

2. **Structure check.** Run the command below. If there are errors, fix the purely structural ones (e.g. a missing `accessed` date) and show the operator what you changed. If a fix would change the content, stop and suggest `/rewrite`.
   ```
   python run.py check <file>
   ```

3. **Duplicate check.** Run the command below. If the same topic is already in `finalized/` or `published/`, warn the operator, and continue only if they confirm the repeat is deliberate. Record that in reviewer notes.
   ```
   python run.py topics <slug>
   ```

4. **Fact-check.** Run the `fact-checker` subagent with the item path, the channel slug, and today's date. It returns `VERDICT: PASS` or `VERDICT: FAIL` with a claim table.

5. **Record the result.**
   - Set `fact_check: passed` or `fact_check: failed` in the frontmatter.
   - Append to `## Reviewer notes`: `Fact-check YYYY-MM-DD: PASS/FAIL. <n> claims checked.` followed by any issues or suggestions, one per line.

6. **If FAIL:** show the unsupported or contradicted claims with the checker's suggested fixes, and stop. The operator can run `/rewrite` and then `/finalize` again.

7. **If PASS:** show the operator exactly what will be published:
   - the export, as it will appear: `python run.py export <file>`
   - the image (kind and idea), if the item has one
   - every point of the "Publishing checklist" in the tool's `CLAUDE.md` that applies to this item
   - remaining reviewer notes and any fact-checker suggestions

   Then ask: **"Approve this item and move it to finalized/?"** (in the tool's words, e.g. "Approve this post…").

8. **Move only on an explicit yes** from the operator in this conversation (e.g. "yes", "approve"). Anything else, including silence, edits or questions, is not approval. Then run:
   ```
   python run.py move finalize <file> --approved
   ```
   If the operator asks for changes instead, leave the item in `drafts/` and suggest `/rewrite`.

9. **Report** the new path. Remind the operator: publish it manually on the platform, then run `/mark-published <file> [YYYY-MM-DD]`.
