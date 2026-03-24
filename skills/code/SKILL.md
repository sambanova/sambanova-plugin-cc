---
name: code
description: Run a coding tool (e.g. continue, opencode) as a sub-agent with a given model and prompt. Use when the user asks to "run continue", "run opencode", "use a coding agent", or wants to delegate a coding task to a sub-agent tool.
argument-hint: <tool> <model> <prompt> <cwd> [files...]
allowed-tools: Bash(bash *)
---

# Code

Run a coding tool as a sub-agent, suitable for a variety of tasks such as code review, ideation, and implementation.

## Arguments

The user invoked this with: $ARGUMENTS

## Instructions

The user's request is in natural language. You must extract the following positional arguments and pass them to the script. Do NOT pass the raw user text as-is. If needed, write the prompt to a file and have the tool read that file instead.

Run: `bash ${CLAUDE_SKILL_DIR}/scripts/code.sh <tool> <model> <prompt> <cwd> [files...]` relative to this skill's directory.
DO NOT RUN THIS SCRIPT DIRECTLY OUTSIDE THE CONTEXT OF THIS SKILL.

### Arguments

| Arg | Required | Description |
|---|---|---|
| `tool` | yes | Coding tool to use: `continue` or `opencode`. Prefer `continue` by default; use `opencode` for complex tasks that benefit from iterative code+test loops. |
| `model` | yes | Model name as stored in the parameters database (use `/list-models` to check). **Important:** Use the bare model ID (e.g. `MiniMax-M2.5`), not a provider-prefixed name (e.g. ~~`sambanova/MiniMax-M2.5`~~). The provider is configured automatically. |
| `prompt` | yes | The prompt to send to the tool. Quote it as a single shell argument. |
| `cwd` | yes | Working directory for the tool. Default to the project root if not specified. |
| `files` | no | Optional list of files to grant access to. Used by `opencode` via `--file`; ignored by `continue`. |

### Common model aliases

When the user says one of these, map to the corresponding database ID:

| User says | Database model ID |
|---|---|
| `MiniMax`, `MiniMax-M2.5`, `sambanova/MiniMax-M2.5` | `MiniMax-M2.5` |
| `gpt-oss`, `gpt-oss-120b`, `sambanova/gpt-oss-120b` | `gpt-oss-120b` |

If unsure, run `/list-models` first to verify the model exists.
