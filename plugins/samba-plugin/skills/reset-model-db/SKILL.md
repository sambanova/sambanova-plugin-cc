---
name: reset-model-db
description: Reset the model parameters database, clearing all entries. Use when the user asks to "reset the database", "clear the model database", or "wipe model parameters".
allowed-tools: mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__reset_model_db
---

# Reset Model Database

Clears all entries from the model parameters database.

## Instructions

This skill is a thin pointer to the plugin's MCP server, which owns the
implementation. When invoked:

1. Warn the user that this will permanently delete all model entries from the
   database and ask for confirmation before proceeding.
2. Once confirmed, call the MCP tool
   `mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__reset_model_db`
   (no arguments).
3. Confirm the database was reset successfully.

Requires the `sambanova-plugin-cc` MCP server to be running.
