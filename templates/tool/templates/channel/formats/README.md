# Formats — {{channel_name}}

One file per item type that works for this channel, named after the `item_type` value (e.g. `how-to.md`). `/new-channel` creates them, and the writer follows them.

Each format file describes:
- **Structure**: the parts of the item in order (e.g. hook → body → call to action) and how long each part is
- **Length**: target characters or words, within the limits in `tool.json`
- **Example**: one short example in the channel's voice (fictional, no real facts)
- **Notes**: anything that worked or flopped (update after `/import-insights`)
