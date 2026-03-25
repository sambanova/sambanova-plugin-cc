# Qwen3-235B

65K context, 4K max completion. Strong conceptual reasoning but limited tool-use reliability.

## Best For
- C++ code generation (especially via `continue`)
- Architectural design and high-level structure
- Tasks where the 4K completion window is sufficient

## Known Limitations
- **Cannot write Python or Go files** via either tool — this is a model-level tool-use issue, not a prompt engineering problem
- 4K completion limit truncates complex implementations
- Rust fundamentals (e.g., incorrectly derives Copy on atomics, misuses &self for mutable access)
- Long prompts cause output duplication (especially with `opencode`)

## How to Prompt

**Do:**
- Keep prompts short and focused — Qwen is sensitive to prompt length
- Use `continue` for C++ tasks (produces cleaner output than `opencode`)
- Name specific language features you want ("use concepts", "use coroutines")
- Specify a single output file per invocation
- Always verify the file was actually written after completion

**Don't:**
- Use Qwen for Python or Go tasks — use MiniMax-M2.5 instead
- Write long, multi-requirement prompts — the model loses track and duplicates sections
- Retry with different wording if the model failed to write a file — switch models instead
