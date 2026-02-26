# Code Review: multi-model-dispatch (Iteration 2)

## Critical

- None.

## Major

1. `.opencode/tools/dispatch.ts`
   - Catch blocks assume `err.message` exists; non-Error throws can crash inside catch.
   - Fix: normalize unknown errors via helper and use in every catch path.

## Minor

1. `.opencode/tools/dispatch.ts`
   - `context` parameter is unused.
   - Fix: remove it or rename to `_context`.

## Verdict

Critical: 0, Major: 1, Minor: 1
