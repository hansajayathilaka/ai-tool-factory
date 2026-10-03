---
name: start
description: Start a session - show the tools, the modes and the MCP servers, then help the operator pick a mode. Use at the beginning of a session, or when the operator asks where to begin or what this project can do.
---

# /start

## Steps

1. **Already in a mode?** If a mode is active in this session (see the root `CLAUDE.md`), say which one. Say that switching needs `/clear` first. Then follow `/help` for that mode instead, and stop.

2. **Look around.** Run:
   ```
   python studio/factory.py list
   python studio/factory.py mcp
   ```

3. **Show**, briefly:
   - the tools: tool · item · channel · channels
   - the modes:

     | Command | Use it to |
     |---|---|
     | `/load-tool <tool>` | research, write and finalize items with a tool |
     | `/load-studio [tool]` | build a new tool, or change a tool's format, voice, writer or limits |
     | `/build-studio [goal]` | improve the framework: validator, lifecycle, shared workflows, commands, MCP support |
   - MCP: the configured servers, the servers each tool declares, and any problems. Say that `/mcp` shows the live connection state.

4. **Ask** what they want to do, and map the answer to one command. Example: "write posts for my page" → `/load-tool facebook`. The operator runs the command. Never start a mode yourself.

## Rules
- Change no files. `/start` only looks.
