# Shared research cache

Channel-neutral research that several channels, in any tool, can reuse: for example a news story that becomes a Facebook post, an Instagram post and a newsletter story.

- One note per topic: `YYYY-MM-DD-<topic-slug>.md`, in the format of `../research_note.md`, with `channel: shared` and no `pillar`.
- Notes hold facts and sources only. Channel-specific angles go in each channel's own `research/` note, which links back here through its `cache:` field.
- Freshness: reuse `kind: news` notes for up to **7 days** after `created`, and `kind: evergreen` notes for up to **90 days**. After that, research again.
