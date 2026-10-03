---
name: research
description: Find current, relevant topics for one channel of the current tool and save research notes with sources to its research/ folder. Use before generating items, or when the operator asks what a channel could publish about.
argument-hint: <channel-slug> [topic]
---

# /research

Arguments: **$ARGUMENTS**. The first word is the channel slug; anything after it is an optional topic.

## Steps

1. **Load the channel.** Read `channels/<slug>/profile.md`, `channels/<slug>/sources.md` and `../shared/style_guide.md`. If the slug is missing or unknown, list the folders in `channels/` and ask.

2. **Already covered.** Run the command below and keep the list. A candidate is a **duplicate** if it covers the same story, or the same evergreen topic from the same angle, as anything published, finalized, drafted or still `new` in research within the last ~90 days.
   ```
   python run.py topics <slug> --status all
   ```

3. **Shared cache.** List `../shared/research_cache/`. It is shared by every channel of every tool. A cached note on the same topic is reusable if it is fresh: `kind: news` up to 7 days after `created`, `kind: evergreen` up to 90 days.

4. **Signals** (skip this step if the operator gave a topic):
   - `python run.py rss <slug> --days 7`
   - `python run.py reddit <slug> --period week`, only if `sources.md` lists subreddits. If it fails, note that and move on.
   - Google Trends has no official API. Use any trend terms in `sources.md` as search hints, and tell the operator they can check trends.google.com manually.

5. **Shortlist** (skip this step if the operator gave a topic). Pick about **2 × the channel's items per week** candidates (the profile's posting frequency). Each one must fit a pillar, be timely (or worthwhile evergreen), not be a duplicate, and not touch the profile's Don't list. If the signals are thin, ask the `researcher` subagent to find candidates. Show the shortlist as a table (topic · pillar · why now · kind), and ask the operator to confirm or adjust before deep research.

6. **Deep research.** For each confirmed topic, run the `researcher` subagent. Topics are independent, so launch them in parallel. Give each one:
   - channel slug, niche, audience, language, the topic's pillar
   - the topic, plus any signal links from step 4
   - the trusted and avoided sources from `sources.md`
   - the path of a fresh cached note to build on, if one exists
   - an instruction to return a note in the format of `../shared/research_note.md`

7. **Save notes.** Write each note to `channels/<slug>/research/YYYY-MM-DD-<topic-slug>.md` (today's date) with `status: new` and empty `used_in:`. Reject notes where a key fact has no source: drop the fact, or ask the researcher again.
   If the facts would be useful to other channels or tools too (general news rather than a channel-specific angle), also save a channel-neutral copy to `../shared/research_cache/YYYY-MM-DD-<topic-slug>.md`: `channel: shared`, no pillar, no "Angles" section. Then set the channel note's `cache:` field to `../shared/research_cache/<file>` (relative to the tool folder, like every path here).

8. **Report.** Show a table of the new notes (file · topic · pillar · kind · number of sources), plus any candidates you dropped and why. Next step: `/generate <slug> [n]`.

## Rules
- Never use Facebook, Instagram, Threads or other Meta properties as sources, and never try to open them.
- Research notes hold facts with sources. Keep opinions and final wording for the writer.
