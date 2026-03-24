---
name: reset-model-db
description: Reset the model parameters database, clearing all entries. Use when the user asks to "reset the database", "clear the model database", or "wipe model parameters".
allowed-tools: Bash(bash *)
---

# Reset Model Database

Clears all entries from the model parameters database.

## Instructions

When this skill is invoked:

1. Warn the user that this will permanently delete all model entries from the database and ask for confirmation before proceeding.
2. Once confirmed, run `bash ${CLAUDE_SKILL_DIR}/scripts/reset_model_db.sh`
3. Confirm the database was reset successfully.

DO NOT RUN THIS SCRIPT DIRECTLY OUTSIDE THE CONTEXT OF THIS SKILL.
