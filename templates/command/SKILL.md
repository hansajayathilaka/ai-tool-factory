---
name: {{name}}
description: TODO one or two sentences - what /{{name}} does and when to use it. Claude reads this to decide when the command applies, so name the situation.
argument-hint: TODO e.g. <channel-slug> [count]; delete this line if the command takes no arguments
disable-model-invocation: TODO true if the command changes files or an item's status, so only the operator can trigger it; otherwise delete this line
---

# /{{name}}

Arguments: **$ARGUMENTS**

## Needs
TODO the mode this command runs in: `any`, `tool` (after `/load-tool`), `studio` (after `/load-studio`) or `studio-dev` (after `/build-studio`). If a different mode is active, stop and name the command that loads the right one. Commands in `tools/` always run in tool mode, and their paths are relative to the tool folder.

## Steps

1. **Check the input.** TODO what to do when an argument is missing or unknown (list the options and ask).

2. **TODO step name.** TODO one action per step. Give the exact helper command in a code block:
   ```
   python run.py <command>
   ```

3. **Report.** TODO what to show the operator, and the next command to suggest.

## Rules
- TODO the hard limits: which files this command may change, what needs explicit operator approval, what it must never do.
