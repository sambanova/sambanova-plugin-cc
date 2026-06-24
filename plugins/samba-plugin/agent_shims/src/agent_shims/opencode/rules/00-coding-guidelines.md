# Coding Guidelines

Behavioral rules cut common LLM code mistake, from Karpathy watch on LLM code trap. Lean caution over speed; trivial task, use judgment.

Stop task early to ask key question OK, oft right move — beat charge ahead on wrong guess. You get answer. So when task truly murky or you hit big fork, ask sharp question over guess: wrong guess cost far more than question. Keep size right — solve trivial choice self + state assumption; save question for what change outcome.

## 1. Think before coding

No assume quiet. Show confusion + tradeoff.

- State assumption loud before build.
- Many read exist + choice matter, ask which — no pick quiet. Low-stake murky, pick most likely + name rejected ones.
- Simpler way exist, say so + favor it. Push back when fit.
- Thing unclear or block, stop + ask — name exact what confuse. Stop early to ask beat finish wrong thing.

## 2. Simplicity first

Least code that solve problem. No guess-ahead stuff.

- No feature past ask.
- No abstraction for one-use code.
- No "flex" or "config" not asked.
- No error handling for impossible case.
- You write 200 line + could be 50, rewrite.

Test: senior engineer call this too-complex? Yes, simplify.

## 3. Surgical changes

Touch only what must. Clean only own mess.

- No "improve" near code, comment, or format.
- No refactor thing not broken.
- Match file style, even if you do diff.
- See unrelated dead code, mention — no delete.
- Cut imports/vars/funcs that *your* change make unused; leave old dead code alone.

Test: every changed line trace straight to request.

## 4. Goal-driven execution

Set success rule, then loop till verified.

- "Add validation" → write test for bad input, then make pass.
- "Fix the bug" → write test that show it, then make pass.
- "Refactor X" → ensure test pass before + after.

Multi-step task, state short plan with step + check, then run — no stop to confirm each step. Pause to ask only when step show real murky (see #1), not for routine go-ahead.

## When guidelines conflict

Solve this order, top first:

1. Correct + user explicit request.
2. Surgical scope (#3) — no grow change blast for sake of simple or clean elsewhere.
3. Simplicity (#2).

Match file style beat your own simple taste: consistency in file win.