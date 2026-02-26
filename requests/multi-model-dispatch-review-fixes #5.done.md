# Feature: multi-model-dispatch review fixes #5

## Scope

Minor-only quick-safe hardening slice:
1) validate `jsonSchema` parses to object
2) enforce safe maximum timeout bound

## Source Review

- `requests/code-reviews/multi-model-dispatch-review #5.md`

## Fix Tasks

1. `.opencode/tools/dispatch.ts`
   - Validate parsed schema is a non-array object before assigning `format`.

2. `.opencode/tools/dispatch.ts`
   - Add max timeout guard for JS timer-safe bounds.

## Validation

```bash
cd .opencode && bun build tools/dispatch.ts --outdir .tmp/dispatch-check
```
