# AI Automation Framework — architecture

Status: **proposal**. Nothing in this document is built yet. The current Facebook post generator in `app/` is described in [README.md](../README.md).

## 1. Vision

Turn the Facebook post generator into a **personal tool factory**: a small framework for quickly building AI automation tools that run locally in Claude Code. Examples:

- Facebook post generator (exists today)
- Instagram post generator
- Blog post generator
- Tailored newsletter

Every tool follows the same pattern, already proven by the Facebook app:

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
| Headless `claude -p "/skill …"` | Unclear; docs suggest an API key may be needed | Optional extra, verify first (see §10) |

## 2. Core concepts

The Facebook app's terms generalise as follows.

| Facebook app today | Framework term | Meaning | Examples |
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
- A file's folder is its status. Status changes only through the lifecycle script, never a raw `mv`.
- Every factual claim traces to a source in the item's `sources`.
- A human explicitly approves every item before it reaches `finalized/`.
- Channel knowledge lives in channel files (`profile.md`, `insights/`), never in Claude's memory.

## 3. How Claude Code makes sharing possible

Three documented Claude Code behaviours decide the folder layout:

1. **Skills and subagents are inherited from parent folders.** Claude Code loads `.claude/skills/` and `.claude/agents/` from the launch folder and every parent folder up to the repo root. For subagents, the definition closest to the launch folder wins.
   → Shared workflows and agents live **once** in `tools/.claude/`. Every tool in `tools/<name>/` gets them automatically. A tool can override a shared agent by defining one with the same name.
2. **`CLAUDE.md` is also inherited from parent folders.**
   → There must be **no `CLAUDE.md` at the repo root** or in `tools/`, or it leaks into every tool session. Build-mode instructions move to a sibling folder, `studio/`, which is never a parent of a tool. This replaces today's machine-specific `claudeMdExcludes` workaround with isolation built into the folder layout.
3. **Skills can declare `disable-model-invocation`, `argument-hint`, `allowed-tools` and `model`**, and can read supporting files in their own folder.
   → Shared skills stay small and read tool-specific details from the tool's `tool.json` and `CLAUDE.md`.

## 4. Folder layout

```
ai-automation/
├── README.md                        # framework overview (NO CLAUDE.md at the root)
├── docs/
│   └── framework-architecture.md    # this file
│
├── core/                            # stdlib Python engine shared by all tools
│   ├── paths.py                     # TOOL_DIR / CHANNELS_DIR resolution
│   ├── frontmatter.py               # parser, set_field, sections   (from common.py)
│   ├── validate.py                  # schema-driven item checks     (from common.py + check_post.py)
│   ├── lifecycle.py                 # finalize / publish / reopen   (from move_post.py)
│   ├── topics.py                    # covered-topic listing         (from posted_topics.py)
│   ├── insights.py                  # engagement CSV summary        (from insights_summary.py)
│   ├── sources/rss.py, reddit.py    # signal fetchers               (from rss_fetch.py, reddit_top.py)
│   ├── scaffold.py                  # new tool / new channel        (from new_page.py)
│   ├── export.py                    # item → md / html / txt for copy-paste publishing
│   ├── cli.py                       # one argparse entry point with subcommands
│   └── tests/
│
├── templates/
│   └── tool/                        # skeleton copied by /new-tool
│
├── studio/                          # BUILD MODE: run `claude` here
│   ├── CLAUDE.md                    # how to develop core/ and tools/ (today's root CLAUDE.md)
│   └── .claude/
│       ├── settings.json            # additionalDirectories: ["../core", "../tools", "../templates"]
│       └── skills/
│           ├── new-tool/SKILL.md    # interview → scaffold → fill → check
│           └── check-tool/SKILL.md  # unit tests + validate a tool's _test channel
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
    │   └── research_cache/          # notes reusable across channels AND tools
    │
    └── <tool>/                      # facebook, instagram, blog, newsletter, ...
        ├── CLAUDE.md                # tool vocabulary, rules, format notes
        ├── tool.json                # manifest + item schema (§5)
        ├── run.py                   # shim: python run.py <cmd> → core/cli.py with TOOL_DIR = here
        ├── .claude/
        │   ├── settings.json        # autoMemoryEnabled: false, permissions
        │   └── agents/writer.md     # format-specific writer
        ├── templates/
        │   ├── item.md              # item file template
        │   ├── note.md              # research note template (optional override)
        │   └── channel/             # channel skeleton (profile.md, sources.md, formats/)
        └── channels/
            ├── _test/               # fixture channel used by /check-tool
            └── <slug>/
                ├── profile.md   sources.md   formats/
                ├── research/
                ├── drafts/   finalized/   published/
                └── insights/
```

### Why a `run.py` shim per tool
Skills call `python run.py check …` rather than a path into `core/`. The shim is a few lines:

```python
# tools/<tool>/run.py
import sys
from pathlib import Path
TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR.parent.parent / "core"))
import cli
cli.main(tool_dir=TOOL_DIR)
```

This keeps today's convention ("resolve paths from a known directory, never from the current directory") and gives every tool the same commands:

| Command | Replaces | Purpose |
|---|---|---|
| `python run.py check <files> \| --channel <slug>` | `check_post.py` | Validate items against `tool.json` |
| `python run.py move finalize\|publish\|reopen <item> [...]` | `move_post.py` | Lifecycle moves |
| `python run.py topics <slug> [--status ...]` | `posted_topics.py` | Duplicate-topic check |
| `python run.py rss <slug> --days 7` | `rss_fetch.py` | RSS signals |
| `python run.py reddit <slug> --period week` | `reddit_top.py` | Reddit signals |
| `python run.py insights <slug> <csv> --out <file>` | `insights_summary.py` | Engagement summary |
| `python run.py new-channel <slug> --name "..."` | `new_page.py` | Create a channel from the tool's template |
| `python run.py export <item> --format html` | new | Copy-paste output |

Permissions in each tool's `.claude/settings.json` shrink to `Bash(python run.py *)`.

## 5. The tool manifest: `tool.json`

JSON, because the standard library parses it. It holds everything the shared skills and `core/validate.py` need to know about a tool.

### Fields

| Field | Purpose |
|---|---|
| `name`, `description` | Tool identity |
| `nouns` | `item`, `items`, `channel`, `channels`, `publish_verb`: lets shared skills talk in the tool's own words ("post", "page", "posted") |
| `notes_per_item` | `"one"` (one note → one item) or `"many"` (one item combines several notes, e.g. a newsletter issue) |
| `frontmatter.required` | Required keys (today's `REQUIRED_POST_KEYS`) |
| `frontmatter.enums` | Allowed values per key (today's `IMAGE_KINDS`, `FACT_CHECK_VALUES`, plus `item_type`) |
| `sections` | Required and optional `## Headings`, each with optional `max_chars`, `min_words`, `max_words`, `max_count` |
| `rules.sources_required` | Every item must list sources |
| `rules.image_required` | `image.kind` may not be `none` |
| `rules.blocked_domains` | Sources that are errors (e.g. `facebook.com`) |
| `rules.banned_phrases` | Added to the shared engagement-bait list |
| `export` | Formats supported by `run.py export` |

### Example: facebook (today's format, unchanged)

```json
{
  "name": "facebook",
  "description": "Facebook post drafts for one or more pages",
  "nouns": {"item": "post", "items": "posts", "channel": "page", "channels": "pages",
            "publish_verb": "post"},
  "notes_per_item": "one",
  "frontmatter": {
    "required": ["channel", "topic", "pillar", "item_type", "language",
                 "created", "sources", "image", "fact_check"],
    "enums": {
      "item_type": ["tip", "news", "question", "listicle", "quote", "story"],
      "image.kind": ["none", "own-photo", "stock", "ai-generated"],
      "fact_check": ["pending", "passed", "failed"]
    }
  },
  "sections": [
    {"name": "Caption", "required": true},
    {"name": "Hashtags", "required": true},
    {"name": "Alternatives", "required": false},
    {"name": "Reviewer notes", "required": true}
  ],
  "rules": {
    "sources_required": true,
    "image_required": false,
    "blocked_domains": ["facebook.com", "instagram.com"],
    "banned_phrases": []
  },
  "export": ["txt"]
}
```

`page:` becomes `channel:` and `post_type:` becomes `item_type:` in the frontmatter. During migration, `core/validate.py` accepts the old names as aliases so existing files stay valid.

### Sketches for the next tools

**instagram**: visual first.
- `rules.image_required: true`. `image` gains `alt_text` and `format: single | carousel | reel-cover`.
- Sections: `Caption` (`max_chars: 2200`), `Hashtags` (`max_count` set from Instagram's current limit; check it when building the tool), `Slides` (optional, one line per carousel slide), `Reviewer notes`.
- Shares research with facebook through `tools/shared/research_cache/`.

**blog**: long form, SEO.
- Frontmatter adds `target_keyword` and `slug`.
- Sections: `Title` (`max_chars: 70`), `Meta description` (`max_chars: 160`), `Body` (`min_words` / `max_words` from the channel profile), `Reviewer notes`.
- Claims in the body cite sources inline as `[n]`. The fact-checker already works this way.
- `export: ["md", "html"]` for pasting into a CMS.

**newsletter**: tailored issues.
- `notes_per_item: "many"`: `/generate` builds one issue from several unused notes.
- Sections: `Subject` (`max_chars: 60`), `Preview text` (`max_chars: 120`), `Intro`, `Stories` (each story a `###` block with its own `[n]` citations), `Outro`, `Reviewer notes`.
- **Tailoring**: each audience segment is its own channel with its own `profile.md` (interests, reading level, language). One research run feeds several segment issues.
- `export: ["html", "txt"]` for pasting into the email service.

## 6. Shared workflows

The seven skills move from `app/.claude/skills/` to `tools/.claude/skills/` and become tool-agnostic. Each starts the same way:

1. Read the tool's `tool.json` (nouns, schema, rules) and the tool's `CLAUDE.md`.
2. Read the channel's `profile.md` and `tools/shared/style_guide.md`.
3. Run the same steps as today, calling `python run.py …`.

| Today | Shared skill | Change |
|---|---|---|
| `/new-page` | `/new-channel` | Interview questions come from the tool's channel template |
| `/research` | `/research` | Unchanged; uses `research_cache/` across tools |
| `/generate-posts` | `/generate` | Honours `notes_per_item`; runs the tool's `writer` |
| `/rewrite-post` | `/rewrite` | Unchanged |
| `/finalize-post` | `/finalize` | Unchanged; keeps `disable-model-invocation: true` |
| `/mark-posted` | `/mark-published` | Moves to `published/` |
| `/import-insights` | `/import-insights` | CSV column mapping can be overridden in `tool.json` |

### Customising one tool, in order of preference
1. **`tool.json`**: formats, limits and rules.
2. **Tool `CLAUDE.md`**: vocabulary, tone and workflow notes the shared skills will read.
3. **Tool agents**: the `writer` is always tool-specific. A tool may also override `researcher` or `fact-checker` by putting a same-named file in its own `.claude/agents/` (closest wins).
4. **Tool-only skills with unique names**, e.g. `/carousel-plan` for instagram. Don't reuse a shared skill's name; the precedence for same-named skills is not documented (see §10).

## 7. Building a new tool

In build mode (`cd studio && claude`):

```
/new-tool blog
```

1. **Interview**: what is an item, what is a channel, which sections and limits, which item types, research sources, export format, language(s).
2. **Scaffold**: `python ../core/cli.py scaffold-tool blog` copies `templates/tool/` to `tools/blog/` (`run.py`, `settings.json`, empty `channels/`).
3. **Fill**: write `tool.json`, `CLAUDE.md`, `.claude/agents/writer.md`, `templates/item.md`, and a `channels/_test/` channel with one hand-written valid item and one invalid item.
4. **Check**: `/check-tool blog` runs the unit tests and `python run.py check --channel _test` (valid passes, invalid fails).
5. **Try it**: `cd tools/blog && claude`, then `/new-channel`, `/research`, `/generate`.

Target: a working new tool in about 30 minutes. Most of that is the interview and the writer prompt.

### Testing rules for every change
- `core/tests/`: unit tests for the frontmatter parser, schema validation (one test per tool manifest), lifecycle moves and topics. Run with `python -m unittest discover -s core/tests`.
- Each tool keeps a `channels/_test/` fixture. A change is done when the affected workflow has been run against `_test` and the output passes `python run.py check --channel _test`.
- In a tool session, `/memory` must list only that tool's `CLAUDE.md`, never `studio/CLAUDE.md`.

## 8. Working within a Pro subscription

- **Interactive first.** Every workflow is run by you in a Claude Code session. Approval gates (`/finalize`) are always interactive.
- **Usage limits are the main cost.** Pro limits are shared with claude.ai, so:
  - Launch subagents in parallel only when the batch is worth it; parallel runs use quota faster.
  - Set `model:` in agent frontmatter: a lighter model for mechanical work (formatting, structural fixes), the default for writing and fact-checking.
  - **Research once, reuse everywhere.** `tools/shared/research_cache/` sits above every tool, so one topic note can feed a FB post, an IG post and a newsletter story without searching the web again.
- **Optional unattended research** (after verifying §10): a Windows Task Scheduler job runs `claude -p "/research <slug>"` from a tool folder overnight with a restricted `--allowedTools`. Only research runs this way. Writing can wait for you, and approval always does.

## 9. Migration of the Facebook app

Goal: same behaviour, new layout. Do it in this order, with tests passing after each step.

1. **Extract core.** Split `app/utils/common.py` into `core/paths.py`, `core/frontmatter.py` (`split_frontmatter`, `parse_frontmatter`, `set_field`, `sections`, `read_post`) and `core/validate.py`. Move the other utils into `core/` behind `core/cli.py` subcommands. Port `app/utils/tests/test_utils.py` to `core/tests/`.
2. **Schema-driven validation.** Write `tools/facebook/tool.json` (§5). Make `core/validate.py` read it and produce **the same errors and warnings** as today's `validate_post`. Add aliases `page → channel` and `post_type → item_type`.
3. **Move the tool.** `app/` → `tools/facebook/`, `facebook_pages/` → `channels/`, `posted/` → `published/`. `core/lifecycle.py` accepts `posted/` during the transition. Add `run.py`.
4. **Share the workflows.** Move the 7 skills and the `researcher` and `fact-checker` agents to `tools/.claude/`, renamed (§6) and made generic. Keep `writer.md` in `tools/facebook/.claude/agents/`. Move `app/shared/` → `tools/shared/`.
5. **Studio.** Move the root `CLAUDE.md` → `studio/CLAUDE.md`, updated for the new layout. Delete `claudeMdExcludes` from the old `app/.claude/settings.local.json`. Add `/new-tool` and `/check-tool`.
6. **Verify.** In `tools/facebook/`, run `/research _test` → `/generate _test 1` → `/finalize`. Check that `/memory` lists only `tools/facebook/CLAUDE.md`, and that the output passes `python run.py check --channel _test`.

## 10. Roadmap

1. **Spike**: confirm parent-folder inheritance with a throwaway `tools/.claude/skills/hello/` and `tools/demo/`.
2. **Core plus Facebook migration** (§9).
3. **`/new-tool` plus the blog tool**: the first proof that the abstraction holds.
4. **Newsletter** (tests `notes_per_item: many` and segments) and **Instagram** (tests `image_required` and carousels).
5. **Cross-tool repurposing**: a `/repurpose <note> <tool>…` skill that turns one note into items in several tools.
6. **Optional local dashboard**: a stdlib `http.server` page that lists items by tool, channel and status, renders previews and calls `core/lifecycle.py` on approval clicks. Still local, still single-user.

## 11. Open questions

| Question | How to settle it |
|---|---|
| When a tool and `tools/.claude/` both define a skill with the same name, which wins? | The spike in §10 step 1. Until then, use unique names. |
| Does `claude -p` run with a Pro login on this machine? | Try `claude -p "/research _test"` in `tools/facebook/`. If it fails, unattended runs stay out of scope. |
| Should channels be shared across tools (one "brand" with FB + IG + newsletter outputs)? | Decide after the second tool. The shared research cache covers most of the benefit without coupling tools. |
| Do non-content tools (e.g. job-application tailoring, lead research) fit the same core? | Probably: item, channel, lifecycle and schema are not content-specific. Revisit once there are three content tools. |
