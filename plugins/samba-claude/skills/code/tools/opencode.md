# Opencode via the Code Skill

Opencode is invoked through the code skill using tool name `opencode`.

> For the full CLI reference, see `agent_shims/src/agent_shims/opencode/README.md`.

## Basic Invocation

```bash
code.sh opencode <model> <cwd> <prompt>
```

## Passing Extra Flags

Use `--tool-arg` to forward additional flags. Each flag and its value must be a separate `--tool-arg`.

```bash
# Attach files for context
code.sh opencode MiniMax-M2.5 /path/to/project "review this code" \
  --tool-arg --file --tool-arg src/main.py \
  --tool-arg --file --tool-arg src/utils.py

# JSON event stream output
code.sh opencode MiniMax-M2.5 /path/to/project "analyze this" \
  --tool-arg --format --tool-arg json

# Continue a previous session
code.sh opencode MiniMax-M2.5 /path/to/project "follow up question" \
  --tool-arg --continue

# Show thinking blocks
code.sh opencode MiniMax-M2.5 /path/to/project "explain this" \
  --tool-arg --thinking
```

## Useful `--tool-arg` Options

| Flag | Purpose |
|------|---------|
| `--file <path>` | Attach a file to the message context. Repeatable. |
| `--format json` | Get newline-delimited JSON events instead of text. |
| `--thinking` | Include thinking blocks in output. |
| `--dir <path>` | Override working directory (note: `cwd` already sets this). |
| `--continue` | Continue the last session. |
| `--session <id>` | Continue a specific session. |
| `--fork` | Fork when continuing (use with `--continue` or `--session`). |
| `--title <text>` | Set a session title. |
