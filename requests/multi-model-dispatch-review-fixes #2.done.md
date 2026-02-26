# Feature: multi-model-dispatch review fixes #2

## Scope

Single bounded fix slice for Iteration 2 findings:
1) robust error normalization for all catch paths
2) remove unused execute context parameter

## Source Review

- `requests/code-reviews/multi-model-dispatch-review #2.md`

## Fix Tasks

1. `.opencode/tools/dispatch.ts`
   - Add helper to safely derive error message from `unknown`.
   - Switch all catch clauses to `unknown` and use helper output.

2. `.opencode/tools/dispatch.ts`
   - Rename unused `context` parameter to `_context`.

## Validation

```bash
cd .opencode && bun build tools/dispatch.ts --outdir .tmp/dispatch-check
```
