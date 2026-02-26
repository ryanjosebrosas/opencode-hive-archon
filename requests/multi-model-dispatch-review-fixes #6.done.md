# Feature: multi-model-dispatch review fixes #6

## Scope

Single bounded fix slice:
1) unify timeout cleanup with `shouldCleanup`
2) validate `port` integer/range
3) harden raw-response stringify in error paths

## Source Review

- `requests/code-reviews/multi-model-dispatch-review #6.md`

## Fix Tasks

1. `.opencode/tools/dispatch.ts`
   - Replace timeout branch cleanup condition with `shouldCleanup`.

2. `.opencode/tools/dispatch.ts`
   - Validate `port` as integer between 1 and 65535.

3. `.opencode/tools/dispatch.ts`
   - Add safe stringify helper for raw response/error diagnostics.

## Validation

```bash
cd .opencode && bun build tools/dispatch.ts --outdir .tmp/dispatch-check
```
