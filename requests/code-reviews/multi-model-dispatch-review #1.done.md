# Code Review: multi-model-dispatch (Iteration 1)

## Critical

- None.

## Major

- None.

## Minor

1. `.opencode/package.json:4`
   - `@opencode-ai/sdk` uses `latest`, which is non-reproducible.
   - Fix: pin to a tested exact version.

2. `.opencode/tools/dispatch.ts:13-25`
   - `provider`, `model`, and `prompt` allow empty strings.
   - Fix: add `.min(1, "...")` constraints.

3. `.opencode/tools/dispatch.ts:103`
   - Prompt failure cleanup always deletes newly created sessions, even with `cleanup=false`.
   - Fix: gate failure-path cleanup with the same cleanup policy (`args.cleanup ?? !isReusedSession`).

## Verdict

Critical: 0, Major: 0, Minor: 3

Slice complete: no Critical/Major issues
