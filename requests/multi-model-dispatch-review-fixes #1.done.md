# Feature: multi-model-dispatch review fixes #1

## Scope

Single bounded fix slice for Iteration 1 minor findings:
1) reproducible SDK dependency pin
2) non-empty input constraints for required tool args
3) cleanup policy consistency on prompt-failure path

## Source Review

- `requests/code-reviews/multi-model-dispatch-review #1.md`

## Fix Tasks

1. `.opencode/package.json`
   - Pin `@opencode-ai/sdk` from `latest` to exact tested version.

2. `.opencode/tools/dispatch.ts`
   - Add `.min(1, ...)` constraints for `provider`, `model`, and `prompt`.
   - Apply consistent `shouldCleanup` policy in failure cleanup path.

## Validation

```bash
cd .opencode && bun install
cd .opencode && bun build --no-bundle tools/dispatch.ts --outdir .tmp/dispatch-check
```
