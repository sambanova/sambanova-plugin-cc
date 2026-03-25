# continue

Agentic coding sub-agent with tool use. Runs in `--auto` mode with access to file read/write and terminal tools. Can iterate across multiple turns, making it the **preferred tool for MiniMax-M2.5**.

## When to Use
- **Default choice for MiniMax-M2.5** — opencode has ~80% think-only failure rate with this model
- Complex, large-scale code generation (tested up to 3,700 lines / 132KB in one session)
- Reviewing large files — can read in chunks across multiple tool calls (no ~1,500 line limit like opencode)
- Tasks that benefit from write-test-fix loops (continue drives these itself — tested: wrote code, ran 67 tests, fixed bugs across multiple turns autonomously)
- Qwen3-235B + C++ (produces significantly cleaner output than opencode)

## When to Use opencode Instead
- When you want deterministic, side-effect-free output (continue uses tools that modify the filesystem)
- Qwen3-235B tasks where you need `--tool-arg --file` to inject file context directly

## Prompt Structure

1. **Lead with the action** — "Read /path/to/file and write a code review" or "Implement X and write it to /path/to/file"
2. **List requirements as numbered items**
3. **Explicit file paths** — continue can create files via tool use, but specifying paths keeps output predictable
4. **Request tests** — continue can write tests, run them, and fix failures in a loop
5. **Keep prompts to 200-500 words** — the model iterates, so you don't need to front-load everything

## Model Pairing

| Model | Recommendation |
|-------|---------------|
| **MiniMax-M2.5** | **Strongly preferred.** Reliable across all languages. Handles large tasks (3,700+ lines). opencode has ~80% failure rate. |
| **Qwen3-235B** | C++ only (cleaner than opencode). Does not reliably write Python/Go files with either tool. |

## Session Isolation
Each `cn` invocation runs with an isolated `HOME` directory to prevent session history leakage. Without this, `cn` injects a `conversationSummary` from the most recent prior session for the same workspace, causing the model to respond based on stale context. The config is passed via `--config`, so no files from the real `~/.continue` are needed.

## Post-Generation
- Always check file sizes — especially with Qwen, verify the write actually happened
- For Qwen + Python/Go: don't bother retrying, switch to MiniMax-M2.5
- `continue` in `--auto` mode may find and operate on pre-existing files on disk — clean up stale artifacts from `/tmp` or the working directory before running if you need fresh output
