# AI Automation — build mode

This is the **build-mode** instructions file. You are helping a developer build and improve the Facebook post generator. The full design is in [README.md](README.md). Read it before making structural changes.

## What the project is
A Claude Code–driven content tool. An operator launches Claude Code from `app/`, and the agent researches topics and writes Facebook post drafts for several pages. A human reviews every post and publishes it manually. Nothing in this repo posts to Facebook or scrapes it.

## Two modes, kept apart
| | Build mode (you, now) | Generate mode |
|---|---|---|
| Launch folder | repo root `ai-automation/` | `app/` |
| Instructions | this file | `app/CLAUDE.md` |

Isolation rules. Do not break these:
1. **No skills or subagents in the root `.claude/` folder.** Everything the app uses lives in `app/.claude/`. Anything placed at the root would leak into generate-mode sessions.
2. `app/.claude/settings.local.json` excludes this file via `claudeMdExcludes` (absolute path, machine-specific, never committed). If the repo moves, update that path.
3. `app/.claude/settings.json` sets `"autoMemoryEnabled": false`. Page knowledge belongs in page files (`profile.md`, `insights/`), not Claude's memory.

When you open files under `app/`, Claude Code will also load `app/CLAUDE.md`. That is intended: read it to understand how the app behaves, but follow *this* file for how to work.

## Where things live
- `app/.claude/skills/<name>/SKILL.md`: workflows the operator runs as slash commands (`/new-page`, `/research`, `/generate-posts`, `/rewrite-post`, `/finalize-post`, `/mark-posted`, `/import-insights`)
- `app/.claude/agents/*.md`: subagents (`researcher`, `writer`, `fact-checker`)
- `app/shared/style_guide.md`: writing and safety rules for every page
- `app/templates/`: page skeleton (`page/`), `post.md`, `research_note.md`
- `app/utils/`: helper scripts
- `app/facebook_pages/_test/`: test page used to verify changes

## Writing skills and subagents
- Skills: YAML frontmatter with `name`, `description` and `argument-hint`. Use `$ARGUMENTS` for the operator's input. Set `disable-model-invocation: true` on workflows with side effects that only the operator should trigger (moving posts between status folders).
- Subagents: frontmatter with `name`, `description`, `tools` and `model`. Give each one the fewest tools that work. `researcher` and `fact-checker` must stay read-only: no `Write`, `Edit` or `Bash`.
- Skills give steps, not essays. Any file operation that changes a post's status goes through `utils/move_post.py`, never a raw `mv`.
- Keep the post file format in `app/templates/post.md`, the README's "Post file format" section, and `utils/common.py` (`REQUIRED_POST_KEYS`, validation) in sync.

## `utils/` conventions
- Python 3.10+, **standard library only**, so operators need no `pip install`. If a dependency ever becomes unavoidable, add `app/utils/requirements.txt` and document it here.
- One script per task, runnable as `python utils/<script>.py ...` from `app/`. Every script has `--help` via `argparse`.
- Shared code goes in `utils/common.py`. Resolve paths from `common.APP_DIR`, never from the current directory.
- Call `common.utf8_stdout()` first: pages may be in Sinhala or Tamil, and the Windows console defaults to a legacy code page.
- Secrets (e.g. `REDDIT_CLIENT_ID`) come from environment variables or a gitignored `.env` file, loaded with `common.load_env()`.
- Unit tests live in `app/utils/tests/`. Run them from `app/` with `python -m unittest discover -s utils/tests`.

## Testing a change
A change is not done until:
1. The unit tests pass: `cd app && python -m unittest discover -s utils/tests`
2. You have run the affected workflow in **generate mode** (launch Claude Code from `app/`) against `facebook_pages/_test/`, and the output files pass `python utils/check_post.py --page _test`.
3. In that session, `/memory` does not list the root `CLAUDE.md`.

Clean up test drafts afterwards unless they are intentional fixtures.
