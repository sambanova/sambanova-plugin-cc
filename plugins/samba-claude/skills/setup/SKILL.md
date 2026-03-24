---
name: setup
description: Set up the skills environment by creating a virtual environment and installing agent_shims. Use when the user asks to "set up", "install dependencies", or "initialize the environment".
allowed-tools: Bash(bash *)
---

# Setup

Initialize the skills environment.

## Instructions

When this skill is invoked, run `bash ${CLAUDE_SKILL_DIR}/scripts/setup.sh`.
DO NOT RUN THIS SCRIPT DIRECTLY OUTSIDE THE CONTEXT OF THIS SKILL.
