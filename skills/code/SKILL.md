---
name: code
description: Run a coding tool (e.g. continue) as a sub-agent with a given model and prompt. Use when the user asks to "run continue", "use a coding agent", or wants to delegate a coding task to a sub-agent tool.
argument-hint: <tool> <model> <prompt> <cwd> [files...]
allowed-tools: [Bash(bash *)]
agent: general-purpose
---

# Code

Run a coding tool as a sub-agent, suitable for a variety of tasks such as code review, ideation, and implementation.

## Arguments

The user invoked this with: $ARGUMENTS

## Instructions

When this skill is invoked, run `bash ${CLAUDE_SKILL_DIR}/scripts/code.sh $ARGUMENTS`

Arguments:
- `tool`: the coding tool to use (currently supported: `continue`)
- `model`: model name — must exist in the parameters database (see `/list-models`)
- `prompt`: the prompt to send to the tool
- `cwd`: working directory for the tool to operate in
- `files`: optional list of files to grant the tool access to (unused by `continue`, reserved for future tools)
