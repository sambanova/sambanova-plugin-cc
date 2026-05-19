# Opencode — Headless Mode (`opencode run`)

> Version tested: 1.3.0

Opencode's headless mode is the `run` subcommand. It sends a single message, prints the response, and exits.

## Basic Usage

```bash
opencode run "explain this function"
```

The prompt can also be piped via stdin:

```bash
echo "explain this function" | opencode run
```

**Important:** The prompt (positional argument) must come immediately after `run`. Flags like `--file` go after the prompt, not before — otherwise opencode interprets them as positional args and errors out.

```bash
# Correct
opencode run "review this" --file src/main.py

# Wrong — "review this" is parsed as a file path
opencode run --file src/main.py "review this"
```

## Key Flags

| Flag | Description |
|------|-------------|
| `--format default` | Formatted text output (default). Includes `<think>` blocks. |
| `--format json` | Raw JSON event stream (one JSON object per line). Events include `step_start`, `text`, `tool_call`, `step_finish`. |
| `--thinking` | Show thinking blocks in default format output. Off by default. |
| `-m`, `--model <provider/model>` | Override the model (e.g. `sambanova/MiniMax-M2.7`). |
| `--dir <path>` | Working directory for the session. |
| `--agent <name>` | Use a named agent definition. |

## File Attachment

```bash
opencode run "review this code" --file src/main.py --file src/utils.py
```

`-f` / `--file` attaches files to the message context. The model sees their contents. Multiple `--file` flags are supported.

## Session Management

| Flag | Description |
|------|-------------|
| `-c`, `--continue` | Continue the last session. |
| `-s`, `--session <id>` | Continue a specific session by ID. |
| `--fork` | Fork the session when continuing (new branch, use with `-c` or `-s`). |
| `--title <text>` | Set a title for the session (defaults to truncated prompt). |
| `--share` | Share the session after completion. |

## Output Formats

### Default (`--format default`)

Plain text with optional `<think>` blocks:

```
<think>The user wants...</think>

Hello! Here's my answer.
```

Use `--thinking` to include the thinking blocks; without it, they're still present in the raw output but visually separated.

### JSON (`--format json`)

Newline-delimited JSON events:

```json
{"type":"step_start","timestamp":...,"sessionID":"...","part":{...}}
{"type":"text","timestamp":...,"sessionID":"...","part":{"type":"text","text":"..."}}
{"type":"step_finish","timestamp":...,"sessionID":"...","part":{"reason":"stop","cost":0,"tokens":{...}}}
```

The `step_finish` event includes token usage and cost information.

## Configuration

Opencode reads its configuration from a JSON file. The path is set via the `OPENCODE_CONFIG` environment variable:

```bash
OPENCODE_CONFIG=/path/to/config.json opencode run "hello"
```

The config file specifies the provider, model, API key, and other settings.

## Gotchas

- **Prompt position matters.** The message must be the first positional arg after `run`. Flags go after.
- **Think tags in output.** Default format includes `<think>` blocks in the text. If parsing output programmatically, either use `--format json` or strip think tags yourself.
- **No `--silent` flag.** Unlike Continue, opencode has no built-in silent mode. Think tags are always present in default output.
- **Config via env var.** There's no `--config` CLI flag — configuration is only via `OPENCODE_CONFIG`.
