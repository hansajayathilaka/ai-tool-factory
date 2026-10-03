# Shared research cache

Page-neutral research that several pages can reuse, for example a news story relevant to more than one niche.

- One note per topic: `YYYY-MM-DD-<topic-slug>.md`, in the format of `templates/research_note.md`, with `page: shared` and no `pillar`.
- Notes hold facts and sources only. Page-specific angles go in each page's own `research/` note, which links back here through its `cache:` field.
- Freshness: reuse `kind: news` notes for up to **7 days** after `created`, and `kind: evergreen` notes for up to **90 days**. After that, research again.
