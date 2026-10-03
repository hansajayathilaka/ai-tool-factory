---
name: import-insights
description: Summarize a manually exported Meta Business Suite engagement CSV for a page, save the summary in insights/, and update the "What works" section of the page profile.
argument-hint: <page-slug> <path-to-csv>
---

# /import-insights

Arguments: **$ARGUMENTS**. The first word is the page slug; the second is the CSV path.

## How the operator exports the data
If they don't have a CSV yet, explain: Meta Business Suite → **Insights** → **Content** → choose the date range → **Export data** → *Post-level data* → **CSV**. Facebook is never accessed from here.

## Steps

1. **Place the file.** If the CSV is not already in `facebook_pages/<slug>/insights/`, copy it there as `YYYY-MM-DD-export.csv` (today's date). Raw CSVs are gitignored because they may hold private page data.

2. **Summarize.** Run:
   ```
   python utils/insights_summary.py <slug> insights/YYYY-MM-DD-export.csv --out insights/YYYY-MM-DD-summary.md
   ```
   If the script cannot find the columns, it prints the CSV headers. Rerun with `--map field="Header"` for the missing ones.

3. **Read the results.** Read the new summary, and the previous `insights/*-summary.md` files to see the trend.
   - The **baseline** is the median engagement rate and median reach in the **first** summary for this page. Keep it fixed once set.
   - If many posts are unmatched (posted outside this tool, or captions edited on Facebook), say so: pillar conclusions are weaker.

4. **Update "What works"** in `facebook_pages/<slug>/profile.md`. Replace everything under that heading with:
   ```
   _Updated by `/import-insights`. Edit by hand only to fix mistakes._
   - **Baseline:** <median eng. rate>, median reach <n> (from YYYY-MM-DD-summary.md)
   - **Latest (<period>):** <median eng. rate>, median reach <n>: <up/down x% vs baseline>
   - **Works:** <pillars / post types / days / times that beat the page median, with numbers>
   - **Doesn't work:** <what underperforms, with numbers>
   - **Try next:** <2–4 concrete recommendations for /research and /generate-posts>
   ```
   Only state what the numbers support. Mark groups with fewer than 5 posts as *tentative*. Don't remove the Do / Don't rules because of engagement data: those are the operator's decisions.

5. **Update post formats.** If a post type clearly over- or underperforms, add a short dated line under "Notes" in `facebook_pages/<slug>/templates/<post_type>.md`.

6. **Show** the operator the updated "What works" section and the headline numbers.
