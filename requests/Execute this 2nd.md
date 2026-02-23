# Swarm UBS Setup Plan

> **Goal**: Install UBS bug scanner, configure git hooks, and integrate guardrails into agent workflow
> **Estimated Time**: 1-2 hours
> **Complexity**: Medium (setup + integration)

---

## Solution Statement

Install Ultimate Bug Scanner (UBS) with git hooks for pre-commit bug blocking, configure agent guardrails to auto-run UBS scans, and verify the integration works with SwarmTools workers. This setup catches bugs before they reach version control.

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **UBS Installation** | curl installer with --easy-mode | Auto-configures git hooks + agent guardrails |
| **Git Hooks** | Pre-commit + pre-push | Block bugs at commit and push time |
| **Agent Guardrails** | Add UBS scan requirement to swarm workers | Ensure AI runs scans automatically |
| **Scan Scope** | Changed files only (default) | Fast feedback, skip unchanged code |
| **Strictness** | Fail on critical, warn on warnings | Balance safety vs. velocity |

---

## Implementation Plan

### Setup Phase
1. Install UBS via curl installer
2. Verify installation with `ubs doctor`
3. Run initial scan on project

### Integration Phase
4. Verify git hooks installed (pre-commit, pre-push)
5. Test git hook blocks intentional bug
6. Add UBS scan requirement to swarm worker agents

### Validation Phase
7. Test swarm worker mentions UBS in workflow
8. Create `.ubs-ignore` for any false positives
9. Document setup in memory.md

---

## Step by Step Tasks

### Task 1: Install UBS
- **ACTION**: Run UBS installation script
- **TARGET**: System-wide UBS binary + dependencies
- **IMPLEMENT**:
  ```bash
  curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/master/install.sh" | bash -s -- --easy-mode
  ```
- **PATTERN**: Pipe installer with --easy-mode flag for auto-configuration
- **IMPORTS**: None
- **GOTCHA**: Windows requires Git Bash or WSL for curl command. Use PowerShell alternative if needed.
- **VALIDATE**: `ubs --version` and `ubs doctor`

### Task 2: Verify UBS Installation
- **ACTION**: Confirm UBS is working
- **TARGET**: UBS binary and dependencies
- **IMPLEMENT**: Run verification commands
- **PATTERN**: Check version and health
- **IMPORTS**: None
- **GOTCHA**: If `ubs` not found, check PATH or reinstall
- **VALIDATE**: 
  ```bash
  ubs --version
  ubs doctor
  ```

### Task 3: Run Initial Project Scan
- **ACTION**: Scan current project for bugs
- **TARGET**: C:\Users\Utopia\Desktop\opencode
- **IMPLEMENT**: Run UBS scan on project root
- **PATTERN**: Full project scan baseline
- **IMPORTS**: None
- **GOTCHA**: First scan may take 5-10 seconds (indexing)
- **VALIDATE**: `ubs .` — expect 0 critical issues on clean codebase

### Task 4: Verify Git Hooks
- **ACTION**: Check git hooks are installed
- **TARGET**: .git/hooks/pre-commit, .git/hooks/pre-push
- **IMPLEMENT**: List hook files
- **PATTERN**: Verify executable hooks exist
- **IMPORTS**: None
- **GOTCHA**: Windows may need `chmod +x` on hooks
- **VALIDATE**:
  ```bash
  ls -la .git/hooks/pre-commit
  ls -la .git/hooks/pre-push
  ```

### Task 5: Test Git Hook Blocks Bugs
- **ACTION**: Verify pre-commit hook blocks intentional bug
- **TARGET**: .git/hooks/pre-commit
- **IMPLEMENT**: Create test file with bug, attempt commit
- **PATTERN**: Negative test — hook should reject
- **IMPORTS**: None
- **GOTCHA**: Clean up test file after (git reset + rm)
- **VALIDATE**:
  ```bash
  echo "const x = undefined; x.foo();" > test-bug.ts
  git add test-bug.ts
  git commit -m "test: intentional bug"
  # Expected: Hook blocks commit
  git reset HEAD test-bug.ts
  rm test-bug.ts
  ```

### Task 6: Add UBS to Swarm Worker Guardrails
- **ACTION**: Update swarm worker agents to require UBS scan
- **TARGET**: .opencode/agents/swarm-worker-*.md
- **IMPLEMENT**: Add UBS scan step to worker workflow
- **PATTERN**: Add validation step before swarm_complete()
- **IMPORTS**: None
- **GOTCHA**: Keep guardrails concise — one paragraph per agent
- **VALIDATE**: Read updated agent files, confirm UBS requirement present

### Task 7: Test Agent Mentions UBS
- **ACTION**: Verify AI acknowledges UBS requirement
- **TARGET**: Agent behavior
- **IMPLEMENT**: Ask AI to implement a simple feature, observe if UBS mentioned
- **PATTERN**: Behavioral test
- **IMPORTS**: None
- **GOTCHA**: May need /prime to reload agent context
- **VALIDATE**: AI mentions running `ubs` before marking task complete

### Task 8: Create .ubs-ignore (if needed)
- **ACTION**: Add exclusions for false positives
- **TARGET**: .ubs-ignore
- **IMPLEMENT**: Create file with exclusions if scan found false positives
- **PATTERN**: One path per line, comments with #
- **IMPORTS**: None
- **GOTCHA**: Only add if actual false positives found
- **VALIDATE**: `ubs .` — excluded files not scanned

### Task 9: Document in memory.md
- **ACTION**: Record setup decisions and gotchas
- **TARGET**: memory.md
- **IMPLEMENT**: Add UBS setup section with date, decisions, gotchas
- **PATTERN**: Structured memory entry
- **IMPORTS**: None
- **GOTCHA**: Create file if doesn't exist
- **VALIDATE**: Read memory.md, confirm UBS section present

---

## Validation Commands

Run in order after implementation:

```bash
# 1. UBS installation
ubs --version
ubs doctor

# 2. Initial scan
ubs .

# 3. Git hooks exist
ls -la .git/hooks/pre-commit .git/hooks/pre-push

# 4. Agent guardrails updated
grep -A 5 "UBS\|bug scanner" .opencode/agents/swarm-worker-*.md

# 5. Memory documented
grep -A 10 "UBS\|Bug Scanner" memory.md
```

---

## Acceptance Criteria

- [ ] UBS installed and `ubs doctor` passes
- [ ] Initial scan completes with 0 critical issues (or bugs fixed)
- [ ] Git pre-commit hook exists and is executable
- [ ] Git hook blocks intentional bug (tested)
- [ ] All 4 swarm worker agents mention UBS scan requirement
- [ ] AI mentions UBS when asked to implement features
- [ ] memory.md documents UBS setup with gotchas
- [ ] `.ubs-ignore` created only if false positives found (optional)

---

## Completion Checklist

- [ ] All 9 tasks completed
- [ ] All validation commands pass
- [ ] No divergences from plan (or documented)
- [ ] Ready for /commit

---

## Testing Strategy

| Test | Method | Expected |
|------|--------|----------|
| UBS installed | `ubs --version` | Version number |
| UBS healthy | `ubs doctor` | All checks pass |
| Scan works | `ubs .` | Summary with 0 critical |
| Hook installed | `ls .git/hooks/pre-commit` | File exists, executable |
| Hook blocks | Commit test bug | Rejected with error |
| Guardrails added | `grep UBS swarm-worker-*.md` | UBS mentioned |
| AI behavior | Ask AI to implement | Mentions UBS scan |

---

## Gotchas & Risks

| Risk | Mitigation |
|------|------------|
| Windows curl fails | Use PowerShell Invoke-WebRequest or WSL |
| UBS not in PATH | Reinstall or add to PATH manually |
| Git hook not executable | `chmod +x .git/hooks/pre-commit` |
| False positives | Add to `.ubs-ignore` |
| AI ignores guardrails | /prime to reload context |

---

## Handoff Notes

**Carry Forward**:
- UBS installation path (global)
- Git hook locations (.git/hooks/)
- Agent guardrail patterns (reuse for new agents)

**Watch For**:
- UBS version updates (check monthly)
- New false positives (add to .ubs-ignore)
- AI forgetting guardrails (re-prime if needed)

---

<!-- PLAN-VERSION: 1.0 -->
<!-- CREATED: 2026-02-23 -->
<!-- FEATURE: swarm-ubs-setup -->
