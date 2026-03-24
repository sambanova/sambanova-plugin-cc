---
name: list-models
description: List all models stored in the parameters database along with their parameters. Use when the user asks to "list models", "show models in the database", or "what models are stored".
allowed-tools: [Bash(bash *)]
---

# List Models

Display all models in the parameters database with their fields.

## Instructions

When this skill is invoked, run `bash ${CLAUDE_SKILL_DIR}/scripts/list_models.sh` and display the output to the user.
