---
name: code
description: Run a powerful coding tool as a sub-agent with a given model and prompt. This skill should be used whenever tasks need to be run (e.g. build-and-test), code reviews and edits, second opinions are needed, or files need to be read and summarized.
argument-hint: <tool> <model> <cwd> <prompt> [--max-tokens <n>] [--tool-arg <arg>...]
allowed-tools: Bash(bash *), Write(/tmp/samba-claude/**)
context: fork
---

# Code

Run a coding tool as a sub-agent, suitable for a variety of tasks such as code review, ideation, and implementation.
This skill is powerful, and can handle code reviews, run commands (i.e. git diff, git rebase, etc.), and other tasks by itself internally.

## Instructions

The user's request is in natural language. You must extract the following positional arguments and pass them to the script. Do NOT pass the raw user text as-is. If needed, write the prompt to a file and have the tool read that file instead.

Run: `bash ${CLAUDE_SKILL_DIR}/scripts/code.sh <tool> <model> <cwd> <prompt> [--tool-arg <arg>...]`.

**Always run the Bash call with `run_in_background: true`.**

### Arguments

| Arg | Required | Description |
|---|---|---|
| `tool` | yes | Coding tool to use. See the section below under "Available Tools and Documentation" for more information. |
| `model` | yes | Model name as stored in the parameters database (use `/list-models` to check). **Important:** Use the bare model ID (e.g. `MiniMax-M2.5`), not a provider-prefixed name (e.g. ~~`sambanova/MiniMax-M2.5`~~). The provider is configured automatically. |
| `cwd` | yes | Working directory for the tool. Default to the project root if not specified. |
| `prompt` | yes | The prompt to send to the tool. Quote it as a single shell argument. **If the prompt contains shell-sensitive characters** (e.g. `$`, `<`, `>`, `(`, `)`, `` ` ``, `!`, `{`, `}`, `|`, `&`, `;`, `*`, `?`, `\`), write the prompt to a temporary file (e.g. `/tmp/samba-claude/prompts/prompt_XXXXX.md`) and pass the full path to that file as the prompt instead, with instructions for the tool to read it (e.g. `"Read the prompt from /tmp/samba-claude/prompts/prompt_XXXXX.md and follow its instructions."`). This avoids shell expansion and quoting issues. |
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

# Prompting Rules

## Progress tracking
Include instructions in the prompt telling the sub-agent to write progress updates to a file, letting user check on progress. **Do not poll for completion.**

When constructing the prompt, **always** append something like:

> As you work, write periodic progress updates to `/tmp/samba-claude/progress/progress_<unique_id>.md`. Include what phase you are on, what you have completed, and what remains.
> Write to this file when starting the task to indicate that you have started, and update it periodically even if forward progress is not being made.
> Additionally, update this file whenever encountering an unexpected or noteworthy error or update.

## Providing Context:
The coding tool is given the project directory and the prompt.
It does not have access to the terminal history or the broader system context unless you explicitly provide it via the prompt or attached files.
If the user provided instructions (including via AGENTS.md, CLAUDE.md, etc.) which are relevant to the task, include them as well.
Additionally, if available, provide instructions for testing the code or verifying the task is complete.

## Task Fusion
Since this skill is capable of using tools and calling commands, put the commands into the prompt instead of running them first and injecting their results.

**Compound and fuse as many actions as reasonable into the instructions provided to the agent, including prelude and post-skill actions.**
**For complex tasks with provided testable outcomes, prefer to include instructions such as:**
> After making changes, run the tests to verify they work. If they fail, iterate and refine until the tests pass. However, if the task seems intractable, summarize the issues and report them instead.

The agent is fully proficient in ALL common programming languages and file formats. Instructions that do not affect semantics such as "Add explicit template instantiations at the bottom of the .cpp:" or "Use `this->` prefix for dependent names" are generally not needed.

As a general rule of thumb, prefer to think less about the minutae of the task, and instead let the agent deal with it.

## Verifying Work
Since this skill is capable of using tools and calling commands, prefer to have the agent **provide evidence of its results**.

**When writing prompts for this agent, use the WRITE skill. DO NOT use `cat`, `echo`, or other shell commands to write the prompt unless absolutely necessary.**

## File Paths
When providing paths to the agent, use **absolute paths**. This prevents confusion between `/tmp` (global temporary) and `./tmp` (local temporary), and ensures that interactions with the agent are unambiguous.

# Available Tools and Documentation:
- [Continue](./tools/continue.md)
- [Opencode](./tools/opencode.md)

