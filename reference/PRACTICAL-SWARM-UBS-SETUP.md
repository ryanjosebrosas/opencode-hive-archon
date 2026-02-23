# Practical SwarmTools + UBS Setup

> **No-BS Guide**: Get bug-catching automation in 2 hours. Skip the overengineering.

**Version**: 1.0  
**Last Updated**: 2026-02-23  
**Status**: Ready to Implement  
**Estimated Time**: 2 hours

---

## Quick Decision Tree

```
Do you want fewer bugs in production?
    │
    YES → Do this guide (2 hours)
    │
    NO  → Close this file, go touch grass
```

---

## What You're Getting

| Feature | What It Does | Why You Care |
|---------|--------------|--------------|
| **UBS Bug Scanner** | Catches 1000+ bug patterns | Prevents embarassing commits |
| **Git Hooks** | Auto-scan before commit | Blocks bugs before they merge |
| **Agent Guardrails** | AI runs UBS automatically | No need to remember |
| **File Watchers** | Scan on save | Instant feedback |

**What You're NOT Getting** (and don't need yet):
- ❌ CASS session search (nice-to-have, revisit in 6 months)
- ❌ Multi-machine sync (overkill for most)
- ❌ Custom rules (defaults catch 95% of bugs)
- ❌ CI/CD integration (add when you have a team)

---

## Prerequisites

| Requirement | Check |
|-------------|-------|
| **SwarmTools installed** | `swarm doctor` ✅ (you already did this) |
| **Git repository** | `git status` ✅ |
| **Python 3.8+** | `python --version` |
| **Node.js 18+** | `node --version` |

---

## Step 1: Install UBS (15 minutes)

### The Easy Way (Recommended)

```bash
# Windows (PowerShell or Git Bash)
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/master/install.sh" | bash -s -- --easy-mode
```

**What `--easy-mode` does:**
1. ✅ Installs UBS globally
2. ✅ Installs dependencies (ast-grep, ripgrep, jq, typos)
3. ✅ Detects your AI agents (Claude, Cursor, etc.)
4. ✅ Wires guardrails into agent configs
5. ✅ Sets up git hooks
6. ✅ Configures file watchers

### What You'll See

```
🔬 Ultimate Bug Scanner v5.0 - Installing...

✓ UBS binary installed
✓ Dependencies installed (ast-grep, ripgrep, jq)
✓ Detected AI agents: Claude Code, OpenCode
✓ Configured agent guardrails
✓ Set up git hooks
✓ Set up file watchers
✓ Added to AGENTS.md

✨ Installation complete! Run 'ubs doctor' to verify.
```

### Verify Installation

```bash
ubs --version
# Expected: ubs 5.0.6 (or similar)

ubs doctor
# Expected: All checks passing
```

---

## Step 2: Test UBS Scan (5 minutes)

### Scan Your Project

```bash
cd C:\Users\Utopia\Desktop\opencode
ubs .
```

### Expected Output

```
╔══════════════════════════════════════════════════════════════╗
║  🔬 ULTIMATE BUG SCANNER v5.0 - Scanning your project...     ║
╚══════════════════════════════════════════════════════════════╝

Project:  C:\Users\Utopia\Desktop\opencode
Files:    45 TypeScript + 12 JavaScript files
Finished: 2.3 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary Statistics:
  Files scanned:    57
  🔥 Critical:      0
  ⚠️  Warnings:      3
  ℹ️  Info:          12

✨ GOOD! No critical issues found ✨
```

### If Bugs Are Found

```
🔥 CRITICAL: 2 bugs found

#1: Null pointer dereference
   File: src/auth/service.ts:42
   Issue: User object may be null
   Fix: Add null check before accessing user.email

#2: Missing await
   File: src/api/handler.ts:18
   Issue: Promise not awaited
   Fix: Add 'await' before database call
```

**Fix the critical bugs before proceeding.**

---

## Step 3: Verify Git Hooks (5 minutes)

### Check Hooks Are Installed

```bash
# Windows
ls .git/hooks/pre-commit
ls .git/hooks/pre-push
```

### Test Pre-Commit Hook

```bash
# Create a file with an intentional bug
echo "const x = undefined; x.foo();" > test-bug.ts

# Try to commit it
git add test-bug.ts
git commit -m "test: intentional bug"
```

### Expected Output (Hook Should Block)

```
🔬 Running bug scanner on changed files...

test-bug.ts:
  🔥 CRITICAL: Null pointer dereference at line 1

❌ Critical issues found. Fix before commit.
Hint: Use --no-verify to bypass (not recommended)
```

### Clean Up Test File

```bash
git reset HEAD test-bug.ts
rm test-bug.ts
```

---

## Step 4: Verify Agent Guardrails (10 minutes)

### Check Guardrails Are Installed

```bash
# For Claude Code
ls .claude/agents/rules.md

# For OpenCode
cat AGENTS.md | grep -A 10 "UBS\|bug scanner"
```

### What Guardrails Look Like

**`.claude/agents/rules.md`:**
```markdown
## Quality Standards

Before marking ANY task complete:

1. Run bug scanner: `ubs .` or `ubs <changed-files>`
2. Fix ALL critical issues (🔥)
3. Review warnings (⚠️) - fix if trivial
4. Only then mark complete

If scanner finds critical issues, task is NOT done.
```

### Test Agent Guardrail

```
> /prime

# Then ask AI:
"Implement a simple utility function"

# Expected: AI should mention running ubs before completing
```

---

## Step 5: Test First Swarm with UBS (30 minutes)

### Run a Simple Swarm

```
> /swarm "Create a health check endpoint at /api/health"
```

### Watch the Flow

```
Analyzing task...
Decomposing into 2 subtasks:
  1. Create /api/health endpoint
  2. Add health check test

Creating epic: bd-abc123
  ├─ bd-abc123.1 (worker-1)
  └─ bd-abc123.2 (worker-2)

Spawning 2 worker agents...

[worker-1] Reserved: src/api/health.ts
[worker-1] ✓ Created endpoint
[worker-1] 🔬 UBS scan: 0 issues

[worker-2] Reserved: src/api/health.test.ts
[worker-2] ✓ Added tests
[worker-2] 🔬 UBS scan: 0 issues

✓ All subtasks complete
✓ UBS scan: 0 issues
✓ Synced to git
```

### Key Observation

**Notice:** Each worker ran UBS before `swarm_complete`. This is the autonomy working.

---

## Step 6: Daily Workflow (Ongoing)

### Your New Normal

```
1. Start task
   > /swarm "Add feature X"

2. Workers implement
   - File reservations prevent conflicts
   - Progress checkpoints at 25/50/75%

3. Before complete
   - UBS scans automatically
   - Bugs fixed by AI
   - Re-scan passes

4. Commit
   - Git hooks verify again
   - Push to remote
```

### Manual Scans (When Needed)

```bash
# Scan specific files
ubs src/auth/**/*.ts

# Scan staged changes
ubs --staged

# Scan with strict mode (fail on warnings)
ubs . --fail-on-warning

# Quiet mode (summary only)
ubs . --quiet
```

---

## Configuration (Optional)

### Skip False Positives

Create `.ubs-ignore` in project root:

```bash
# Ignore specific files
test-bugs.ts
legacy/code.js

# Ignore specific patterns
# ubs:ignore
eval("safe code")
```

### Adjust Strictness

```bash
# CI mode (fail on warnings)
ubs . --fail-on-warning

# Quiet mode (summary only)
ubs . --quiet

# JSON output (for tooling)
ubs . --format=json
```

---

## Troubleshooting

### Problem: "ubs: command not found"

**Solution:**
```bash
# Verify installation
npm list -g ultimate-bug-scanner

# Reinstall if needed
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/master/install.sh" | bash
```

---

### Problem: "Git hook not running"

**Solution:**
```bash
# Check hook exists
ls .git/hooks/pre-commit

# Make executable (Windows Git Bash)
chmod +x .git/hooks/pre-commit

# Check hook content
cat .git/hooks/pre-commit
```

---

### Problem: "Too many false positives"

**Solution:**
```bash
# Add to .ubs-ignore
echo "path/to/file.ts" >> .ubs-ignore

# Or inline suppression
riskyCode() # ubs:ignore
```

---

### Problem: "UBS slowing down workflow"

**Reality Check:** UBS should add 1-3 seconds per scan. If slower:

```bash
# Scan only changed files
ubs --staged

# Exclude slow directories
ubs . --exclude "node_modules,vendor"

# Use quiet mode
ubs . --quiet
```

---

## What's Next

### After 2 Weeks of Use

Ask yourself:

| Question | If "Yes" → |
|----------|------------|
| Am I catching bugs before commit? | ✅ Working as intended |
| Is AI running UBS automatically? | ✅ Guardrails working |
| Do I want historical session search? | → Add CASS (see Appendix) |
| Am I getting false positives? | → Add custom `.ubs-ignore` rules |
| Does my team want CI/CD integration? | → Add GitHub Actions |

### When to Add CASS (3-6 months)

**Add CASS when:**
- ✅ You have 100+ AI sessions
- ✅ You use 3+ different agents (Claude, Codex, Cursor, etc.)
- ✅ You find yourself manually searching old sessions

**Not before.** The learning curve isn't worth it for small session counts.

---

## Appendix A: CASS Setup (Optional, Future)

**Install when ready:**

```bash
# Manual install (no easy-mode for CASS)
git clone https://github.com/Dicklesworthstone/coding_agent_session_search
cd coding_agent_session_search
pip install -e .

# Initial index (5-30 min)
cass index

# Verify
cass search "test" --robot --limit 1
```

**Auto-indexing (cron):**
```bash
# Edit crontab
crontab -e

# Add: Index every hour
0 * * * * cass index --incremental
```

---

## Appendix B: Command Quick Reference

### UBS Commands

```bash
ubs .                        # Scan entire project
ubs src/**/*.ts              # Scan specific files
ubs --staged                 # Scan git staged changes
ubs --diff                   # Scan working tree changes
ubs --fail-on-warning        # Strict mode (CI)
ubs --format=json            # JSON output
ubs --quiet                  # Summary only
ubs doctor                   # Check installation
```

### Git Hook Bypass (Emergency Only)

```bash
git commit --no-verify       # Skip pre-commit hook
git push --no-verify         # Skip pre-push hook
```

**⚠️ Warning:** Only use for emergencies. You're bypassing quality gates.

---

## Appendix C: Success Metrics

| Metric | Target | Check |
|--------|--------|-------|
| **Bugs Caught Pre-Commit** | 3-5/week | Git hook logs |
| **UBS Scan Time** | <3 seconds | Scan output |
| **False Positive Rate** | <5% | Manual review |
| **AI Auto-Runs UBS** | 90%+ sessions | Session logs |

---

## Summary

### What You Did (2 hours)

- [x] Installed UBS with `--easy-mode`
- [x] Verified installation (`ubs doctor`)
- [x] Tested scan on project
- [x] Verified git hooks block bugs
- [x] Verified agent guardrails
- [x] Ran first swarm with UBS integration
- [x] Configured `.ubs-ignore` (if needed)

### What You Get

- ✅ Automatic bug scanning before commits
- ✅ Git hooks blocking critical bugs
- ✅ AI agents running UBS automatically
- ✅ Real-time file watchers
- ✅ Fewer bugs in production

### What You Skipped (For Now)

- ❌ CASS session search (add in 3-6 months if needed)
- ❌ Multi-machine sync (overkill)
- ❌ Custom rules (defaults work)
- ❌ CI/CD integration (add when you have a team)

---

**Bottom Line:** You now have 80% of the "autonomous ecosystem" value in 20% of the time. The rest is optional optimization.

**Documentation Version**: 1.0  
**Setup Time**: 2 hours  
**Maintenance**: Zero (auto-updates)  
**ROI**: Immediate (catches bugs this week)
