# opencode

Single-shot coding sub-agent. Sends the prompt and file context in one request and returns the response. No tool use or iteration.

## When to Use
- Qwen3-235B tasks where you need `--tool-arg --file` to inject file context
- When you want deterministic, side-effect-free output (no filesystem modifications)
- Short, focused tasks where a single response is sufficient

## When to Use continue Instead
- **MiniMax-M2.5 tasks** — opencode has ~80% think-only failure rate with this model
- Large-scale code generation (continue can iterate across turns)
- Reviewing files over ~1,500 lines (opencode truncates)
- Tasks that benefit from write-test-fix loops

## Prompt Structure

1. **Lead with the action** — "Write a complete implementation of X to /path/to/file"
2. **List requirements as numbered items**
3. **Specify the target file path explicitly**
4. **Request a test/demo in main()** to anchor the output
5. **Keep prompts to 200-500 words** — longer prompts cause duplication with some models

## Setup Checklist
- Pre-create stub files with a minimal skeleton before invoking
- Ensure build files exist (Cargo.toml, go.mod, etc.)
- Set cwd to the directory containing the target file
- One file per invocation

## Model Pairing
- **MiniMax-M2.5**: ~80% think-only failure rate. **Use `continue` instead.** If you must use opencode, expect to retry multiple times.
- **Qwen3-235B**: Only reliable for C++ (produces duplicated output more often than with `continue`)

## Limitations
- **Single file read limit**: opencode can only read ~1,500 lines of a file in one pass. For reviewing large files (3,000+ lines), use `continue` instead.
- **Think-only failures with MiniMax**: Stochastic issue where the model spends its entire token budget on `<think>` blocks with no actual output. Not related to `--max-tokens` value. Retrying sometimes helps, but `continue` is far more reliable.

## Anti-Patterns
- Don't provide exact algorithm pseudocode — models introduce subtle bugs while approximating it
- Don't combine multiple hard requirements in one prompt — use iterations
- Don't retry the same failing prompt — if a file wasn't written, switch models or use `continue`
- Set timeout to 300s+ for complex tasks
