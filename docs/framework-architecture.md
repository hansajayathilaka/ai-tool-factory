# AI Automation Framework — architecture

Status: **built** (roadmap steps 1–2, 2026-10-03). **Root launch, modes and MCP support added 2026-10-03 (§12)**: Claude Code is now launched at the repo root and `/load-tool`, `/load-studio` and `/build-studio` load a mode. §3–4 describe the folder isolation the layout still relies on. The framework, the shared workflows and the migrated Facebook tool exist. Deviations from the original proposal are marked *Changed in build*. The overview is in [README.md](../README.md).

## 1. Vision

Turn the Facebook post generator into a **personal tool factory**: a small framework for quickly building AI automation tools that run locally in Claude Code. Examples:

- Facebook post generator (built: `tools/facebook/`)
- Instagram post generator
- Blog post generator
- Tailored newsletter

Every tool follows the same pattern, proven by the Facebook tool:

> **Research → write items → validate → human approval → publish manually**, with each item stored as a markdown file whose **folder is its status**.

The framework provides that pattern once. A new tool only describes what makes it different: its item format, limits, voice and writer.

### Non-goals (unchanged from the Facebook app)
- No paid SaaS, no multi-user accounts, no billing, no hosted server.
- No auto-publishing or scheduling to social platforms. A human publishes.
- No scraping Facebook, Instagram or other Meta properties.
- Python helpers use the standard library only.

### Runtime constraints
The tools run on a **Claude Pro subscription**, which decides the runtime:

| Option | Works with Pro? | Decision |
|---|---|---|
| Interactive Claude Code (`claude`) | Yes | **The runtime.** Every tool is a Claude Code workspace. |
| Claude Agent SDK / Claude API from a web backend | No, needs an API key and pay-per-token billing | Not used |
| Headless `claude -p "/skill …"` | Yes: ran with the subscription login on 2026-10-03 | Optional extra for unattended research (§8) |

## 2. Core concepts

The Facebook app's terms generalise as follows.

| Facebook app before | Framework term | Meaning | Examples |
|---|---|---|---|
| `app/` | **Tool** | One kind of output, one Claude Code workspace | facebook, instagram, blog, newsletter |
| page (`facebook_pages/<slug>/`) | **Channel** | One audience or brand inside a tool, with its own profile and history | a FB page, an IG account, a blog, a newsletter segment |
| post | **Item** | One unit of output, one markdown file | post, article, newsletter issue |
| research note | **Note** | Sourced research, one file per topic | unchanged |
| `drafts/ → finalized/ → posted/` | **Lifecycle** | `drafts/ → finalized/ → published/` | unchanged rules |
| hard-coded checks in `common.validate_post` | **Item schema** | Declared per tool in `tool.json` | sections, limits, required fields |
| `researcher`, `fact-checker` | **Shared agents** | Work the same for every tool | unchanged |
| `writer` | **Tool agent** | Knows one output format | one per tool |

Rules that carry over unchanged:
- A file's folder is its status. Status changes only through the lifecycle command, never a raw `mv`.
- Every factual claim traces to a source in the item's `sources`.
- A human explicitly approves every item before it reaches `finalized/`.
- Channel knowledge lives in channel files (`profile.md`, `insights/`), never in Claude's memory.

## 3. How Claude Code makes sharing possible

Three Claude Code behaviours decide the folder layout. The first two were confirmed by a spike on 2026-10-03 (Claude Code 2.1.278): a throwaway `tools/.claude/` and `tools/demo/`, with `claude -p` launched from `tools/demo/`.

1. **Skills and subagents are inherited from parent folders.** Claude Code loads `.claude/skills/` and `.claude/agents/` from the launch folder and every parent folder up to the repo root. When a parent and the launch folder define a **skill with the same name, the launch folder's copy wins**. For subagents, the definition closest to the launch folder wins.
   → Shared workflows and agents live **once** in `tools/.claude/`. Every tool in `tools/<name>/` gets them automatically. A tool can override a shared agent by defining one with the same name.
2. **`CLAUDE.md` is also inherited from parent folders.** The spike saw the old root `CLAUDE.md` in the `tools/demo/` session.
   → There must be **no `CLAUDE.md` at the repo root** or in `tools/`, or it leaks into every tool session. Build-mode instructions live in a sibling folder, `studio/`, which is never a parent of a tool. This replaced the machine-specific `claudeMdExcludes` workaround with isolation built into the folder layout. A unit test (`test_no_claude_md_above_tools`) keeps it that way.
3. **Skills can declare `disable-model-invocation`, `argument-hint`, `allowed-tools` and `model`**, and can read supporting files in their own folder.
   → Shared skills stay small and read tool-specific details from `python run.py info` and the tool's `CLAUDE.md`.

## 4. Folder layout

```
ai-automation/
├── README.md                        # framework overview (NO CLAUDE.md at the root)
├── docs/
│   └── framework-architecture.md    # this file
│
├── core/                            # stdlib Python package shared by all tools
│   ├── common.py                    # repo paths, status folders, slug/date helpers, utf8_stdout, load_env
│   ├── tool.py                      # Tool (folder + manifest), check_manifest
│   ├── frontmatter.py               # parser, set_field, sections     (from common.py)
│   ├── validate.py                  # schema-driven item checks       (from common.py + check_post.py)
│   ├── lifecycle.py                 # finalize / publish / reopen     (from move_post.py)
│   ├── topics.py                    # covered-topic listing           (from posted_topics.py)
│   ├── insights.py                  # engagement CSV summary          (from insights_summary.py)
│   ├── sources/rss.py, reddit.py    # signal fetchers                 (from rss_fetch.py, reddit_top.py)
│   ├── scaffold.py                  # new tool / new channel          (from new_page.py)
│   ├── export.py                    # item → txt / md / html for copy-paste publishing
│   ├── cli.py                       # tool commands (python run.py ...)
│   ├── factory.py                   # studio commands (python studio/factory.py ...)
│   └── tests/
│
├── templates/
│   └── tool/                        # skeleton copied by /new-tool
│
├── studio/                          # BUILD MODE: run `claude` here
│   ├── CLAUDE.md                    # how to develop core/ and tools/
│   ├── factory.py                   # shim: python studio/factory.py <command> (§12)
│   └── .claude/
│       ├── settings.json            # additionalDirectories: ../core, ../tools, ../templates, ../docs
│       └── skills/
│           ├── new-tool/SKILL.md    # interview → scaffold → fill → check
│           └── check-tool/SKILL.md  # unit tests + check a tool and its _test fixtures
│
└── tools/                           # GENERATE MODE: run `claude` in tools/<tool>/
    ├── .claude/                     # inherited by every tool
    │   ├── skills/
    │   │   ├── new-channel/   research/   generate/   rewrite/
    │   │   └── finalize/   mark-published/   import-insights/
    │   └── agents/
    │       ├── researcher.md        # read-only + web
    │       └── fact-checker.md      # read-only + WebFetch
    ├── shared/
    │   ├── style_guide.md           # rules for every tool and channel
    │   ├── research_note.md         # research note format
    │   └── research_cache/          # notes reusable across channels AND tools
    │
    └── <tool>/                      # facebook today; blog, newsletter, instagram, ...
        ├── CLAUDE.md                # tool vocabulary and rules (fixed sections, §6)
        ├── tool.json                # manifest + item schema (§5)
        ├── run.py                   # shim: python run.py <cmd> → core.cli with TOOL_DIR = here
        ├── .claude/
        │   ├── settings.json        # autoMemoryEnabled: false, permissions
        │   └── agents/writer.md     # format-specific writer
        ├── templates/
        │   ├── item.md              # item file template
        │   └── channel/             # channel skeleton (profile.md, sources.md, formats/)
        └── channels/
            ├── _test/               # test channel, with fixtures/valid/ and fixtures/invalid/
            └── <slug>/
                ├── profile.md   sources.md   formats/
                ├── research/
                ├── drafts/   finalized/   published/
                └── insights/
```

*Changed in build:*
- `core/` is a Python package with relative imports, so module names like `validate` can't clash with installed packages. The proposed `paths.py` became `common.py` (paths and helpers) plus `tool.py` (the `Tool` object every command receives).
- Studio commands got their own shim, `studio/factory.py`, instead of `python ../core/cli.py scaffold-tool`.
- The research note template lives once in `tools/shared/research_note.md`; per-tool overrides were dropped until a tool needs one.
- Validator fixtures live in `channels/_test/fixtures/`, outside the status folders, so workflows never pick them up.

### Why a `run.py` shim per tool
Skills call `python run.py check …` rather than a path into `core/`. The shim is a few lines:

```python
# tools/<tool>/run.py
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR.parent.parent))

from core import cli  # noqa: E402

cli.main(tool_dir=TOOL_DIR)
```

This keeps the convention "resolve paths from a known directory, never from the current directory" and gives every tool the same commands:

| Command | Replaces | Purpose |
|---|---|---|
| `python run.py info` | new | Nouns, sections, limits and channels, for the shared skills |
| `python run.py check <files> \| --channel <slug>` | `check_post.py` | Validate items against `tool.json` |
| `python run.py move finalize\|publish\|reopen <item> [...]` | `move_post.py` | Lifecycle moves |
| `python run.py topics <slug> [--status ...]` | `posted_topics.py` | Duplicate-topic check |
| `python run.py rss <slug> --days 7` | `rss_fetch.py` | RSS signals |
| `python run.py reddit <slug> --period week` | `reddit_top.py` | Reddit signals |
| `python run.py insights <slug> <csv> --out <file>` | `insights_summary.py` | Engagement summary |
| `python run.py new-channel <slug> --name "..."` | `new_page.py` | Create a channel from the tool's template |
| `python run.py export <item> --format html` | new | Copy-paste output |

Permissions in each tool's `.claude/settings.json` shrink to `Bash(python run.py *)`, plus `additionalDirectories: ["../shared"]` so the session can read the style guide and write to the research cache.

## 5. The tool manifest: `tool.json`

JSON, because the standard library parses it. It holds everything the shared skills and `core/validate.py` need to know about a tool. `core/tool.py:check_manifest` rejects unknown keys and wrong types, so typos fail loudly.

### Core keys (every tool, not in the manifest)
`channel` (must match the folder), `topic`, `created`, `sources` (http(s) URLs; never `facebook.com`, `instagram.com` or `threads.net`), `fact_check` (`pending | passed | failed`; `passed` required in `finalized/` and `published/`), and `published` (a date once in `published/`). Every tool also gets the filename rule, the template-placeholder check and the engagement-bait warnings.

### Fields

| Field | Purpose |
|---|---|
| `name`, `description` | Tool identity. `name` must match the folder. |
| `nouns` | `item`, `items`, `channel`, `channels`, `publish_verb`, `platform`: lets shared skills and messages use the tool's own words ("post", "page", "Facebook") |
| `notes_per_item` | `"one"` (one note → one item) or `"many"` (one item combines several notes, e.g. a newsletter issue) |
| `main_section` | The reader-facing section: scanned for engagement bait, matched against engagement exports |
| `frontmatter.required` | Keys required on top of the core keys |
| `frontmatter.enums` | Allowed values per key; `parent.child` for one level of nesting (`image.kind`) |
| `frontmatter.booleans` | Keys that must be `true` or `false` (`image.needs_ai_label`) |
| `sections` | `## Headings` in order, each with `required` and optional limits. `max_chars` and `max_hashtags` are errors (hard platform limits); `min_words` and `max_words` are warnings (targets). |
| `rules.image` | `none`, `optional` or `required`. Not `none` turns on the image rules (`idea` unless `kind: none`, AI-label warning); `required` also rejects `kind: none`. |
| `rules.blocked_domains` | Sources that are errors, on top of the Meta domains |
| `rules.banned_phrases` | Added to the shared engagement-bait list |
| `insights.group_by` | Frontmatter keys to group the engagement summary by |
| `insights.columns` | Extra CSV header names per field, for the platform's export |
| `export.formats`, `export.sections` | Formats `run.py export` allows (first is the default) and the sections it includes |
| `mcp` | Optional. MCP servers the tool's workflows may use: names from the root `.mcp.json`, or claude.ai connectors (`claude_ai_…`). The tool `CLAUDE.md` section "MCP servers" says how (§12) |

*Changed in build:* `rules.sources_required` was dropped (sources are always required, so every claim stays traceable); `rules.image_required` became `rules.image`; `max_count` became `max_hashtags`; `main_section`, `nouns.platform`, `frontmatter.booleans` and `insights` were added.

### Example: facebook

```json
{
  "name": "facebook",
  "description": "Facebook post drafts for one or more Facebook pages",
  "nouns": {"item": "post", "items": "posts", "channel": "page", "channels": "pages",
            "publish_verb": "post", "platform": "Facebook"},
  "notes_per_item": "one",
  "main_section": "Caption",
  "frontmatter": {
    "required": ["pillar", "item_type", "language", "image"],
    "enums": {
      "item_type": ["tip", "news", "question", "listicle", "quote", "story"],
      "image.kind": ["none", "own-photo", "stock", "ai-generated"]
    },
    "booleans": ["image.needs_ai_label"]
  },
  "sections": [
    {"name": "Caption", "required": true},
    {"name": "Hashtags", "required": true},
    {"name": "Alternatives", "required": false},
    {"name": "Reviewer notes", "required": true}
  ],
  "rules": {"image": "optional", "blocked_domains": [], "banned_phrases": []},
  "insights": {"group_by": ["pillar", "item_type"], "columns": {}},
  "export": {"formats": ["txt"], "sections": ["Caption", "Hashtags"]}
}
```

The frontmatter keys were renamed directly: `page:` → `channel:`, `post_type:` → `item_type:`, `posted:` → `published:`. *Changed in build:* the planned aliases for the old names were not needed, because the only existing page was `_test` and it had no posts.

Two checks are new compared with the old `validate_post`: the `item_type` enum (before, only the post template listed the values), and blocking `instagram.com` and `threads.net` (before, only the researcher's rules forbade them). Blocked domains now match the URL's host, so `m.facebook.com` is caught and `notfacebook.com.example.org` is not.

### Sketches for the next tools

**instagram**: visual first.
- `rules.image: "required"`. `image` gains `alt_text` and `format: single | carousel | reel-cover`.
- Sections: `Caption` (`max_chars: 2200`), `Hashtags` (`max_hashtags` set from Instagram's current limit; check it when building the tool), `Slides` (optional, one line per carousel slide), `Reviewer notes`.
- Shares research with facebook through `tools/shared/research_cache/`.

**blog**: long form, SEO.
- Frontmatter adds `target_keyword` and `slug`.
- Sections: `Title` (`max_chars: 70`), `Meta description` (`max_chars: 160`), `Body` (`min_words` / `max_words`), `Reviewer notes`.
- Claims in the body cite sources inline as `[n]`. The fact-checker already works this way.
- `export.formats: ["md", "html"]` for pasting into a CMS.

**newsletter**: tailored issues.
- `notes_per_item: "many"`: `/generate` builds one issue from several unused notes.
- Sections: `Subject` (`max_chars: 60`), `Preview text` (`max_chars: 120`), `Intro`, `Stories` (each story a `###` block with its own `[n]` citations), `Outro`, `Reviewer notes`.
- **Tailoring**: each audience segment is its own channel with its own `profile.md` (interests, reading level, language). One research run feeds several segment issues.
- `export.formats: ["html", "txt"]` for pasting into the email service.

## 6. Shared workflows

The seven skills moved from `app/.claude/skills/` to `tools/.claude/skills/` and became tool-agnostic. Each works the same way:

1. Run `python run.py info` (nouns, schema, limits) when it needs the format. The tool's `CLAUDE.md` is already loaded, because the session runs in the tool folder.
2. Read the channel's `profile.md` and `../shared/style_guide.md`.
3. Run the same steps as before, calling `python run.py …`.

| Before | Shared skill | Change |
|---|---|---|
| `/new-page` | `/new-channel` | Interview questions come from the `TODO`s in the tool's channel template |
| `/research` | `/research` | Unchanged; uses `research_cache/` across tools |
| `/generate-posts` | `/generate` | Honours `notes_per_item`; runs the tool's `writer` |
| `/rewrite-post` | `/rewrite` | Unchanged |
| `/finalize-post` | `/finalize` | Shows `run.py export` and the tool's "Publishing checklist"; keeps `disable-model-invocation: true` |
| `/mark-posted` | `/mark-published` | Moves to `published/` |
| `/import-insights` | `/import-insights` | Export steps come from the tool's "Insights export"; columns can be added in `tool.json` |

### Tool `CLAUDE.md` sections the shared skills rely on
- **Words**: the tool's nouns, so the session talks in them
- **Format notes**: platform writing rules, read by the writer and the fact-checker
- **Publishing checklist**: shown at `/finalize` approval (e.g. "Turn on the AI label when posting")
- **Insights export**: how to export engagement data; absent means `/import-insights` stops

### Customising one tool, in order of preference
1. **`tool.json`**: formats, limits and rules.
2. **Tool `CLAUDE.md`**: vocabulary, tone and the sections above.
3. **Tool agents**: the `writer` is always tool-specific. A tool may also override `researcher` or `fact-checker` by putting a same-named file in its own `.claude/agents/` (closest wins).
4. **Tool-only skills with unique names**, e.g. `/carousel-plan` for instagram. A same-named skill in the tool folder **replaces** the shared one (§3), so reuse a name only to override deliberately. `check-tool` flags it.

## 7. Building a new tool

In studio mode (Claude Code at the repo root, then `/load-studio`):

```
/new-tool blog
```

1. **Interview**: what is an item, what is a channel, the platform, which sections and limits, item types, image, research sources, export format, insights export, language(s).
2. **Scaffold**: `python studio/factory.py new-tool blog` copies `templates/tool/` to `tools/blog/` (`tool.json`, `CLAUDE.md`, `run.py`, settings, writer, item and channel templates, all with `TODO`s).
3. **Fill**: write `tool.json`, `CLAUDE.md`, `.claude/agents/writer.md`, `templates/item.md`, and a `channels/_test/` channel with one hand-written valid fixture and one invalid fixture.
4. **Check**: `/check-tool blog` runs the unit tests and `python studio/factory.py check-tool blog`: manifest valid, required files present, no `TODO` left, valid fixture passes, invalid fixture fails, an unedited template fails.
5. **Try it**: `/clear`, `/load-tool blog`, then `/new-channel`, `/research`, `/generate`.

Target: a working new tool in about 30 minutes. Most of that is the interview and the writer prompt.

### Testing rules for every change
- `core/tests/`: unit tests for the frontmatter parser, manifest checks, schema validation and limits, lifecycle moves, insights, scaffolding, export, and one `check_tool` per tool in `tools/`. Run with `python studio/factory.py test`.
- Each tool keeps a `channels/_test/` channel. A change is done when the affected workflow has been run against `_test` and the output passes `python run.py check --channel _test`.
- In a tool-mode session, `studio/CLAUDE.md` must never be loaded (`/memory` shows what is).

## 8. Working within a Pro subscription

- **Interactive first.** Every workflow is run by you in a Claude Code session. Approval gates (`/finalize`) are always interactive.
- **Usage limits are the main cost.** Pro limits are shared with claude.ai, so:
  - Launch subagents in parallel only when the batch is worth it; parallel runs use quota faster.
  - Set `model:` in agent frontmatter: a lighter model for mechanical work (formatting, structural fixes), the default for writing and fact-checking.
  - **Research once, reuse everywhere.** `tools/shared/research_cache/` sits above every tool, so one topic note can feed a FB post, an IG post and a newsletter story without searching the web again.
- **Optional unattended research**: `claude -p` works with the subscription login, so a Windows Task Scheduler job could run `claude -p "/research <slug> <topic>"` from a tool folder overnight with a restricted `--allowedTools`. Only research runs this way. Writing can wait for you, and approval always does. Not set up yet.

## 9. Migration of the Facebook app (done)

1. **Extract core.** `app/utils/common.py` was split into `core/common.py`, `core/frontmatter.py` and `core/validate.py`. The other utils moved into `core/` behind `core/cli.py` subcommands. `app/utils/tests/test_utils.py` became `core/tests/test_core.py`.
2. **Schema-driven validation.** `tools/facebook/tool.json` (§5) drives `core/validate.py`. It gives the same errors and warnings as the old `validate_post`, plus the new checks in §5.
3. **Move the tool.** `app/` → `tools/facebook/`, `facebook_pages/` → `channels/`, `posted/` → `published/`, a page's `templates/` → `formats/`, `templates/post.md` → `templates/item.md`, `templates/page/` → `templates/channel/`. Added `run.py`.
4. **Share the workflows.** The 7 skills and the `researcher` and `fact-checker` agents moved to `tools/.claude/`, renamed (§6) and made generic. `writer.md` stayed in `tools/facebook/.claude/agents/`. `app/shared/` → `tools/shared/`, with `research_note.md` beside the style guide.
5. **Studio.** The root `CLAUDE.md` moved to `studio/CLAUDE.md`, updated for the new layout. The old `claudeMdExcludes` in `app/.claude/settings.local.json` is gone. Added `/new-tool`, `/check-tool` and `templates/tool/`.
6. **Verify.** See §7, "Testing rules".

## 10. Roadmap

1. ~~**Spike**: confirm parent-folder inheritance.~~ Done 2026-10-03 (§3).
2. ~~**Core plus Facebook migration** (§9).~~ Done 2026-10-03.
3. **`/new-tool` plus the blog tool**: the first proof that the abstraction holds.
4. **Newsletter** (tests `notes_per_item: many` and segments) and **Instagram** (tests `rules.image: required` and carousels).
5. **Cross-tool repurposing**: a `/repurpose <note> <tool>…` skill that turns one note into items in several tools.
6. **Optional local dashboard**: a stdlib `http.server` page that lists items by tool, channel and status, renders previews and calls `core/lifecycle.py` on approval clicks. Still local, still single-user.

## 11. Open questions

| Question | How to settle it |
|---|---|
| ~~When a tool and `tools/.claude/` both define a skill with the same name, which wins?~~ | Settled by the spike: the tool's copy wins. |
| ~~Does `claude -p` run with a Pro login on this machine?~~ | Settled: yes (2026-10-03). Scheduling is still optional and not set up. |
| Should channels be shared across tools (one "brand" with FB + IG + newsletter outputs)? | Decide after the second tool. The shared research cache covers most of the benefit without coupling tools. |
| Do non-content tools (e.g. job-application tailoring, lead research) fit the same core? | Probably: item, channel, lifecycle and schema are not content-specific. Revisit once there are three content tools. |
| Does `export` need per-tool rendering (e.g. the blog `Title` as `<h1>`, `[n]` citations as links)? | Decide when building the blog tool. Today md/html export puts a `##` heading on every exported section. |

## 12. Root launch, modes and MCP (added 2026-10-03)

The operator no longer launches Claude Code in different folders. Every session starts at the **repo root**, and a command loads one mode:

| Command | Mode | Scope (files it may change) |
|---|---|---|
| `/load-tool <tool>` | tool | `tools/<tool>/channels/`, `tools/shared/research_cache/` |
| `/load-studio [tool]` | studio | one tool's definition (`tool.json`, `CLAUDE.md`, agents, templates, `_test`), `.mcp.json`, the README tool table |
| `/build-studio [goal]` | studio-dev | `core/`, `studio/`, `templates/`, `tools/.claude/`, `tools/shared/`, root `CLAUDE.md` and `.claude/`, `.mcp.json`, docs |
| `/start`, `/help [topic]` | any | none: they only read |

**How it works with Claude Code's loading rules** (checked against the Claude Code docs on 2026-10-03):
- A subfolder's `CLAUDE.md` and `.claude/skills/` load on demand, when Claude first reads a file there. So `/load-tool` only has to read `tools/<tool>/CLAUDE.md`; the shared workflows then appear as slash commands. `/load-studio` and `/build-studio` read `studio/CLAUDE.md` in the same way.
- Subagents are found only by walking **up** from the launch folder. The root `.claude/agents/` therefore holds **proxy agents** with the same names and tools as the real ones (`researcher`, `fact-checker`, `writer`). A proxy reads `tools/<tool>/.claude/agents/<name>.md`, or the shared one, and follows it. The calling workflow starts the prompt with `tool: <tool>`. `check-tool` and `check-studio` fail when a proxy is missing or its tools differ.
- Settings and `.mcp.json` are read only from the launch folder, so the root `.claude/settings.json` holds the permissions for every mode (`python tools/*/run.py`, `python studio/factory.py`, edits to channels and the research cache, the Meta deny list, `autoMemoryEnabled: false`).
- **Shared workflows and agents stay tool-relative** (`channels/…`, `python run.py`). `/load-tool` gives the session a path table (`channels/…` → `tools/<tool>/channels/…`), and `run.py` resolves item paths from the tool folder. A session launched inside `tools/<tool>/` still works unchanged. Studio files and root commands use repo-root paths.
- The root `CLAUDE.md` is a short, mode-neutral router: until a mode is loaded, Claude only answers questions. This replaces the earlier "no root `CLAUDE.md`" rule; `tools/CLAUDE.md` is still forbidden.
- One mode per session: `/clear` before switching. Load commands set `disable-model-invocation: true`, so only the operator switches modes.

**Command template.** `templates/command/SKILL.md` gives every command the same shape: frontmatter (`name`, `description`, `argument-hint`, `disable-model-invocation`), **Needs** (the mode), **Steps** (ending with a report and the next command) and **Rules**. `python studio/factory.py new-command <name> --in <root|studio|shared|tool>` copies it into place. `check-studio` checks every command's frontmatter, rejects leftover `TODO`s, and keeps names unique across the root, studio and shared commands.

**MCP.**
- The root `.mcp.json` holds project servers. Secrets go only in `${VAR}` references, which Claude Code expands from its own environment, not from `.env`. `core/mcp.py` rejects a literal value under a secret-looking `env` or `headers` name, and any Meta host.
- claude.ai connectors need no entry.
- A tool opts in with `tool.json` → `mcp`. Its `CLAUDE.md` section "MCP servers" says which workflow step uses each server and how, and `/load-tool` reports their status.
- `python studio/factory.py mcp` lists the servers without their secrets.
- No server may publish, schedule, post or reach a Meta property.
- Subagent frontmatter also supports `mcpServers` (by name), for a future agent that needs a server.
