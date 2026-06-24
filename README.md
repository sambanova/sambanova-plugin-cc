# SambaNova Plugin for Claude Code

Claude Code skills for managing SambaNova models and delegating coding tasks to a
sub-agent running on SambaNova Cloud.

## Installation

### Step 1: Add the marketplace

In Claude Code, run:

```
/plugin marketplace add <this repository link>
```

### Step 2: Install the plugin

```
/plugin install samba-plugin
```

## Prerequisites

- **Python 3.11+** with `venv` support.
- A **`SAMBANOVA_API_KEY`** (or `SAMBA_CLAUDE_API_KEY`) environment variable — required
  by `/model-info` and `/code`.
- The **[opencode](https://opencode.ai) CLI** installed and on your `PATH` (used by
  `/code`; no model configuration of your own is required).

There is **no manual setup step**. On each session start the plugin builds an isolated
virtual environment (`.env/`) and installs its `agent_shims` package into it
automatically, so the skills are ready to use.

## How it works

The plugin ships an **MCP server** (`mcp_server/server.py`, launched via
`mcp_server/bootstrap.sh` and registered in `.mcp.json`) that exposes each skill as an
MCP tool backed by the shared `agent_shims` Python package.

It maintains its own local SQLite database of model parameters
(`agent_shims/model_parameters/parameters.db`) as the **sole source of truth** — the
plugin never reads your personal opencode config. When you run `/code`, it generates an
isolated, runtime-only opencode configuration for the sub-agent, keeping it cleanly
separated from your own setup.

## Skills Overview

| Skill | Command | Description |
|---|---|---|
| [code](#code) | `/code <model> <cwd> <prompt> [--max-tokens <n>] [--session <id>]` | Delegate a coding task to a sub-agent |
| [list-models](#list-models) | `/list-models` | List all models in the local parameters database |
| [model-info](#model-info) | `/model-info` | Show all models available on the SambaNova platform |
| [update-model](#update-model) | `/update-model <name> <ctx> <max_tokens> [params_json]` | Add or update a model in the database |
| [reset-model-db](#reset-model-db) | `/reset-model-db` | Clear all entries from the model database |

## Skill Details

### code

Runs [opencode](https://opencode.ai) as a sub-agent with a specified model and prompt —
useful for delegating tasks like code review, implementation, ideation, or running
commands and summarizing the result.

```
/code <model> <cwd> <prompt> [--max-tokens <n>] [--session <id>]
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `model` | Yes | Bare model ID from the database (e.g. `MiniMax-M2.7`, not `sambanova/MiniMax-M2.7`). Use `/list-models` to see options. |
| `cwd` | Yes | Working directory for the sub-agent. Defaults to `$CLAUDE_PROJECT_DIR` when omitted; an absolute path is recommended. |
| `prompt` | Yes | The prompt to send, quoted as a single argument. |
| `--max-tokens` | No | Override the model's `max_completion_tokens` for this run. |
| `--session` | No | Resume a previous `/code` session (from a prior call) to preserve context. Resuming must use the **same `cwd`** as the original call. |

The model must already be in the local database (`/list-models` to check, `/update-model`
to add one). The sub-agent is sandboxed to `cwd`; grant access to directories outside it
only when needed.

### list-models

Lists all models currently stored in the local parameters database along with their
context length, max completion tokens, and sampling parameters.

```
/list-models
```

### model-info

Queries the SambaNova API (`https://api.sambanova.ai/v1/models`) to display the full
catalog of available models with their context length and max completion tokens.
Requires `SAMBANOVA_API_KEY` (or `SAMBA_CLAUDE_API_KEY`) to be set.

This shows what models *can* be used, as opposed to `/list-models` which shows what is
stored locally.

```
/model-info
```

### update-model

Inserts or updates a model entry in the local parameters database. Look up model details
via `/model-info` and sampling parameters from the model's documentation before writing.

```
/update-model <name> <context_length> <max_completion_tokens> [sampling_parameters_json]
```

The sampling parameters argument is a JSON string (e.g. `'{"temperature": 0.7, "top_p": 0.9}'`).

### reset-model-db

Deletes all entries from the model parameters database.

```
/reset-model-db
```

## Architecture

```
plugins/samba-plugin/
├── .mcp.json                   # registers the plugin's MCP server
├── mcp_server/
│   ├── bootstrap.sh            # ensures the venv, then launches the server
│   └── server.py               # FastMCP server exposing the skills as MCP tools
├── hooks/                      # SessionStart hook warms the venv (no manual setup)
├── skills/                     # one SKILL.md per skill (thin MCP front-ends)
│   ├── code/
│   ├── list-models/
│   ├── model-info/
│   ├── update-model/
│   └── reset-model-db/
└── agent_shims/                # shared Python package (installed into .env)
    ├── model.py                # Model dataclass (id, context_length, max_completion_tokens, sampling_parameters)
    ├── model_parameters/       # SQLite-backed model parameter storage (parameters.db)
    └── opencode/               # opencode runner + injected rules/
```

Each skill is a thin `SKILL.md` front-end: it adds the prompting discipline, while the
implementation lives in the MCP server's tools, backed by `agent_shims`.
