# Feature: multi-model-dispatch review fixes #4

## Scope

Minor-only quick-safe cleanup slice:
1) strict timeout argument validation
2) remove `any` from response parsing path

## Source Review

- `requests/code-reviews/multi-model-dispatch-review #4.md`

## Fix Tasks

1. `.opencode/tools/dispatch.ts`
   - Validate `timeout` when provided (`> 0` and finite).

2. `.opencode/tools/dispatch.ts`
   - Replace `any` in parse/response extraction with unknown-safe helpers.

## Validation

```bash
cd .opencode && bun build tools/dispatch.ts --outdir .tmp/dispatch-check
```
