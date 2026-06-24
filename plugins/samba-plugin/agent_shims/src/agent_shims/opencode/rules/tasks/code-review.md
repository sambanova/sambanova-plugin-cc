---
description: Read when reviewing code, reviewing a diff/PR, finding bugs, or critiquing a change
---

# Code Review

Goal: find REAL problems that MATTER, ranked. Two failure mode kill a review:
- False positive — flag bug that not real. Each one burn your credibility; reader stop trusting you.
- Noise — bury one real bug under ten style nit. Signal must stay high.

## Verify before flag

- Every finding must be real + demonstrable. Trace the path, confirm it actually trigger, before you write it. Suspect ≠ confirmed.
- Read enough context first. Issue you see in diff may be handled by caller, guard, or code elsewhere. Open that code + check before claim. Out-of-context snippet = false positive.
- Cite exact location: `path:line`. No location → reader can not verify → not a finding.
- Unsure? Say so. Label confidence: "bug" (sure) vs "possible" (need check) vs "style". Never dress a guess as certain.

## Prioritize

- Rank by severity, worst first: correctness / data loss / security → crash / resource leak → logic edge case → style.
- Lead with what matter. Do NOT drown a real correctness bug under cosmetic nit.
- Style + preference last, and only if asked or it truly hurt readability. No bikeshed.

## What to check (high value)

- Correctness: off-by-one, wrong operator (`<` vs `<=`), inverted condition, wrong var.
- Edge case: null / empty / zero / overflow / unicode / huge input.
- Error path: swallowed error, missing handling, wrong error, leak on failure.
- Resource: unclosed file/conn, leak, double-free, lock not released.
- Concurrency: race, unguarded shared state, deadlock order.
- Security: injection, unescaped input, secret in code, missing authz, path traversal.
- Contract: does change match what caller expect? break API? break test?

## How to report

- Specific + actionable: what wrong, why it matter, how to fix. No vague "this could be cleaner".
- Fix = minimal + targeted, match codebase style. Suggest the small change, not a rewrite.
- Distinguish bug from intentional. Code may be odd on purpose — flag as question if unsure, not as defect.
- No praise padding. Skip "looks good overall" filler unless asked. Reader want problems, ranked.

## Scope

- Review the change, not the whole world. Focus diff + what it touch. Note unrelated issue brief, do not chase or rewrite it.
