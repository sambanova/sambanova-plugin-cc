# opencode

Iterative coding sub-agent that can run write-test-fix loops.

## When to Use
- Complex tasks that benefit from iterative refinement
- Tasks where the model needs to read existing code for context
- When targeting specific files with `--tool-arg --file /path`

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
- **MiniMax-M2.5**: Reliable for all languages
- **Qwen3-235B**: Only reliable for C++ (produces duplicated output more often than with `continue`)

## Anti-Patterns
- Don't provide exact algorithm pseudocode — models introduce subtle bugs while approximating it
- Don't combine multiple hard requirements in one prompt — use iterations
- Don't retry the same failing prompt — if a file wasn't written, switch models
- Set timeout to 300s+ for complex tasks
