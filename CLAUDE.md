# AI Automation Framework — root session

Claude Code is launched **here, at the repo root**, for all work. Nothing is loaded until the operator picks a **mode** with a command. This file only routes. Each mode's own rules come from its command.

| Command | Mode | For |
|---|---|---|
| `/start` | none | First command of a session: shows the tools, the modes and the MCP servers, then helps pick a mode |
| `/help [topic]` | any | The commands for the current mode, or help on one command |
| `/load-tool <tool>` | **tool** | Using a tool: research, write and finalize items for its channels (e.g. `/load-tool facebook`) |
| `/load-studio` | **studio** | Building a new tool or updating an existing one in `tools/<tool>/` |
| `/build-studio` | **studio-dev** | Improving the studio itself: `core/`, `studio/`, `templates/`, shared workflows, root commands |

## Rules for every session
- **The active mode is the last `/load-*` or `/build-studio` command run in this session.** Before that, answer questions and suggest `/start`, but do not create, edit or move files.
- **One mode per session.** To switch, tell the operator to run `/clear` and then the new command. If they switch without clearing, the new mode's scope replaces the old one completely.
- **Stay inside the mode's scope.** Each mode command lists the files it may change. If a request needs a file outside that scope, stop and name the mode that owns it. Do not make the change.
- If you are unsure which mode is active (for example after `/compact`), ask. Do not guess.
- Nothing in this repo publishes to a platform, schedules posts or scrapes Meta properties (facebook.com, instagram.com, threads.net). This holds for every MCP server too.
- Never read or print `.env` files or API keys. MCP secrets come from environment variables (`${VAR}` in `.mcp.json`).
- Do not save project, tool or channel knowledge in Claude's memory. It belongs in the repo's files.

The overview is in [README.md](README.md) and the design is in [docs/framework-architecture.md](docs/framework-architecture.md).
