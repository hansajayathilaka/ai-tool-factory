# AI Automation Framework

A personal **tool factory** for AI content automation that runs locally in [Claude Code](https://claude.com/claude-code) on a Claude subscription. Each tool researches topics and writes drafts for its channels. A human reviews every draft and publishes it manually. Every tool reuses the same engine: research, drafting, fact-checking, an approval gate, and a file-per-item lifecycle.

The design and the reasons behind it are in [docs/framework-architecture.md](docs/framework-architecture.md).

| Tool | Item | Channel | Status |
|---|---|---|---|
| [facebook](tools/facebook/CLAUDE.md) | post | Facebook page | in use |
| blog, newsletter, instagram | | | planned (roadmap) |

## Quick start
1. Install [Claude Code](https://claude.com/claude-code) and Python 3.10+. Nothing else: the helpers use the standard library only.
2. Launch Claude Code **at the repo root** (`claude` in this folder) and run `/start`. It shows the tools, the modes and the MCP servers.
3. **Use a tool** (produce content):
   ```
   /load-tool facebook
   /new-channel My Page Name
   /research my-page-name
   /generate my-page-name 3
   /finalize 2026-10-03-some-topic.md
   (post it on Facebook yourself)
   /mark-published 2026-10-03-some-topic.md
   ```
4. **Build or update a tool**: `/load-studio`, then `/new-tool blog` or `/update-tool facebook <change>`.
5. **Improve the studio itself** (`core/`, shared workflows, commands): `/build-studio <goal>`.
6. One mode per session: run `/clear` before loading another. `/help` lists the commands for the current mode.
7. Optional: put Reddit API keys in `.env` (see [core/README.md](core/README.md)), and add MCP servers (see "MCP servers" below).

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

## Modes
Claude Code is always launched at the repo root. A command loads one mode into the session:

| Command | Mode | Purpose | Loads | May change |
|---|---|---|---|---|
| `/load-tool <tool>` | tool | Research topics and generate items | `tools/<tool>/CLAUDE.md`, the style guide, `run.py info`, the workflows | `tools/<tool>/channels/`, `tools/shared/research_cache/` |
| `/load-studio [tool]` | studio | Build a new tool or update one | `studio/CLAUDE.md`, the architecture doc, the facebook example | a tool's definition: `tool.json`, `CLAUDE.md`, agents, templates, `_test` |
| `/build-studio [goal]` | studio-dev | Improve the studio itself | `studio/CLAUDE.md`, the whole architecture doc, `core/README.md` | `core/`, `studio/`, `templates/`, `tools/.claude/`, `tools/shared/`, root commands, `.mcp.json`, docs |

Two generic commands work in any mode: `/start` (tools, modes, MCP status, then pick a mode) and `/help [topic]` (the commands for the current mode, or help on one command). The root [CLAUDE.md](CLAUDE.md) is a short router: until a mode is loaded, Claude only answers questions.

How the root session loads things:
- A subfolder's `CLAUDE.md` and its `.claude/skills/` load **on demand**, the first time Claude reads a file there. `/load-tool` reads the tool's `CLAUDE.md`, which makes the shared workflows in `tools/.claude/skills/` available. `/load-studio` and `/build-studio` read `studio/CLAUDE.md`, which makes `/new-tool`, `/update-tool` and `/check-tool` available.
- Subagents are found only in the root `.claude/agents/`, so it holds **proxies** (`researcher`, `fact-checker`, `writer`). Each proxy reads the tool's real definition under `tools/` and follows it, with the same tool limits.
- The root `.claude/settings.json` holds the permissions for every mode and sets `"autoMemoryEnabled": false`. Channel knowledge belongs in channel files (`profile.md`, `insights/`), not in Claude's memory.
- Launching Claude Code inside `tools/<tool>/` still works for the shared workflows, but root launch is the documented way.

## Folder structure

```
ai-automation/                    # LAUNCH `claude` HERE
├── README.md                     # This file
├── CLAUDE.md                     # Root router: modes and session rules only
├── .mcp.json                     # Project MCP servers (secrets as ${VAR})
├── .claude/
│   ├── settings.json             # Permissions for every mode, autoMemoryEnabled=false
│   ├── skills/                   # /start, /help, /load-tool, /load-studio, /build-studio
│   └── agents/                   # Proxies: researcher, fact-checker, writer → tools/
├── docs/framework-architecture.md
├── core/                         # Stdlib Python engine shared by every tool (see core/README.md)
│   └── tests/
├── templates/
│   ├── tool/                     # Skeleton copied by /new-tool
│   └── command/SKILL.md          # Skeleton for every new command (factory.py new-command)
├── studio/                       # STUDIO: loaded by /load-studio and /build-studio
│   ├── CLAUDE.md
│   ├── factory.py                # python studio/factory.py new-tool | check-tool | check-studio | new-command | mcp | list | test
│   └── .claude/skills/           # /new-tool, /update-tool, /check-tool
└── tools/                        # TOOLS: loaded by /load-tool <tool>
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
In studio mode (`/load-studio`), `/new-tool <name>` interviews you (item, channel, sections and limits, image, export, insights), scaffolds `tools/<name>/` from `templates/tool/`, fills `tool.json`, `CLAUDE.md`, the writer and a `_test` channel with fixtures, and runs `/check-tool`. The manifest format is in [docs/framework-architecture.md §5](docs/framework-architecture.md#5-the-tool-manifest-tooljson). `/update-tool <name> <change>` changes an existing tool and keeps its manifest, item template, writer and fixtures in sync.

## Commands template
Every new command starts from [templates/command/SKILL.md](templates/command/SKILL.md): `python studio/factory.py new-command <name> --in <root|studio|shared|tool>`. The template has fixed sections: frontmatter, **Needs** (the mode it runs in), **Steps** (ending in a report and the next command) and **Rules**. `check-studio` fails while a `TODO` is left. It also checks that command names are unique across the root, studio and shared commands.

## MCP servers
- **Project servers** go in the root [.mcp.json](.mcp.json) (empty to start with). Claude Code reads it only from the launch folder, which is why sessions start at the root. Put secrets in environment variables and reference them as `${VAR}`. Claude Code expands them from its own environment, not from `.env`. `check-studio` rejects a literal secret and any Meta host. Claude Code asks you to approve each project server the first time it is used.
- **claude.ai connectors** (Gmail, Google Drive, Calendar…) need no entry. They are named by their server name, e.g. `claude_ai_Google_Drive`.
- **A tool opts in** by listing server names in `tool.json` → `"mcp": [...]`, and its `CLAUDE.md` section "MCP servers" says which workflow step uses each one and how. `/load-tool` reports their status.
- `python studio/factory.py mcp` lists the servers and the tools that use them. `/mcp` in Claude Code shows the live connection state.
- No MCP server may publish, schedule or post, or reach a Meta property.

## Data sources

| Source | How | Notes |
|---|---|---|
| Web search / news sites | Claude Code web search and fetch | Main research source |
| Niche RSS feeds | Listed in each channel's `sources.md`; `python run.py rss` | Reliable and cheap to check |
| Google Trends | Checked manually | No official API |
| Reddit | `python run.py reddit`, API keys optional | Good signal for community interest |
| Engagement | **Manual** CSV export from the platform → `insights/` | The only feedback loop, because publishing is manual |
| MCP servers | Declared per tool in `tool.json` → `mcp` | Optional; see "MCP servers" |
| Facebook, Instagram, Threads | **Never used** | Blocked in the validator, the agents, the permissions and the MCP checks |

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
