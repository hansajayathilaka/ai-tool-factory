# TODO Tool title — generate mode

TODO two lines: what you produce, for which channels, and that a human reviews every item and publishes it on TODO platform **manually**. You never publish, schedule or post anything.

This tool runs on the shared framework. The workflows (slash commands) and the `researcher` and `fact-checker` agents live in `../.claude/` and serve every tool. This file covers what is specific to this tool. `tool.json` defines the item format and its limits, and `python run.py info` prints them.

Paths in this file, the workflows and the agents are relative to this tool folder. In a session launched at the repo root (after `/load-tool {{tool}}`), `channels/…` means `tools/{{tool}}/channels/…`, `../shared/` means `tools/shared/`, and `python run.py` means `python tools/{{tool}}/run.py`.

## Words
The shared workflows say *item* and *channel*. In this tool:

| Framework | This tool |
|---|---|
| item | TODO |
| channel | TODO (`channels/<slug>/`) |
| `published/`, `/mark-published` | TODO e.g. published manually on the platform |

Talk to the operator in this tool's words.

## Before any channel work
1. **Identify the channel.** Channels are the folders in `channels/`. If the operator did not name one and more than one real channel exists (ignore `_test` unless asked), ask which one.
2. **Read `channels/<slug>/profile.md` and `../shared/style_guide.md`** before writing or rewriting any item. If the profile is missing or still contains `TODO`, stop and suggest `/new-channel`, or ask the operator to finish the profile.
3. **When a channel or request is unclear, ask** instead of guessing.

## The folder is the status
An item's folder **is** its status: `drafts/` → `finalized/` → `published/`. Status changes only through `python run.py move finalize|publish|reopen`, which the workflows call. Never move item files with `mv`, `cp` or by rewriting them elsewhere. `channels/_test/fixtures/` holds validator fixtures: never fact-check, finalize or publish them.

## Workflows
| Command | Use it when |
|---|---|
| `/new-channel <name>` | Adding a channel. Interviews the operator and creates the folder and profile. |
| `/research <slug> [topic]` | Finding topics before writing. Saves notes to `research/`. |
| `/generate <slug> [n]` | Turning unused research notes into drafts. |
| `/rewrite <file> <instructions>` | Changing a draft's tone, length, angle or language. |
| `/finalize <file>` | Fact-checking a draft and, after operator approval, moving it to `finalized/`. |
| `/mark-published <file> [date]` | After the operator has published it. |
| `/import-insights <slug> <csv>` | After exporting engagement data (see "Insights export"). |

If the operator asks for something a workflow covers, follow that workflow's steps even if they did not type the slash command. `python run.py --help` lists the helper commands.

## Format notes
TODO platform-specific writing rules the writer and fact-checker must follow (structure, length, SEO, links, images).

## Publishing checklist
TODO what the operator must do when publishing by hand (shown at `/finalize` approval), e.g. "Paste `python run.py export <file> --format html` into the editor."

## Insights export
TODO how to export a per-item engagement CSV from the platform, or delete this section if there is none.

## MCP servers
TODO for each server in `tool.json` → `mcp`: which workflow step uses it and how (e.g. "/finalize: save the export to the Drive folder named in the channel profile"). Write "None." if `mcp` is empty.

## Hard rules
- **Never publish** to any platform (not through an MCP server either), never log in to it, never fetch or scrape facebook.com or other Meta properties.
- **Never create item files outside a channel folder.** Drafts go only in `channels/<slug>/drafts/`.
- **Every factual claim must trace to a source** in the item's `sources`. No source means no claim.
- **A human approves every item** before it reaches `finalized/`. Never pass `--approved` without an explicit yes from the operator in this session.
- **Do not save channel knowledge in Claude's memory.** It belongs in `profile.md`, `sources.md` or `insights/`.
- Never read or print `.env` or API keys.
