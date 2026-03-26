---
name: code
description: Run a powerful coding tool as a sub-agent with a given model and prompt. Use when the user asks to "run continue", "run opencode", "use a coding agent", or wants to delegate a coding task to a sub-agent tool. This is also a suitable command for code reviews and second opinions, and should be used to consult on complex tasks.
argument-hint: <tool> <model> <cwd> <prompt> [--max-tokens <n>] [--tool-arg <arg>...]
allowed-tools: Bash(bash *)
---

# Code

Run a coding tool as a sub-agent, suitable for a variety of tasks such as code review, ideation, and implementation.
This skill is particularly powerful, and can handle code reviews, run commands (i.e. git diff, git rebase, etc.), and other tasks by itself internally.

## Instructions

The user's request is in natural language. You must extract the following positional arguments and pass them to the script. Do NOT pass the raw user text as-is. If needed, write the prompt to a file and have the tool read that file instead.
Prefer passing the file in as an input with instructions to read said file over using another tool such as `cat` to inject it into the command line.

Run: `bash ${CLAUDE_SKILL_DIR}/scripts/code.sh <tool> <model> <cwd> <prompt> [--tool-arg <arg>...]`.
DO NOT RUN THIS SCRIPT DIRECTLY OUTSIDE THE CONTEXT OF THIS SKILL.

### Arguments

| Arg | Required | Description |
|---|---|---|
| `tool` | yes | Coding tool to use. See the section below under "Available Tools and Documentation" for more information. |
| `model` | yes | Model name as stored in the parameters database (use `/list-models` to check). **Important:** Use the bare model ID (e.g. `MiniMax-M2.5`), not a provider-prefixed name (e.g. ~~`sambanova/MiniMax-M2.5`~~). The provider is configured automatically. |
| `cwd` | yes | Working directory for the tool. Default to the project root if not specified. |
| `prompt` | yes | The prompt to send to the tool. Quote it as a single shell argument. **If the prompt contains shell-sensitive characters** (e.g. `$`, `<`, `>`, `(`, `)`, `` ` ``, `!`, `{`, `}`, `|`, `&`, `;`, `*`, `?`, `\`), write the prompt to a temporary file (e.g. `/tmp/prompt_XXXXX.md`) and pass the full path to that file as the prompt instead, with instructions for the tool to read it (e.g. `"Read the prompt from /tmp/prompt_abc.md and follow its instructions."`). This avoids shell expansion and quoting issues. |
| `--tool-arg` | no | Extra arguments passed through verbatim to the underlying tool. Repeatable — each `--tool-arg` takes exactly one value. See the **Passing `--tool-arg`** section below for syntax details. |
| `--max-tokens` | no | Override the model's `max_completion_tokens` for this run. The database value is only a default; the actual limit is the model's context length. Use this to request more output tokens when needed. |

### Passing `--tool-arg`

`--tool-arg` uses argparse `action="append"`, so each occurrence takes **exactly one value**. To pass a flag and its value to the underlying tool, use two separate `--tool-arg` entries.

**Caveat:** Values that start with `-` (i.e. flags) are ambiguous to argparse. Use the `=` syntax (`--tool-arg="--flag"`) to avoid parsing errors.

```bash
# Basic usage with continue
code.sh continue MiniMax-M2.5 /project "prompt"

# Override max tokens to 64k
code.sh continue MiniMax-M2.5 /project "prompt" --max-tokens 65536

# Pass extra arguments through to continue
code.sh continue MiniMax-M2.5 /project "prompt" \
  --max-tokens 16000 \
  --tool-arg="--thinking"

# Attach a file to opencode (note: = syntax for the -f flag)
code.sh opencode MiniMax-M2.5 /project "prompt" \
  --tool-arg="-f" --tool-arg="/path/to/file.py"

# Multiple files with opencode
code.sh opencode MiniMax-M2.5 /project "prompt" \
  --tool-arg="-f" --tool-arg="src/main.py" \
  --tool-arg="-f" --tool-arg="src/utils.py"
```

### Common model aliases

When the user says one of these, map to the corresponding database ID:

| User says | Database model ID |
|---|---|
| `MiniMax`, `MiniMax-M2.5`, `sambanova/MiniMax-M2.5` | `MiniMax-M2.5` |
| `gpt-oss`, `gpt-oss-120b`, `sambanova/gpt-oss-120b` | `gpt-oss-120b` |

If unsure, run `/list-models` first to verify the model exists.

### Available Tools and Documentation:
- [Continue](tools/continue.md)
- [Opencode](tools/opencode.md)
