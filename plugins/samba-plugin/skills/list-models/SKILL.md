---
name: list-models
description: List all models stored in the parameters database along with their parameters. Use when the user asks to "list models", "show models in the database", or "what models are stored".
allowed-tools: mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__list_models
---

# List Models

Display all models in the parameters database with their fields.

## Instructions

This skill is a thin pointer to the plugin's MCP server, which owns the
implementation. When invoked, call the MCP tool
`mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__list_models` (no
arguments) and display its output to the user.

Requires the `sambanova-plugin-cc` MCP server to be running.
