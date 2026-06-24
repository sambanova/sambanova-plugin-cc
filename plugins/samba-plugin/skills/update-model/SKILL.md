---
name: update-model
description: Insert or update a model in the parameters database. Use when the user asks to "update model", "add model", or "insert model" with model details.
argument-hint: <name> <context_length> <max_completion_tokens> [sampling_parameters_json]
allowed-tools: mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__update_model, WebFetch(*), WebSearch(*)
---

# Update Model

Insert or update a model entry in the parameters database.

## Arguments

The user invoked this with: $ARGUMENTS

## Instructions

This skill is a thin pointer to the plugin's MCP server, which owns the
implementation. When invoked:

1. Run `/model-info` to get the list of available models. Use the `id`,
   `context_length`, and `max_completion_tokens` fields from the output — do not
   invent or guess these values.
  - These may vary based on the usage of the model. When multiple options are available, present them to the user to choose from, noting the use-case (i.e. coding, chat, etc.). By default, use the one best suited for coding.
2. Sampling parameters (e.g. `temperature`, `topP`, etc.) are not available from `/model-info`. Look them up from the model's HuggingFace documentation or ask the user to provide them. Do not omit them without confirming with the user. Prefer to look them up and suggest them to the user if possible.
  - For some models, a more complex web search may be required to find the proper parameters.
3. Once all fields are confirmed, call the MCP tool
   `mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__update_model` with
   arguments: `name`, `context_length`, `max_completion_tokens`, and optional
   `sampling_parameters` (a JSON object).

Requires the `sambanova-plugin-cc` MCP server to be running.
