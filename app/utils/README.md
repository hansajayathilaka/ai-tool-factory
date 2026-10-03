# utils

Helper scripts used by the workflows. Python 3.10+, standard library only (no `pip install`). Run them from `app/`. Every script supports `--help`.

| Script | Purpose |
|---|---|
| `new_page.py <slug> --name "Name"` | Copy `templates/page/` to `facebook_pages/<slug>/` |
| `posted_topics.py <slug> [--status ...]` | List covered topics, for duplicate checks |
| `check_post.py <files> \| --page <slug>` | Validate post files (format, sources, image rules, engagement bait) |
| `move_post.py finalize\|posted\|reopen <file>` | The only way a post changes status folder |
| `rss_fetch.py <slug> \| --url <feed>` | Recent items from the RSS feeds in `sources.md` |
| `reddit_top.py <slug> \| --sub <name>` | Top posts from the subreddits in `sources.md` |
| `insights_summary.py <slug> <csv> [--out ...]` | Summarize a Meta Business Suite CSV export |
| `common.py` | Shared code: paths, frontmatter parsing, post validation |

## Reddit API keys
Reddit blocks most unauthenticated requests. Create a "script" app at https://www.reddit.com/prefs/apps, then add these to `.env` (in `app/` or the repo root; it is gitignored):
```
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=script:ai-automation-research:1.0 (by u/yourname)
```

## Tests
```
python -m unittest discover -s utils/tests
```
