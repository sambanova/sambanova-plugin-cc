# MiniMax-M2.5

163K context, 16K default max completion (platform limit is context length). Reliable file writer across all languages and tools.

## Best For
- Python, Go, and other higher-level languages
- Project scaffolding, tests, and demos
- Tasks where you need reliable single-shot generation
- Large-scale code generation (tested up to 3,700 lines / 132KB in a single task via `continue`)

## Known Limitations
- Low-level concurrency (lock-free algorithms, atomic memory ordering)
- C++17 constexpr (doesn't understand what's allowed in constexpr context)
- Rust `unsafe` code (type errors with UnsafeCell, MaybeUninit, ManuallyDrop)


## --max-tokens Behavior
The `max_completion_tokens` value is a per-turn limit, not a total output cap. With `continue` (agentic loop), the model can produce far more total output across multiple turns. With `opencode` (single-shot), the limit constrains the entire response.

Setting very high values (64k+) does not improve output quality. The 16K default works well for most tasks.

## How to Prompt

**Do:**
- Describe the problem at a high level and let the model fill in details
- Use numbered requirement lists
- Include explicit file paths ("Write to /path/to/file.py")
- Ask for a test or demo in main()
- Reference standard library patterns by name ("use frozen dataclasses", "use sync.WaitGroup")
- Keep prompts under ~500 words
- For large generation tasks, use `continue` — it can iterate across many turns

**Don't:**
- Provide exact algorithm pseudocode — the model introduces subtle bugs while "approximately" following it
- Ask for constexpr-heavy C++17 code
- Combine multiple hard low-level requirements in one prompt — break them into iterations instead
