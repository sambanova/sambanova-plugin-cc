---
description: Read when exploring, investigating, searching, locating, or explaining code or a codebase
---

# Exploration

Findings here MUST obey strict grounding.

Asymmetry rule above all: misleading summary cost MASSIVE, extra file read cost tiny. So read liberal — when in doubt, open it. Better waste 10 read than ship 1 wrong claim.

## Citations — hard rule

- Every finding cite concrete source: `path:line` (or `path:start-end`, commit hash, URL). No citation → not finding → drop it.
- Cite ONLY what you open + read this session. Never cite from memory, training, or guess. No read = no find.
- Point exact: `auth/session.py:42-58`, not "somewhere in auth module".
- Claim hinge on specific code? Quote the load-bearing line, so reader verify without re-hunt.
- Read enough scope. No conclude from 5-line snippet — read whole fn, class, surrounding context before you say what it do. Snippet out of context = wrong claim.

## Fact vs guess

- Separate verified from hypothesized. Finding = you read it. Guess = label it guess. Never blur two.
- Negative claim ("X not exist", "Y not used") need shown search: state what you search — dir, pattern. Else say "did not find", not "does not exist". Absence of evidence ≠ evidence of absence.
- Report unknown loud. What you could not resolve — not found, path ran out, truly ambiguous — name the gap. Never paper hole with confident-sound guess.

## Thorough

- No stop at first hit. State search breadth — check many location + naming convention before conclude. One match ≠ whole answer.
- Trace call chain. Finding depend on what fn do or where call go? Open callee, then its callee, follow path till you KNOW. No "this probably call X which likely do Y" — that hypothesize, not trace.
- Find impl that ACTUALLY run. Push through indirection — interface, abstract method, dynamic dispatch, DI, registry, config-wire. No stop at first or abstract `def`; follow to concrete code that run on this path.
- Trace upstream too. "How X work / when X happen" → find caller, entry point, trigger, not just what X call. Trace go both way.
- Goal = high-quality product, not sketch. Verified depth beat plausible guess. Pay cost to follow path, do not shortcut with assumption.
- Conflicting evidence? Surface it, no smooth over.

## Discipline

- Cite source-of-truth, not echo. Real code ≠ comment, doc, test, stale README that may lie. Cite the code.
- Name + comment can lie. Fn call `validate` may not validate; comment may be stale. Ground claim in what code DO, not what it name or doc say.
- Answer asked. Stay scope. Note near finding, no chase it.
