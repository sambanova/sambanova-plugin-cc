# Skills

Claude Code skills for managing SambaNova models and running coding sub-agents.

## Installation

### Step 1: Add the marketplace

In Claude Code, run:

```
/plugin marketplace add git@github.sambanovasystems.com:nathanz/samba-claude.git
```

Or manually add it to your `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "samba-claude": {
      "source": {
        "source": "git",
        "url": "git@github.sambanovasystems.com:nathanz/samba-claude.git"
      }
    }
  }
}
```

### Step 2: Install the plugin

```
/plugin install samba-claude
```

### Step 3: Initialize

Run `/setup` to create the virtual environment before using any other skill.

These skills are invoked as slash commands (e.g. `/setup`, `/code`) within Claude Code.
Each skill lives in its own directory containing a `SKILL.md` descriptor and a `scripts/`
folder with the underlying shell and Python implementations.

## Prerequisites

- Python 3 with `venv` support
- A `SAMBANOVA_API_KEY` environment variable (required by `/model-info`, `/code`, and others.)
- Run `/setup` before using any other skill
- At least one of `continue` and `opencode` installed for use with `/code`.

## Skills Overview

| Skill | Command | Description |
|---|---|---|
| [setup](#setup) | `/setup` | Initialize the virtual environment and install `agent_shims` |
| [code](#code) | `/code <tool> <model> <prompt> <cwd> [files...]` | Delegate a coding task to a sub-agent |
| [list-models](#list-models) | `/list-models` | List all models in the local parameters database |
| [model-info](#model-info) | `/model-info` | Show all models available on the SambaNova platform |
| [update-model](#update-model) | `/update-model <name> <ctx> <max_tokens> [params_json]` | Add or update a model in the database |
| [reset-model-db](#reset-model-db) | `/reset-model-db` | Clear all entries from the model database |

## Skill Details

### setup

Initializes the skills environment by creating a Python virtual environment at
`skills/.env/` and installing the `agent_shims` package in editable mode.

**Run this first** — all other skills depend on the virtual environment it creates.

```
/setup
```

### code

Runs a coding tool (`continue` or `opencode`) as a sub-agent with a specified model
and prompt. Useful for delegating tasks like code review, implementation, or ideation.

```
/code <tool> <model> <cwd> <prompt> [--max-tokens <n>] [--tool-arg <arg>...]
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `tool` | Yes | `continue` or `opencode` (see tool selection guide below) |
| `model` | Yes | Bare model ID from the database (e.g. `MiniMax-M2.5`, not `sambanova/MiniMax-M2.5`) |
| `cwd` | Yes | Working directory for the tool (defaults to project root if unspecified) |
| `prompt` | Yes | The prompt to send, quoted as a single shell argument |
| `--max-tokens` | No | Override the model's `max_completion_tokens` for this run |
| `--tool-arg` | No | Extra args passed to the underlying tool (repeatable, use `=` syntax for flags: `--tool-arg="--file"`) |

**Tool selection guide:**

| Scenario | Tool |
|---|---|
| Large code generation (1,000+ lines) | `continue` — iterates across turns, tested up to 3,700 lines |
| Code review of large files (1,500+ lines) | `continue` — reads in chunks; opencode truncates at ~1,500 lines |
| Qwen3-235B + C++ | `continue` (cleaner) or `opencode` |
| Side-effect-free output needed | `opencode` — doesn't modify filesystem |

See `skills/code/prompting/` for detailed model and tool guides.

**Common model aliases:**

| User says | Maps to |
|---|---|
| `MiniMax`, `sambanova/MiniMax-M2.5` | `MiniMax-M2.5` |
| `gpt-oss`, `sambanova/gpt-oss-120b` | `gpt-oss-120b` |

### list-models

Lists all models currently stored in the local parameters database along with their
context length, max completion tokens, and sampling parameters.

```
/list-models
```

### model-info

Queries the SambaNova API (`https://api.sambanova.ai/v1/models`) to display the full
catalog of available models with their context length and max completion tokens.
Requires `SAMBANOVA_API_KEY` to be set.

This shows what models *can* be used, as opposed to `/list-models` which shows what
is stored locally.

```
/model-info
```

### update-model

Inserts or updates a model entry in the local parameters database. Looks up model
details from `/model-info` and sampling parameters from HuggingFace documentation
before writing.

```
/update-model <name> <context_length> <max_completion_tokens> [sampling_parameters_json]
```

The sampling parameters argument is a JSON string (e.g. `'{"temperature": 0.7, "topP": 0.9}'`).

### reset-model-db

Deletes all entries from the model parameters database. Prompts for confirmation
before proceeding.

```
/reset-model-db
```

## Architecture

```
skills/
├── setup/                  # Environment initialization
├── code/                   # Sub-agent coding tool runner
├── list-models/            # Database model listing
├── model-info/             # SambaNova platform model catalog
├── update-model/           # Database model upsert
└── reset-model-db/         # Database reset

agent_shims/                # Shared Python package (installed by /setup)
├── model.py                # Model dataclass (id, context_length, max_completion_tokens, sampling_parameters)
├── model_parameters/       # SQLite-backed model parameter storage
├── cn/                     # Continue runner
└── opencode/               # Opencode runner
```

Each skill follows the same pattern:
1. `SKILL.md` — metadata and instructions for Claude Code
2. `scripts/*.sh` — shell wrapper that activates the venv and calls the Python script
3. `scripts/*.py` — implementation using `agent_shims`
