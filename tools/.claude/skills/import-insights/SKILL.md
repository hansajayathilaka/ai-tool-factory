---
name: import-insights
description: Summarize a manually exported engagement CSV for one channel of the current tool, save the summary in insights/, and update the "What works" section of the channel profile.
argument-hint: <channel-slug> <path-to-csv>
---

# /import-insights

Arguments: **$ARGUMENTS**. The first word is the channel slug; the second is the CSV path.

## How the operator exports the data
If they don't have a CSV yet, explain the steps in the "Insights export" section of the tool's `CLAUDE.md`. If the tool has no such section, it has no insights export yet: say so and stop. The platform is never accessed from here.

## Steps

1. **Place the file.** If the CSV is not already in `channels/<slug>/insights/`, copy it there as `YYYY-MM-DD-export.csv` (today's date). Raw CSVs are gitignored because they may hold private data.

2. **Summarize.** Run:
   ```
   python run.py insights <slug> insights/YYYY-MM-DD-export.csv --out insights/YYYY-MM-DD-summary.md
   ```
   If the command cannot find the columns, it prints the CSV headers. Rerun with `--map field="Header"` for the missing ones. If the same headers will recur, suggest adding them to `tool.json` → `insights.columns` in studio mode (`/load-studio`).

3. **Read the results.** Read the new summary, and the previous `insights/*-summary.md` files to see the trend.
   - The **baseline** is the median engagement rate and median reach in the **first** summary for this channel. Keep it fixed once set.
   - If many rows are unmatched (published outside this tool, or edited on the platform), say so: group conclusions are weaker.

4. **Update "What works"** in `channels/<slug>/profile.md`. Replace everything under that heading with:
   ```
   _Updated by `/import-insights`. Edit by hand only to fix mistakes._
   - **Baseline:** <median eng. rate>, median reach <n> (from YYYY-MM-DD-summary.md)
   - **Latest (<period>):** <median eng. rate>, median reach <n>: <up/down x% vs baseline>
   - **Works:** <pillars / item types / days / times that beat the channel median, with numbers>
   - **Doesn't work:** <what underperforms, with numbers>
   - **Try next:** <2–4 concrete recommendations for /research and /generate>
   ```
   Only state what the numbers support. Mark groups with fewer than 5 items as *tentative*. Don't remove the Do / Don't rules because of engagement data: those are the operator's decisions.

5. **Update formats.** If an item type clearly over- or underperforms, add a short dated line under "Notes" in `channels/<slug>/formats/<item_type>.md`.

6. **Show** the operator the updated "What works" section and the headline numbers.
