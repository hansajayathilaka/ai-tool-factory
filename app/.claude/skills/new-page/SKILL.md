---
name: new-page
description: Add a new Facebook page. Creates facebook_pages/<slug>/ from the template and fills profile.md and sources.md by interviewing the operator. Use when the operator wants to set up a new page.
argument-hint: <page name>
disable-model-invocation: true
---

# /new-page

Page name from the operator: **$ARGUMENTS**

## Steps

1. **Name and slug.** If no page name was given, ask for it. Propose a slug (lowercase ASCII, hyphens; e.g. "Lanka Home Garden" → `lanka-home-garden`) and confirm it with the operator. Slugs starting with `_` are reserved for test pages.

2. **Create the folder.** If `facebook_pages/<slug>/` already exists, stop: offer to update its `profile.md` instead. Otherwise run:
   ```
   python utils/new_page.py <slug> --name "<Page Name>"
   ```

3. **Interview the operator.** Ask in small groups (2–4 questions per message) and wait for answers. You may suggest options based on the niche, but **never invent facts** about the page (URL, audience numbers, past results). Accept "skip" for optional items and record "not set".
   1. Page URL; niche; 3–5 content pillars (short names, because posts reference them exactly)
   2. Audience: location, age range, interests, what they care about
   3. Language(s), and how to mix them (e.g. Sinhala caption with English hashtags). For a non-English page, say that its output needs closer review, and suggest generating one test post early to check quality.
   4. Voice and tone, with 2–3 sample sentences. Ask for real past posts if they have them.
   5. Post types, posts per week, hashtag policy, call-to-action style
   6. Do / Don't: banned topics, sensitive subjects, competitor mentions
   7. Sources: trusted websites, RSS feeds, subreddits, Google Trends terms, sites to avoid. Offer to find candidate RSS feeds with web search, and test each one before adding it:
      ```
      python utils/rss_fetch.py --url <feed-url> --days 30
      ```
      Never add Facebook pages or groups as sources.

4. **Write the files.** Replace every `TODO` in `facebook_pages/<slug>/profile.md` and `sources.md` with the answers. Leave the "What works" section as it is: `/import-insights` maintains it.

5. **Post formats.** For each post type in the profile, create `facebook_pages/<slug>/templates/<post_type>.md`, following `templates/README.md` in that folder: structure, target length, one short example in the page's voice (fictional, with no real facts), and notes.

6. **Confirm.** Show a short summary of the profile and ask the operator to correct anything. Then search `facebook_pages/<slug>/` for any remaining `TODO` and resolve it.

7. **Next step:** suggest `/research <slug>`.
