# Feature: multi-model-dispatch review fixes #3

## Scope

Single bounded fix slice: make session cleanup policy consistent across success and prompt-failure paths.

## Source Review

- `requests/code-reviews/multi-model-dispatch-review #3.md`

## Fix Tasks

1. `.opencode/tools/dispatch.ts`
   - In prompt-failure catch, use `shouldCleanup` without excluding reused sessions.
   - Keep best-effort deletion semantics.

## Validation

```bash
cd .opencode && bun build tools/dispatch.ts --outdir .tmp/dispatch-check
```
