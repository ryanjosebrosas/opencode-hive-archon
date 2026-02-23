# GitHub Workflows & Review Automation

Example workflow YAML files and review automation setup for your GitHub repository.

## Architecture

This template uses a two-part system for automated code quality:

1. **CodeRabbit** (GitHub App) — Automatically reviews every PR. No workflow YAML needed. Install once from the GitHub Marketplace.
2. **Claude Code** (GitHub Action) — Reacts to CodeRabbit's reviews and auto-applies suggested fixes, or handles issue-triggered fix/create tasks.

Together they create an automated review-fix loop: CodeRabbit reviews → Claude fixes → CodeRabbit re-reviews → repeat (up to MAX_ITERATIONS).

## What's Included

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `claude-fix-coderabbit.yml` | CodeRabbit review (auto) or `@claude-fix` on PR | Auto-apply CodeRabbit review suggestions |
| `claude-fix.yml` | `@claude-fix` or `@claude-create` on Issues | Run fix (bug) or full PIV Loop (enhancement) from issues |

**Note**: Code reviews are handled by CodeRabbit (GitHub App), not a workflow. See `templates/GITHUB-SETUP-CHECKLIST.md` for installation steps.

## Quick Start

1. Install [CodeRabbit from GitHub Marketplace](https://github.com/marketplace/coderabbit-ai)
2. Add `.coderabbit.yaml` to your repo root (copy from template root)
3. Copy these YAML files to your repo's `.github/workflows/` directory
4. Copy prompt templates from `.github/workflows/prompts/` to the same location in your repo
5. Add your `CLAUDE_CODE_OAUTH_TOKEN` secret (see `templates/GITHUB-SETUP-CHECKLIST.md`)
6. Enable PR creation in repo settings
7. Update `AUTHORIZED_USERS` in `claude-fix.yml` with your GitHub username
8. Push to GitHub

See `templates/GITHUB-SETUP-CHECKLIST.md` for the complete step-by-step setup guide.

## Customization

### Authorized Users

In `claude-fix.yml`, find the `AUTHORIZED_USERS` variable and add your GitHub username(s):

```yaml
AUTHORIZED_USERS="your-username another-username"
```

### Prompt Template Paths

Workflows expect prompt templates at `.github/workflows/prompts/`. If you place them elsewhere, update the `cat` commands in the "Load instructions" step.

### Loop Iteration Limit

In `claude-fix-coderabbit.yml`, adjust the `MAX_ITERATIONS` env var to control how many review-fix cycles are allowed:

```yaml
env:
  MAX_ITERATIONS: 3  # Default: 3
```

### Label-Based Routing

The issue fix workflow (`claude-fix.yml`) routes based on issue labels:
- Issues labeled `enhancement`, `feature`, or `new feature` → loads `end-to-end-feature-github.md` (full PIV Loop)
- All other issues → loads `bug-fix-github.md` (RCA + fix)

### CodeRabbit Configuration

Customize CodeRabbit behavior via `.coderabbit.yaml` in your repo root. Key settings:
- `reviews.profile` — `"chill"` (fewer comments) or `"assertive"` (thorough)
- `reviews.auto_review.enabled` — Toggle automatic reviews
- `reviews.auto_review.drafts` — Include/exclude draft PRs

## Secrets Reference

| Secret | How to Get | Required By |
|--------|-----------|-------------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Run `claude setup-token` locally | `claude-fix.yml`, `claude-fix-coderabbit.yml` |
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions | All workflows (for `gh` CLI) |

## Troubleshooting

- **CodeRabbit doesn't review**: Check App installation at Settings → Integrations → CodeRabbit
- **Workflow doesn't appear**: Ensure YAML files are in `.github/workflows/` on the default branch
- **Workflow triggers but fails**: Check Actions logs for permission or secret errors
- **Agent can't create PRs**: Enable "Allow GitHub actions to create and approve pull requests" in Settings → Actions → General
- **Comment not recognized**: Ensure the comment starts with the exact trigger text (e.g., `@claude-fix`)
- **Template not found**: Verify prompt template paths match the `cat` commands in the YAML
- **Infinite loop**: Check MAX_ITERATIONS setting and verify `[claude-fix]` commit prefix is working
- **Free tier after trial**: Private repos need Lite/Pro plan for full CodeRabbit reviews
