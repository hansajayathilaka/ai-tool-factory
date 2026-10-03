# AI Automation Framework

A personal **tool factory** for AI content automation that runs locally in [Claude Code](https://claude.com/claude-code) on a Claude subscription. Each tool researches topics and writes drafts for its channels. A human reviews every draft and publishes it manually. Every tool reuses the same engine: research, drafting, fact-checking, an approval gate, and a file-per-item lifecycle.

The design and the reasons behind it are in [docs/framework-architecture.md](docs/framework-architecture.md).

| Tool | Item | Channel | Status |
|---|---|---|---|
| [facebook](tools/facebook/CLAUDE.md) | post | Facebook page | in use |
| blog, newsletter, instagram | | | planned (roadmap) |

## Quick start
1. Install [Claude Code](https://claude.com/claude-code) and Python 3.10+. Nothing else: the helpers use the standard library only.
2. **Generate mode** (produce content): `cd tools/facebook && claude`. Run `/memory` once to confirm that only `tools/facebook/CLAUDE.md` is listed. Then:
   ```
   /new-channel My Page Name
   /research my-page-name
   /generate my-page-name 3
   /finalize 2026-10-03-some-topic.md
   (post it on Facebook yourself)
   /mark-published 2026-10-03-some-topic.md
   ```
3. **Build mode** (develop the framework or a new tool): `cd studio && claude`. Then `/new-tool blog` to build a tool, or `/check-tool all` after a change.
4. Optional: put Reddit API keys in `.env` (see [core/README.md](core/README.md)).

## Scope

**In scope**
- Researching trending and relevant topics for each channel's niche
- Generating drafts tailored to each channel, in each tool's format
- Fact-checking drafts against their sources
- Rewriting drafts on request
- Tracking what has been published, to avoid repeating topics
- Learning from engagement data that is exported manually

**Out of scope (non-goals)**
- Scheduling or publishing. A human publishes every item **manually**.
- Paid SaaS, multi-user accounts, billing, a hosted server, or any agent runtime other than Claude Code
- Scraping Facebook, Instagram or other Meta properties. This breaks their Terms of Service.
- Third-party Python packages

## Concepts
| Term | Meaning | Facebook tool |
|---|---|---|
| **Tool** | One kind of output; one Claude Code workspace in `tools/<tool>/` | `tools/facebook/` |
| **Channel** | One audience or brand inside a tool, with its own profile and history | a Facebook page |
| **Item** | One unit of output, one markdown file | a post |
| **Note** | Sourced research on one topic | |
| **Lifecycle** | `drafts/ → finalized/ → published/`. The folder **is** the status. | |
| **Manifest** | `tool.json`: the tool's nouns, item sections, limits and rules | |

## Two modes of working

| | Build mode | Generate mode |
|---|---|---|
| **Purpose** | Develop `core/`, the shared workflows, and tools | Research topics and generate items |
| **Launch Claude Code from** | `studio/` | `tools/<tool>/` |
| **Instructions file** | `studio/CLAUDE.md` | `tools/<tool>/CLAUDE.md` |
| **Who uses it** | Developer | Content operator |

Claude Code loads `CLAUDE.md`, `.claude/skills/` and `.claude/agents/` from the launch folder **and every parent folder**. The layout uses that:
- `tools/.claude/` holds the shared workflows and agents, so every tool inherits them.
- `studio/` is a sibling of `tools/`, never a parent, so build-mode instructions and skills never reach a tool session.
- There is **no `CLAUDE.md` at the repo root**, or it would leak into every session.
- Each tool sets `"autoMemoryEnabled": false`. Channel knowledge belongs in channel files (`profile.md`, `insights/`), not in Claude's memory.

## Folder structure

```
ai-automation/
├── README.md                     # This file (no CLAUDE.md at the root, on purpose)
├── docs/framework-architecture.md
├── core/                         # Stdlib Python engine shared by every tool (see core/README.md)
│   └── tests/
├── templates/tool/               # Skeleton copied by /new-tool
├── studio/                       # BUILD MODE: launch `claude` here
│   ├── CLAUDE.md
│   ├── factory.py                # python factory.py new-tool | check-tool | list | test
│   └── .claude/skills/           # /new-tool, /check-tool
└── tools/                        # GENERATE MODE: launch `claude` in tools/<tool>/
    ├── .claude/
    │   ├── skills/               # Shared workflows (see "Workflows")
    │   └── agents/               # researcher.md, fact-checker.md
    ├── shared/
    │   ├── style_guide.md        # Writing and safety rules for every tool
    │   ├── research_note.md      # Research note format
    │   └── research_cache/       # Research reusable across channels and tools
    └── facebook/
        ├── CLAUDE.md             # Facebook rules and vocabulary
        ├── tool.json             # Manifest: nouns, post format, limits
        ├── run.py                # python run.py <command> → core
        ├── .claude/
        │   ├── settings.json     # Permissions, autoMemoryEnabled=false
        │   └── agents/writer.md  # The Facebook writer
        ├── templates/
        │   ├── item.md           # Post file template
        │   └── channel/          # Page skeleton copied by /new-channel
        └── channels/
            └── <slug>/
                ├── profile.md    # Who the channel is for and how it sounds
                ├── sources.md    # Trusted sources, RSS feeds, subreddits
                ├── formats/      # Item formats that work for this channel
                ├── research/     # Research notes, one file per topic
                ├── drafts/       # Generated items awaiting review
                ├── finalized/    # Reviewed and fact-checked, ready to publish
                ├── published/    # Published manually; used to avoid repeat topics
                └── insights/     # Engagement exports and summaries
```

## Item lifecycle

```
/research ──► research/ ──► /generate ──► drafts/
                                           │  ▲
                                           │  └── /rewrite
                                           ▼
                       /finalize (fact-check + human approval) ──► finalized/
                                                                     │
                                          human publishes by hand    │
                                                                     ▼
                                                /mark-published ──► published/
```
Moves happen only through `python run.py move finalize|publish|reopen`, never a raw `mv`.

## Workflows (slash commands)
Shared by every tool, in `tools/.claude/skills/`. They speak the tool's own words (on the Facebook tool: "post", "page").

| Command | Input | What it does | Output |
|---|---|---|---|
| `/new-channel` | Channel name | Asks profile questions, copies the tool's `templates/channel/` | `channels/<slug>/` with `profile.md`, `sources.md`, `formats/` |
| `/research` | Channel (optional topic) | Finds current topics using `sources.md` and web search, checks for repeats, reuses `research_cache/` | Notes in `research/`, each with source links |
| `/generate` | Channel, number of items | Writes drafts from research with the tool's `writer`, following `profile.md`, `formats/`, `tool.json` and the style guide | Files in `drafts/` |
| `/rewrite` | Draft file, instructions | Rewrites a draft (tone, length, angle, language) and keeps the sources | Updated draft |
| `/finalize` | Draft file | Runs the fact-checker; on pass and operator approval, moves the item to `finalized/` | File in `finalized/` |
| `/mark-published` | Finalized file, date | Records the publishing date and moves the item to `published/` | File in `published/` |
| `/import-insights` | Channel, exported CSV | Summarizes engagement data and updates "What works" in `profile.md` | `insights/` summary, updated profile |

## Subagents
Subagents run in their own context window, so heavy research doesn't fill the main session.
- **researcher** (shared): searches the web and reads sources, then returns short notes with URLs. Read-only plus web tools.
- **fact-checker** (shared): checks every factual claim in a draft against its sources and flags anything unsupported. Read-only.
- **writer** (one per tool): turns research into drafts in the tool's format and the channel's voice.

## Building a new tool
In build mode, `/new-tool <name>` interviews you (item, channel, sections and limits, image, export, insights), scaffolds `tools/<name>/` from `templates/tool/`, fills `tool.json`, `CLAUDE.md`, the writer and a `_test` channel with fixtures, and runs `/check-tool`. The manifest format is in [docs/framework-architecture.md §5](docs/framework-architecture.md#5-the-tool-manifest-tooljson).

## Data sources

| Source | How | Notes |
|---|---|---|
| Web search / news sites | Claude Code web search and fetch | Main research source |
| Niche RSS feeds | Listed in each channel's `sources.md`; `python run.py rss` | Reliable and cheap to check |
| Google Trends | Checked manually | No official API |
| Reddit | `python run.py reddit`, API keys optional | Good signal for community interest |
| Engagement | **Manual** CSV export from the platform → `insights/` | The only feedback loop, because publishing is manual |
| Facebook, Instagram, Threads | **Never used** | Blocked in the validator, the agents and the tool permissions |

## Content quality and safety rules
In `tools/shared/style_guide.md`, for every tool:
- **No unsupported facts.** Every factual claim must trace back to a source in the item's `sources`.
- **No copying.** Summarize and rewrite sources; never paste their text.
- **Images:** never use images without a license. Mark AI-generated realistic images `needs_ai_label: true`.
- **No engagement bait** ("comment YES", "share if you agree").
- **No duplicate topics.** Check `published/` before writing.
- **Respect each channel's Do / Don't list.**
- **A human always reviews an item before it is finalized and published.**

## Secrets and git
- Store API keys (e.g. Reddit) in environment variables or a `.env` file listed in `.gitignore`. Never commit them.
- Never commit `settings.local.json`.
- Research notes and insight *summaries* are committed. Raw CSV/XLSX exports are gitignored (`tools/*/channels/*/insights/*.csv`), because they may hold private data.

## Success criteria
- Most drafts need only light editing before they are finalized
- No item is finalized with an unsupported claim
- No topic is repeated on a channel unless it is deliberate
- Engagement per item, from `insights/`, improves over the channel's baseline
- A new tool takes about 30 minutes to build with `/new-tool`

## Open decisions
- Use the Meta Graph API for insights later, instead of manual CSV export?
- Should channels be shared across tools (one brand with FB + IG + newsletter outputs)? Decide after the second tool.
- Unattended research with `claude -p` from Windows Task Scheduler: headless runs work with a subscription login (checked 2026-10-03), but there is no scheduler setup yet.
