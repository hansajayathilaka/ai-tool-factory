# Style guide (all pages)

These rules apply to every page. A page's `profile.md` adds to them. Where the two conflict, the **stricter** rule wins.

## 1. Facts and sources
- **No unsupported facts.** Every factual claim (numbers, dates, names, events, quotes, "studies show", cause and effect) must trace to a source in the post's `sources` list.
- List in `## Reviewer notes` each claim and the source that supports it, e.g. `- "Rice prices rose 12% in September" → [1]`. The `[n]` number is the position of the source in the `sources` list, counting from 1.
- Prefer primary sources: official bodies, original studies, company announcements, reputable news outlets reporting first-hand. Avoid content farms, aggregators and anything in the page's "Avoid" list.
- Don't state things more certainly than the source does. "May", "early study" and "according to" must survive into the post.
- Developing story: say so ("Reports so far say…"), and put a reviewer note to re-check before posting.
- Dates: use absolute dates. Avoid "yesterday" or "this week", because the post may go out days later.
- Opinion is allowed only in the page's voice, and must be clearly opinion ("We think…"), never presented as fact.

## 2. Originality
- **No copying.** Summarize and rewrite in the page's voice. Never paste sentences from a source.
- Short direct quotes (one sentence at most) are allowed only in quotation marks, with the speaker named and the source listed.
- Don't imitate another page's or brand's signature formats or catchphrases.

## 3. Images
- `image.kind` is one of:
  - `own-photo`: the page owner takes or has the photo. Describe the shot.
  - `stock`: licensed stock (e.g. Unsplash or Pexels free licenses, or a paid library). Give search keywords. Never pick a specific copyrighted image.
  - `ai-generated`: give a generation prompt.
  - `none`: text-only post.
- **Never** use images from news sites, other Facebook pages, Google Images or social media without a license.
- **AI-generated realistic images** (photorealistic people, places or events) must set `needs_ai_label: true`, because Meta requires the "AI info" label. Illustrations and obvious graphics can be `false`. When unsure, use `true`.
- Never generate realistic images of real, identifiable people, or of news events presented as if they were photographs.

## 4. Engagement
- **No engagement bait.** Facebook ranks it lower. Banned patterns include:
  - "Comment YES / Type AMEN / Like if you agree"
  - "Share if…", "Tag a friend who…", "Share before it's deleted"
  - Fake urgency, misleading "you won't believe" hooks, or clickbait that the post doesn't deliver on
- Genuine questions are fine ("What's your go-to monsoon recipe?"), because they invite real conversation.
- Follow the page's call-to-action style.

## 5. Topics
- **No duplicate topics.** Before writing, check `posted/`, `finalized/` and `drafts/` (`python utils/posted_topics.py <slug> --status all`). Revisiting a topic is allowed only with a clearly new angle or new information, and must be flagged in reviewer notes as a deliberate repeat.
- **Respect the page's Do / Don't list.** It overrides anything trending.
- Sensitive subjects (health, finance, law, elections, religion, ethnicity, tragedies, minors): be neutral and careful. Use only authoritative sources. Health and finance posts must not give personal advice; point to professionals. Don't post about a tragedy in a way that seeks engagement from it.
- No defamation: don't accuse named people or businesses of wrongdoing unless a reputable source reports it, and attribute it ("according to…").

## 6. Writing
- Lead with the hook: the first line is what people see before "See more".
- Short paragraphs and plain words. Write for a phone screen.
- Match the page's language. Non-English drafts: write natively, never as a word-for-word translation of English. Put any phrasing you are unsure of in reviewer notes.
- Emojis and hashtags: follow the page's policy. With no policy, use at most 3 relevant hashtags and no hashtag spam.
- Links: if the post links to a source, use the canonical article URL, not a tracking link.

## 7. Process
- **A human always reviews a post before it is finalized and posted.**
- Every draft starts with `fact_check: pending`. Only the fact-checker, run by `/finalize-post`, sets it to `passed` or `failed`.
- Any edit after a fact-check resets it to `pending`.
