# core

The shared engine behind every tool. Python 3.10+, standard library only (no `pip install`). Every command supports `--help`.

## Tool commands
Run from the repo root as `python tools/<tool>/run.py <command>` (or `python run.py <command>` inside the tool folder). `run.py` is a short shim that calls `core.cli.main(tool_dir=<that folder>)`, so paths resolve from the tool folder wherever it runs.

| Command | Module | Purpose |
|---|---|---|
| `info` | `cli.py` | Nouns, sections, limits and channels, from `tool.json` |
| `check <files> \| --channel <slug>` | `validate.py` | Validate items against `tool.json` and the style guide |
| `move finalize\|publish\|reopen <file>` | `lifecycle.py` | The only way an item changes status folder |
| `topics <slug> [--status ...]` | `topics.py` | List covered topics, for duplicate checks |
| `rss <slug> \| --url <feed>` | `sources/rss.py` | Recent entries from the RSS feeds in `sources.md` |
| `reddit <slug> \| --sub <name>` | `sources/reddit.py` | Top posts from the subreddits in `sources.md` |
| `insights <slug> <csv> [--out ...]` | `insights.py` | Summarize an engagement CSV export |
| `new-channel <slug> --name "Name"` | `scaffold.py` | Copy `templates/channel/` to `channels/<slug>/` |
| `export <file> [--format txt\|md\|html]` | `export.py` | Copy-paste output for publishing by hand |

## Studio commands
Run from the repo root as `python studio/factory.py <command>` (`core/factory.py`):

| Command | Purpose |
|---|---|
| `new-tool <name>` | Copy `templates/tool/` to `tools/<name>/` |
| `check-tool <name\|all>` | Manifest, required files, leftover TODOs, MCP servers, root proxy agents, `_test` fixtures |
| `check-studio` | Root files, every command's frontmatter and unique names, proxy agents in sync, `.mcp.json` safety |
| `new-command <name> --in <root\|studio\|shared\|tool>` | Copy `templates/command/SKILL.md` to that place's `.claude/skills/<name>/` |
| `mcp` | Project MCP servers (never their secrets) and the servers each tool declares |
| `list` | Every tool with its nouns and channels |
| `test` | Run the unit tests in `core/tests/` |

## Other modules
- `common.py`: repo paths, status folders, slug and date helpers, `utf8_stdout`, `load_env`
- `tool.py`: `Tool` (one tool folder plus its manifest) and `check_manifest`
- `frontmatter.py`: the small YAML-subset parser, `set_field`, `sections`
- `mcp.py`: loads and checks `.mcp.json` (secrets only as `${VAR}`, no Meta hosts), and each tool's `mcp` servers

## What every item must have
`tool.json` adds to these; `validate.py` always checks them:
- frontmatter `channel` (matches the folder), `topic`, `created`, `sources` (http(s) URLs, never Meta properties), `fact_check` (`pending | passed | failed`), and `published` (a date once in `published/`)
- `fact_check: passed` in `finalized/` and `published/`
- no `<placeholder>` left from the tool's `templates/item.md`

## Reddit API keys
Reddit blocks most unauthenticated requests. Create a "script" app at https://www.reddit.com/prefs/apps, then add these to `.env` (in the tool folder or the repo root; it is gitignored):
```
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=script:ai-automation-research:1.0 (by u/yourname)
```

## Tests
From the repo root: `python studio/factory.py test`, or `python -m unittest discover -s core/tests`.
