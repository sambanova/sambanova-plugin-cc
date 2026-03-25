# continue

Single-pass coding sub-agent. Faster than opencode but does not iterate by default.

## When to Use
- Quick generation where one-shot accuracy is sufficient
- Qwen3-235B + C++ (produces significantly cleaner output than opencode)
- Simpler tasks that don't need write-test-fix loops
- When you need faster turnaround

## When to Use opencode Instead
- Complex tasks that need iterative refinement
- Tasks where reading existing code context matters
- When you need `--tool-arg --file` to target specific files

## Prompt Structure

Same fundamentals as opencode, but even more important to be precise since there's no iteration:

1. **Be specific in one shot** — the model won't get a second pass to fix bugs
2. **Explicit file paths required** — "Write to /full/path/to/file"
3. **Keep prompts concise** — shorter is better since continue doesn't iterate
4. **Request a test/demo in main()** to verify correctness

## Multi-Iteration: Driving the Loop Yourself

`continue` does not iterate on its own, even if asked to "compile and fix". To get iterative refinement, **you must drive the loop externally**:

1. Call `continue` to generate the initial code
2. Compile/run the output yourself
3. Call `continue` again with the error output and a targeted diagnosis

This is highly effective when you can pinpoint the bug category in your follow-up prompt:

- **Stress test bugs**: "Each consumer loops to 80000 but there are 8 consumers sharing 80000 items — use a shared atomic counter instead"
- **Runtime panics**: "Intn panics when n<=0 — guard the steal target count"
- **Compile errors**: Paste the exact error and ask for a fix

The key is **diagnosing the root cause yourself** and giving a targeted hint, not just pasting the error and hoping. Generic "fix this error" prompts tend to introduce new bugs.

## Model Pairing

| Model | continue | opencode |
|-------|----------|----------|
| MiniMax-M2.5 | Reliable for all languages | Reliable for all languages |
| Qwen3-235B | C++ only (cleaner than opencode) | C++ only (may duplicate output) |

Key difference: **Qwen C++ is better with `continue`** — the opencode duplication bug doesn't appear.

## Post-Generation
- Always check file sizes — especially with Qwen, verify the write actually happened
- For Qwen + Python/Go: don't bother retrying, switch to MiniMax-M2.5
