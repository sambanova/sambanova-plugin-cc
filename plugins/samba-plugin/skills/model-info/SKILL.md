---
name: model-info
description: Show all models available on the SambaNova platform with their context length and max completion tokens. Use when the user asks "what models are available", "show platform models", or needs to look up model parameters before adding one to the database.
allowed-tools: mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__model_info
---

# Model Info

Display information about all models available on the SambaNova platform. This shows the full catalog of models that *can* be used, not just those stored in the local parameters database (use `/list-models` for that).

## Instructions

This skill is a thin pointer to the plugin's MCP server, which owns the
implementation. When invoked, call the MCP tool
`mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__model_info` (no arguments)
and display its output to the user.

Requires the `sambanova-plugin-cc` MCP server to be running, with
`SAMBA_CLAUDE_API_KEY` or `SAMBANOVA_API_KEY` set in the environment the server
inherits.
