# AI Automation — Facebook Post Generator

> Planned: turning this into a framework for several automation tools (blog, newsletter, Instagram…). See [docs/framework-architecture.md](docs/framework-architecture.md).

## Quick start
1. Install [Claude Code](https://claude.com/claude-code) and Python 3.10+.
2. Check the absolute path in `app/.claude/settings.local.json` (`claudeMdExcludes`). It must point to this repo's root `CLAUDE.md` on your machine.
3. **Generate mode:** `cd app && claude`, then run `/memory` once to confirm the root `CLAUDE.md` is not listed. Then:
   ```
   /new-page My Page Name
   /research my-page-name
   /generate-posts my-page-name 3
   /finalize-post 2026-10-03-some-topic.md
   (post it on Facebook yourself)
   /mark-posted 2026-10-03-some-topic.md
   ```
4. **Build mode:** run `claude` from the repo root. Test changes against `app/facebook_pages/_test/`.
5. Optional: put Reddit API keys in `.env` (see [app/utils/README.md](app/utils/README.md)).

## Goal
Research topics and generate ready-to-post Facebook content for multiple Facebook pages, using **Claude Code** as the agent. Each page has its own audience, voice and history, and the agent tailors posts to it.

## Scope

**In scope**
- Researching trending and relevant topics for each page's niche
- Generating post drafts (caption, hashtags, image idea) tailored to each page
- Fact-checking drafts against their sources
- Rewriting drafts on request
- Tracking what has been posted, to avoid repeating topics
- Learning from engagement data that is exported manually

**Out of scope (non-goals)**
- Scheduling or publishing posts. Posting is done **manually** by a human.
- Any agent other than Claude Code
- Scraping Facebook. This breaks Facebook's Terms of Service.
- Automatic access to the Meta Graph API (may be considered later)

## Two modes of working

| | Build mode | Generate mode |
|---|---|---|
| **Purpose** | Develop and improve the app (skills, subagents, templates, utils) | Research topics and generate posts |
| **Launch Claude Code from** | Repository root (`ai-automation/`) | `app/` folder |
| **Instructions file** | `/CLAUDE.md` | `/app/CLAUDE.md` |
| **Who uses it** | Developer | Content operator |

### Keeping the two modes separate
Claude Code loads `CLAUDE.md` files from the launch folder **and every parent folder**. It also loads project skills from `.claude/skills/` in the launch folder and every parent folder up to the repo root. Without the safeguards below, generate-mode sessions would also see build-mode instructions and skills.

1. **Exclude the root CLAUDE.md in generate mode.** Add this to `app/.claude/settings.local.json` (machine-specific, not committed):
   ```json
   {
     "claudeMdExcludes": ["D:/Work/Waruna/ai-automation/CLAUDE.md"]
   }
   ```
   Use the absolute path for your machine. Check it worked by running `/memory` in a generate-mode session: the root `CLAUDE.md` must not be listed.
2. **Do not put skills or subagents in the root `.claude/` folder.** Everything the app needs lives in `app/.claude/`. Build mode doesn't need its own skills. If it ever does, document why it is safe for them to show up in generate mode too.
3. **Turn off auto memory in generate mode.** Auto memory is shared across the whole git repo, so generate-mode learnings would mix with build-mode notes. Set `"autoMemoryEnabled": false` in `app/.claude/settings.json`. Page knowledge belongs in the page's own files (`profile.md`, `insights/`), not in Claude's memory.

In build mode, Claude also reads `app/CLAUDE.md` when it opens files under `app/`. That is intended: the developer needs to understand how the app behaves.

## Folder structure

```
ai-automation/
├── CLAUDE.md                     # Build-mode instructions (how to develop the app)
├── README.md                     # This file
├── .gitignore
└── app/
    ├── CLAUDE.md                 # Generate-mode instructions (how to produce posts)
    ├── .claude/
    │   ├── settings.json         # Committed: permissions, autoMemoryEnabled=false
    │   ├── settings.local.json   # Not committed: claudeMdExcludes (absolute path)
    │   ├── skills/               # Workflows, run as slash commands (see "Workflows")
    │   │   ├── new-page/SKILL.md
    │   │   ├── research/SKILL.md
    │   │   ├── generate-posts/SKILL.md
    │   │   ├── rewrite-post/SKILL.md
    │   │   ├── finalize-post/SKILL.md
    │   │   ├── mark-posted/SKILL.md
    │   │   └── import-insights/SKILL.md
    │   └── agents/               # Subagents with their own context window
    │       ├── researcher.md
    │       ├── writer.md
    │       └── fact-checker.md
    ├── shared/
    │   ├── style_guide.md        # Writing and safety rules for every page
    │   └── research_cache/       # Topic research reusable by several pages
    ├── templates/
    │   ├── page/                 # Skeleton copied by /new-page
    │   └── post.md               # Post file template (see "Post file format")
    ├── utils/                    # Helper scripts (e.g. RSS fetch, insights CSV parsing)
    └── facebook_pages/
        └── <page-slug>/
            ├── profile.md        # Who the page is for and how it sounds
            ├── sources.md        # Trusted sources / RSS feeds for this niche
            ├── templates/        # Post formats that work for this page
            ├── research/         # Research notes, one file per topic
            ├── drafts/           # Generated posts awaiting review
            ├── finalized/        # Reviewed and fact-checked, ready to post
            ├── posted/           # Posted manually; used to avoid repeat topics
            └── insights/         # Engagement exports from Meta Business Suite
```

A post's **folder is its status**. Moving a file from `drafts/` → `finalized/` → `posted/` is the only way its status changes.

## Page profile (`profile.md`)
Every page needs a profile before generating posts. `/new-page` creates it by asking the operator questions.

- **Page name and URL**
- **Niche and content pillars**: the 3–5 recurring themes
- **Audience**: location, age range, interests, what they care about
- **Language(s)**: e.g. English, Sinhala, Tamil, or mixed. Test output quality per language early, because non-English output needs closer review.
- **Voice and tone**: e.g. friendly, expert, humorous; include sample sentences
- **Post types**: news summary, tip, question, listicle, quote, story, etc.
- **Posting frequency**: posts per week, to size each batch
- **Hashtag policy**
- **Call-to-action style**
- **Do / Don't**: banned topics, sensitive subjects, competitor mentions
- **What works**: updated from `insights/` by `/import-insights`

## Post file format
One markdown file per post, named `YYYY-MM-DD-<topic-slug>.md`:

```markdown
---
page: <page-slug>
topic: <short topic>
pillar: <content pillar from profile>
post_type: <tip | news | question | ...>
language: en
created: 2026-10-03
posted: <date, filled by /mark-posted>
sources:
  - url: https://...
    title: ...
    accessed: 2026-10-03
image:
  kind: none | own-photo | stock | ai-generated
  idea: <description or generation prompt>
  needs_ai_label: false
fact_check: pending | passed | failed
---

## Caption
<post text>

## Hashtags
#...

## Alternatives
<optional: 1–2 alternative hooks or shorter versions>

## Reviewer notes
<claims to double-check, assumptions, anything the human should know>
```

## Post lifecycle

```
/research ──► research/ ──► /generate-posts ──► drafts/
                                                 │  ▲
                                                 │  └── /rewrite-post
                                                 ▼
                              /finalize-post (fact-check + human approval) ──► finalized/
                                                                                │
                                                       human posts on Facebook  │
                                                                                ▼
                                                              /mark-posted ──► posted/
```

## Workflows (slash commands)
Workflows are Claude Code skills in `app/.claude/skills/`. The operator runs them as slash commands.

| Command | Input | What it does | Output |
|---|---|---|---|
| `/new-page` | Page name | Asks profile questions, copies `templates/page/` | `facebook_pages/<slug>/` with `profile.md`, `sources.md` |
| `/research` | Page (optional topic) | Finds current topics in the page's niche using `sources.md` and web search, checks `posted/` to avoid repeats, reuses `shared/research_cache/` | Notes in `research/`, each with source links |
| `/generate-posts` | Page, number of posts | Writes drafts from research, following `profile.md`, `templates/` and `shared/style_guide.md` | Files in `drafts/` |
| `/rewrite-post` | Draft file, instructions | Rewrites a draft (tone, length, angle, language) and keeps the sources | Updated draft |
| `/finalize-post` | Draft file | Runs the fact-checker; on pass and operator approval, moves the post to `finalized/` | File in `finalized/` |
| `/mark-posted` | Finalized file, date | Records the posting date and moves the post to `posted/` | File in `posted/` |
| `/import-insights` | Page, exported CSV | Summarizes Meta Business Suite engagement data and updates "What works" in `profile.md` | `insights/` summary, updated profile |

## Subagents
Subagents run in their own context window, so heavy research doesn't fill the main session.

- **researcher**: searches the web and reads sources, then returns short notes with URLs. Read-only plus web tools.
- **writer**: turns research into drafts in the page's voice.
- **fact-checker**: checks every factual claim in a draft against its sources and flags anything unsupported. Read-only.

## Data sources

| Source | How | Notes |
|---|---|---|
| Web search / news sites | Claude Code web search and fetch | Main research source |
| Niche RSS feeds | Listed in each page's `sources.md`; optional `utils/` script | Reliable and cheap to check |
| Google Trends | Checked manually, or with an unofficial library | No official API; unofficial libraries often break |
| Reddit | Public API | Good signal for community interest |
| Page engagement | **Manual** CSV export from Meta Business Suite → `insights/` | The only feedback loop, because posting is manual |
| Facebook feeds / other pages | **Not used** | Scraping breaks Facebook's Terms of Service |

## Content quality and safety rules
These rules go in `shared/style_guide.md` and apply to every page.

- **No unsupported facts.** Every factual claim must trace back to a source in the post's `sources`.
- **No copying.** Summarize and rewrite sources; never paste their text.
- **Images:** never use images from news sites or other pages without a license. Mark AI-generated realistic images `needs_ai_label: true`, because Meta requires a label.
- **No engagement bait** ("comment YES", "share if you agree"). Facebook ranks these posts lower.
- **No duplicate topics.** Check `posted/` before writing.
- **Respect each page's Do / Don't list.**
- **A human always reviews a post before it is finalized and posted.**

## Secrets and git
- Store API keys (e.g. Reddit) in environment variables or a `.env` file listed in `.gitignore`. Never commit them.
- Never commit `settings.local.json`.
- Decide whether `facebook_pages/*/research/` and `insights/` are committed. Research notes grow quickly, and insights may hold private page data.

## Root `CLAUDE.md` (build mode)
Instructions for developing the app:
- What the project is, and a link to this README
- The two modes and the isolation rules above (especially: no skills in the root `.claude/`)
- How to write and test skills and subagents in `app/.claude/`
- Conventions for `utils/` scripts (language, how to run them)
- Testing: run a workflow in generate mode against a test page (e.g. `facebook_pages/_test/`) before treating a change as done

## `app/CLAUDE.md` (generate mode)
Instructions for producing content:
- The folder layout and the "folder is status" rule
- Always read the page's `profile.md` and `shared/style_guide.md` before writing
- The list of available workflows and when to use each
- Never create posts outside a page folder; never post to Facebook
- Ask the operator when a page or request is unclear instead of guessing

## Roadmap
1. **Foundation**: folder skeleton, both `CLAUDE.md` files, isolation settings, `/new-page`, page template
2. **Research and drafts**: `/research`, `/generate-posts`, researcher and writer subagents, style guide
3. **Quality gate**: fact-checker, `/finalize-post`, `/rewrite-post`, `/mark-posted`, duplicate-topic check
4. **Feedback loop**: `/import-insights` and "What works" updates in the profile

## Success criteria
- Most drafts need only light editing before they are finalized
- No post is finalized with an unsupported claim
- No topic is repeated on a page unless it is deliberate
- Engagement per post, from `insights/`, improves over the page's baseline

## Open decisions
- How many pages to start with, and their niches and languages?
- ~~Language and runtime for `utils/` scripts~~. **Decided:** Python 3.10+, standard library only.
- Commit research and insights data to git, or keep them local? **Current default:** research notes and insight *summaries* are committed. Raw CSV/XLSX exports are gitignored (`facebook_pages/*/insights/*.csv`). Revisit if research grows too large.
- Use the Meta Graph API for insights later, instead of manual CSV export?
