---
name: code
description: Run a powerful coding tool as a sub-agent with a given model and prompt. This skill should be used when tasks need to be run (e.g. build-and-test), code reviews and edits, second opinions are needed, or files need to be read and summarized.
argument-hint: <model> <cwd> <prompt> [--max-tokens <n>] [--session <id>]
allowed-tools: mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__code, mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__list_models, Write, Read
---

# Code

Run coding tool as sub-agent. Good for code review, ideation, implementation. Handle code reviews, run commands (i.e. git diff, git rebase, etc.), other tasks solo.

This skill is the in-Claude-Code front end. The implementation lives in the
plugin's MCP server (the `code` tool); this skill adds the prompting discipline
below. The skill runs inline (synchronous): the `code` MCP call blocks until the
sub-agent finishes, so its result is available in the same turn. For running
several jobs at once, see **Parallel execution** below.

## Parallel execution
The MCP server runs tool calls concurrently — each opencode run is offloaded to a
worker thread, so independent `code` requests execute in parallel server-side.

BUT the Claude Code main loop **serializes** `code` calls issued together in one
message: it sends the next request only after the previous returns. Verified —
three 20s jobs batched in one message ran back-to-back (~74s), not concurrently.
So batching calls does **not** parallelize.

To actually run `code` jobs concurrently, **fan out separate background agents**,
each making one `code` call. Independent agents dispatch concurrently and the
server runs them in parallel (verified: three agent-driven jobs overlapped, ~29s
total). Guidance:
- Use **fresh `general-purpose` agents**, not forks. A `context: fork` agent
  inherits the entire parent conversation (heavy per agent); a fresh agent starts
  near-empty (~12k tokens overhead per agent observed).
- For a **single** job, call `code` inline — synchronous, no agent overhead.
- Fan-out also isolates each job's (possibly large) output in its own context;
  only a summary returns to the main thread.

## Instructions

User request is natural language. Extract the arguments and call the MCP tool
`mcp__plugin_sambanova-plugin-cc_sambanova-plugin-cc__code`. DO NOT pass raw
user text — shape it into a proper prompt per the guidelines below.

Requires the `sambanova-plugin-cc` MCP server to be running.

### MCP tool arguments

| Arg | Required | Description |
|---|---|---|
| `model` | yes | Model name from parameters database (use `/list-models`). **Important:** bare model ID (e.g. `MiniMax-M2.7`), not provider-prefixed (e.g. ~~`sambanova/MiniMax-M2.7`~~). Provider auto-configured. |
| `prompt` | yes | Prompt for the tool. References to external tools (git, grep, find, etc.) are valid prompt text — pass verbatim, never pre-resolve. |
| `cwd` | no | Working dir for the tool. Defaults to `$CLAUDE_PROJECT_DIR`; an absolute path is recommended. Must be an existing dir. |
| `session_id` | no | Session ID from a prior `code` call, to continue that train of thought. Must reuse the **same `cwd`** as the original call — opencode keys sessions by project root, so a different/defaulted cwd silently starts fresh. |
| `max_tokens` | no | Override model's `max_completion_tokens`. DB value is default; real limit is model context length. Use for more output tokens. |
| `tool_args` | no | Extra args passed verbatim to opencode (after the prompt). To attach a file as **read-only** context (loaded into the message, works even outside `cwd`), use `["-f", "/abs/path"]`. |
| `external_dirs` | no | Absolute paths of dirs **outside `cwd`** to grant the sub-agent **read+write** access to (opencode otherwise sandboxes it to `cwd`). Use when the task must read or write files outside the project dir. opencode has no read-only external grant, so this is read+write — for read-only context prefer `tool_args ["-f", ...]`. |

The tool returns the opencode session ID and the model's text output (or its
reasoning trace, flagged, when the run ends with no text event). Surface the
session ID if the user may want to continue the session.

# Core Guidelines
Not follow = **very embarrassing**.

Write prompts with the WRITE tool when they are long or structured. DO NOT use `cat`, `echo`, or shell commands unless you must.

## Independent Action
DO NOT DO TASK YOURSELF. EMBARRASSING LIKE COVERING FOR SUBORDINATE BY DOING THEIR WORK.
DO NOT PRE-DIGEST TASKS SUCH AS RUNNING `git diff` OR `grep` FIRST. LET THE `code` TOOL DO THE WORK.

### Pre-digestion anti-pattern
If the user's request references an external tool (git, grep, find, curl, etc.), pass the
instruction **verbatim** — do NOT run the tool yourself to resolve it first.

**BAD** — pre-digesting: call `code` with prompt `"Review these changes: <pasted output of git diff main>"`.

**GOOD** — delegate fully: call `code` with prompt `"Review commits since merge-base main. Run git merge-base main HEAD, then git log/diff from that point."`

## Progress tracking
Prompt must tell sub-agent to write progress updates to file.

The progress file MUST live **inside the `cwd`** you pass. opencode sandboxes the
sub-agent to `cwd` and silently auto-rejects writes outside it (e.g. global
`/tmp`), so an external path produces no file at all. Substitute the actual `cwd`
into the path before appending. Always append to the prompt:

> As you work, write periodic progress updates to `<cwd>/tmp/progress/progress_<unique_id>.md` (a path inside this project directory). Include what phase you are on, what you have completed, and what remains.
> Write to this file when starting the task to indicate that you have started, and update it periodically even if forward progress is not being made.
> Additionally, update this file whenever encountering an unexpected or noteworthy error or update.

## Providing Context:
The tool gets the project dir and prompt. No terminal history or broader system context unless explicitly provided via prompt or attached files. If the user gave instructions (AGENTS.md, CLAUDE.md, etc.) relevant to the task, reference them too.

## An Intelligent Junior Developer
Treat as very intelligent junior dev. Handles complex multi-step tasks with minimal but strict guidance.

The `code` tool can use tools and run commands — strongly prefer putting commands in the instructions instead of running first and injecting results. Fuse actions into instructions, including prelude and coda actions.

General rule: think less about minutiae, let the `code` tool handle it.

### Complex task guidance
For complex tasks with testable outcomes, add:
> After making changes, run the tests to verify they work. If they fail, iterate and refine until the tests pass. However, if the task still fails after a few tries or needs additional guidance, summarize the issues and report them instead.

### Verifying Work
The `code` tool can use tools and commands — provide testable outcomes, have it **provide evidence of its results**.

## File Paths
Any file the sub-agent must read or write MUST be **inside the `cwd`** — opencode
sandboxes the sub-agent to `cwd` and auto-rejects paths outside it (global `/tmp`,
parent dirs, etc.), silently producing no file. Do NOT point it at global `/tmp`.

Prefer an **absolute path under `cwd`** (e.g. `<cwd>/tmp/...`) over a bare
relative path, to avoid confusion between global `/tmp` and the project-local
`./tmp` — but either resolves inside `cwd`, which is what the sandbox requires.

To reach files **outside `cwd`**, do NOT just point the sub-agent at the path
(the sandbox rejects it). Either:
- `external_dirs: ["/abs/dir"]` — grants the sub-agent **read+write** to that dir
  (use when it must edit/create files there), or
- `tool_args: ["-f", "/abs/file"]` — attaches a file as **read-only** context
  loaded into the message (use when it only needs to read it).
