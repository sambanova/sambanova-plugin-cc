# Continue via the Code Skill

Continue is invoked through the code skill using tool name `continue`.

> For the full CLI reference, see `agent_shims/src/agent_shims/cn/README.md`.

## Basic Invocation

```bash
code.sh continue <model> <cwd> <prompt>
```

## Passing Extra Flags

Use `--tool-arg` to forward additional flags. Each `--tool-arg` takes **exactly one value**, so flags and their values must be separate entries.

**Important:** Values starting with `-` (i.e. flags like `--readonly`, `--rule`) must use the `=` syntax to avoid argparse ambiguity: `--tool-arg="--readonly"` not `--tool-arg --readonly`.

```bash
# Read-only mode (no write/shell tools)
code.sh continue MiniMax-M2.7 /path/to/project "review this code" \
  --tool-arg="--readonly"

# Add a rule
code.sh continue MiniMax-M2.7 /path/to/project "summarize changes" \
  --tool-arg="--rule" --tool-arg="Be concise"

# Restrict tools
code.sh continue MiniMax-M2.7 /path/to/project "analyze the code" \
  --tool-arg="--exclude" --tool-arg="builtin_run_terminal_command"

# Override max output tokens
code.sh continue MiniMax-M2.7 /path/to/project "write a large file" \
  --max-tokens 65536
```

## Useful `--tool-arg` Options

| Flag | Purpose |
|------|---------|
| `--readonly` | Plan mode — only read-only tools available. |
| `--rule <text>` | Add a system-level behavioral constraint. |
| `--prompt <text\|file>` | Append extra context to the user message. |
| `--allow <tool>` | Explicitly allow a tool. |
| `--exclude <tool>` | Block a tool. |
| `--format json` | Get output as `{"message": "..."}` JSON. |
| `--resume` | Resume the last session. |
| `--fork <sessionId>` | Fork from an existing session. |
