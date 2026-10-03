---
name: new-channel
description: Add a new channel to the current tool (a Facebook page, a blog, a newsletter segment...). Creates channels/<slug>/ from the tool's template and fills profile.md and sources.md by interviewing the operator. Use when the operator wants to set up a new channel.
argument-hint: <channel name>
disable-model-invocation: true
---

# /new-channel

Channel name from the operator: **$ARGUMENTS**

Use the tool's own words (its `CLAUDE.md` "Words" table): on the Facebook tool a channel is a "page".

## Steps

1. **Name and slug.** If no name was given, ask for it. Propose a slug (lowercase ASCII, hyphens; e.g. "Lanka Home Garden" → `lanka-home-garden`) and confirm it with the operator. Slugs starting with `_` are reserved for test channels.

2. **Create the folder.** If `channels/<slug>/` already exists, stop: offer to update its `profile.md` instead. Otherwise run:
   ```
   python run.py new-channel <slug> --name "<Channel Name>"
   ```

3. **Interview the operator.** Read the new `profile.md` and `sources.md`: their `TODO`s are the questions. Ask in small groups (2–4 questions per message) and wait for answers. You may suggest options based on the niche, but **never invent facts** about the channel (URL, audience numbers, past results). Accept "skip" for optional items and record "not set".
   - For a non-English channel, say that its output needs closer review, and suggest generating one test item early to check quality.
   - Ask for real past items if they have them, to capture the voice.
   - Sources: offer to find candidate RSS feeds with web search, and test each one before adding it:
     ```
     python run.py rss --url <feed-url> --days 30
     ```
     Never add Facebook, Instagram or other Meta pages or groups as sources.

4. **Write the files.** Replace every `TODO` in `channels/<slug>/profile.md` and `sources.md` with the answers. Leave the "What works" section as it is: `/import-insights` maintains it.

5. **Formats.** For each item type in the profile, create `channels/<slug>/formats/<item_type>.md`, following `formats/README.md` in that folder: structure, target length, one short example in the channel's voice (fictional, with no real facts), and notes. Respect the limits in `python run.py info`.

6. **Confirm.** Show a short summary of the profile and ask the operator to correct anything. Then search `channels/<slug>/` for any remaining `TODO` and resolve it.

7. **Next step:** suggest `/research <slug>`.
