# Continue CLI — Headless Mode (`cn -p`)

> Version tested: 1.5.45

Continue's headless mode is activated with `-p` / `--print`. It runs a single prompt, prints the response, and exits — no interactive TUI.

## Basic Usage

```bash
cn -p "explain this function"
```

The prompt can also be piped via stdin:

```bash
echo "explain this function" | cn -p
```

## Key Flags

| Flag | Description |
|------|-------------|
| `-p`, `--print` | **Required for headless.** Print response and exit. |
| `--silent` | Strip `<think>` tags and excess whitespace from output. Only works with `-p`. |
| `--format json` | Output as `{"message": "..."}` JSON. Only works with `-p`. |
| `--auto` | Auto-approve all tool use (read, write, shell). Without this, tools that modify state will be skipped. |
| `--readonly` | Plan mode — only read-only tools are available. |
| `--config <path>` | Path to a configuration file (or hub slug). |

## Prompt & Rule Injection

| Flag | Description |
|------|-------------|
| `--prompt <text\|file\|slug>` | Append to the initial user message. Repeatable. Can be a string, file path, or hub slug. |
| `--rule <text\|file\|slug>` | Add a system-level rule/instruction. Repeatable. |

These compose: `--rule` sets behavioral constraints, `--prompt` adds context to the user message.

```bash
cn -p --silent \
  --rule "Always respond in bullet points" \
  --prompt context.txt \
  "summarize the changes"
```

## Tool Policy

Fine-grained control over which tools the model can use:

| Flag | Description |
|------|-------------|
| `--allow <tool>` | Always allow this tool (no confirmation). Repeatable. |
| `--ask <tool>` | Require confirmation before use. Repeatable. |
| `--exclude <tool>` | Completely block this tool. Repeatable. |

```bash
# Allow file reads, block shell commands
cn -p --auto \
  --allow builtin_read_file \
  --exclude builtin_run_terminal_command \
  "read .gitignore and summarize it"
```

## Session Management

| Flag | Description |
|------|-------------|
| `--resume` | Resume the last session (adds to existing context). |
| `--fork <sessionId>` | Fork from an existing session (new branch of conversation). |

## Output Modes

| Combo | Behavior |
|-------|----------|
| `-p` | Raw output including think tags and whitespace. |
| `-p --silent` | Clean text output, think tags stripped. |
| `-p --format json` | JSON object: `{"message": "..."}`. |
| `-p --format json --silent` | JSON with clean message content. |

## Gotchas

- `--silent` and `--format` only work with `-p`. Without `-p`, they are ignored.
- `--auto` is required for the model to use write/shell tools in headless mode. Without it, those tools are skipped silently.
