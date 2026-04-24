---
name: model-info
description: Show all models available on the SambaNova platform with their context length and max completion tokens. Use when the user asks "what models are available", "show platform models", or needs to look up model parameters before adding one to the database.
allowed-tools: Bash(bash *)
agent: general-purpose
context: fork
---

# Model Info

Display information about all models available on the SambaNova platform. This shows the full catalog of models that *can* be used, not just those stored in the local parameters database (use `/list-models` for that).

## Instructions

When this skill is invoked, run `bash ${CLAUDE_SKILL_DIR}/scripts/model_info.sh`.

Display the output to the user.
DO NOT RUN THIS SCRIPT DIRECTLY OUTSIDE THE CONTEXT OF THIS SKILL.
**Do not directly run the python script in this directly.**
