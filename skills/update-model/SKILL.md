---
name: update-model
description: Insert or update a model in the parameters database. Use when the user asks to "update model", "add model", or "insert model" with model details.
argument-hint: <name> <context_length> <max_completion_tokens> [sampling_parameters_json]
allowed-tools: [Bash(bash *)]
---

# Update Model

Insert or update a model entry in the parameters database.

## Arguments

The user invoked this with: $ARGUMENTS

## Instructions

When this skill is invoked:

1. Run `/model-info` to get the list of available models. Use the `id`, `context_length`, and `max_completion_tokens` fields from the output — do not invent or guess these values.
2. Sampling parameters (e.g. `temperature`, `topP`, etc.) are not available from `/model-info`. Look them up from the model's HuggingFace documentation or ask the user to provide them. Do not omit them without confirming with the user. Prefer to look them up and suggest them to the user if possible.
3. Once all fields are confirmed, run `bash ./scripts/update_model.sh <name> <context_length> <max_completion_tokens> [sampling_parameters_json]` relative to this skill's directory.
