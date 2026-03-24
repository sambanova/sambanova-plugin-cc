---
name: reset-model-db
description: Reset the model parameters database, clearing all entries. Use when the user asks to "reset the database", "clear the model database", or "wipe model parameters".
allowed-tools: "Bash"
---

# Reset Model Database

Clears all entries from the model parameters database.

## Instructions

When this skill is invoked:

1. Warn the user that this will permanently delete all model entries from the database and ask for confirmation before proceeding.
2. Once confirmed, run `bash ./scripts/reset_model_db.sh` relative to this skill's directory.
3. Report how many rows were deleted.
