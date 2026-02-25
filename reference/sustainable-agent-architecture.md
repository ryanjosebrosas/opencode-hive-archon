# Sustainable Agent Architecture

This guide defines the **non-negotiable principles, strict gates, and bypass protocol** for building sustainable, flexible AI agent systems. All feature plans must declare gate status and comply with the build order unless bypass is approved with evidence.

---

## 1. Non-Negotiable Principles

These principles apply to **every** agent feature, regardless of size or complexity. Violating these principles leads to technical debt, brittle systems, and premature complexity.

### 1.1. Contracts First

**Rule**: Define stable interfaces before implementing integrations.

**What this means**:
- Tool schemas are versioned with SemVer before tool implementation
- Tool result envelopes include: `call_id`, `tool_name`, `status`, `result`, `error`, `meta`
- State schemas include: `state_schema_version`, event log, derived summaries
- Knowledge source contracts are stable even if vector DB, reranker, or chunker changes

**Why**: Enables swapping implementations without rewriting core logic. You can replace mock tools with real APIs, or swap storage backends, without touching the agent loop.

**Gotchas**:
- Don't change field semantics without a migration path
- Don't remove or rename existing fields without version bump
- Additive evolution is safe; breaking changes require version increment

#### Python-first with framework-neutral contracts

Python-first execution is allowed and recommended for fast delivery, but contracts must remain framework-neutral and adapter-based.

Checklist:
- [ ] Domain contracts do not expose framework-native runtime types
- [ ] Contract schemas can be exported as JSON Schema
- [ ] Port boundaries are explicit (runtime, tools, memory, eval)
- [ ] Adapter swap criteria are documented before implementation
- [ ] Eval datasets and grading remain reusable across adapters

### 1.2. Eval-Driven Development

**Rule**: No feature ships without an eval gate.

**What this means**:
- Every feature defines pass/fail criteria before implementation
- Baseline eval suite includes 10-30 golden tasks for core workflows
- Trace grading is used for workflow-level errors (not just final output)
- Evals run in CI as a regression gate

**Why**: Prevents vibe-based iteration. Makes reliability measurable. Catches regressions before they reach production.

**Gotchas**:
- Don't skip eval suite even for "simple" features
- Don't rely solely on LLM judges — include deterministic checks
- Calibrate automated graders with periodic human review

### 1.3. Ingestion Last

**Rule**: Build ingestion pipelines only after agent core, evals, and observability are stable.

**What this means**:
- Phase A: Agent loop + tools + evals (no real ingestion)
- Phase B: State/memory + orchestration (still minimal ingestion)
- Phase C: Production-grade ingestion and governed retrieval

**Why**: Ingestion quality is dominated by document normalization, chunking strategy, metadata, embedding/indexing decisions, and refresh governance. Each has real engineering and cost economics. Microsoft's RAG chunking guidance explicitly calls out that each unique chunking implementation carries engineering/maintenance costs and per-document processing costs.

**Gotchas**:
- Don't build ingestion before you know how the agent will query
- Don't optimize chunking before you have evals to measure retrieval quality
- Start with stubbed KnowledgeSource, replace with real retrieval in Phase C

### 1.4. Complexity Escalation Only When Justified

**Rule**: Start with the lowest complexity that meets requirements.

**What this means**:
- Single-agent baseline before multi-agent orchestration
- Deterministic trimming before summarization
- Direct LLM calls before adding tool orchestration
- Simplest tool that works before adding approval gates

**Why**: Microsoft and Anthropic guidance converge on starting simple. Multi-agent systems add coordination overhead, latency, cost, and failure modes. Early optimism often turns into avoidable abstraction and debugging overhead.

**Gotchas**:
- Don't add orchestration until single-agent limits are proven
- Don't add summarization until deterministic trimming fails
- Document rejected simpler options in every plan

### 1.5. Trace-First Observability

**Rule**: Observability is not optional. Build tracing into the agent loop from day one.

**What this means**:
- Every tool call is logged with structured events
- Agent run traces capture: LLM generations, tool calls, handoffs, guardrails, decisions
- Traces are queryable for debugging and eval grading
- Key metrics are defined per feature (latency, success rate, token cost)

**Why**: Agents fail in multi-step ways. Without traces you can't attribute failure. OpenAI's Agents SDK and Microsoft Foundry both emphasize trace capture for root-cause analysis.

**Gotchas**:
- Don't store traces as raw strings — use structured event format
- Don't skip trace capture for "simple" features
- Define retention policies early (traces accumulate fast)

---

## 2. Strict Gates G1-G5

Every feature plan must declare gate status. Gates are sequential — you cannot pass G3 without passing G1 and G2.

### Gate 1: Contracts

**Pass Criteria**:
- [ ] Tool schemas defined with JSON Schema and versioned (SemVer)
- [ ] Tool result envelope includes required fields: `call_id`, `tool_name`, `status`, `result`, `error`, `meta`
- [ ] State schema includes `state_schema_version` and event log structure
- [ ] KnowledgeSource interface defined (even if implementation is stub)
- [ ] Compatibility notes documented (additive vs breaking changes)

**Evidence Required**: Links to schema files or plan sections with schema definitions.

**Blocks**: No tool implementation until G1 passes.

### Gate 2: Core Reliability

**Pass Criteria**:
- [ ] Agent loop includes iteration/time limits
- [ ] Typed error handling for all failure modes
- [ ] Structured run trace capture (not raw strings)
- [ ] Guardrails defined for high-risk actions
- [ ] No infinite loop risk (explicit termination conditions)

**Evidence Required**: Code snippets or plan sections showing loop control and error handling.

**Blocks**: No multi-step workflows until G2 passes.

### Gate 3: Eval/Regression

**Pass Criteria**:
- [ ] Baseline eval suite defined with 10-30 golden tasks
- [ ] Pass/fail thresholds defined per task type
- [ ] Trace grading approach specified
- [ ] Regression gate will run in CI
- [ ] LLM judge calibrated with human review plan

**Evidence Required**: Eval task examples, grading rubric, CI integration plan.

**Blocks**: No production deployment until G3 passes.

### Gate 4: Observability

**Pass Criteria**:
- [ ] Required trace events defined
- [ ] Key metrics identified (latency, success rate, token cost, etc.)
- [ ] Observability backend identified (even if basic logging)
- [ ] Debugging workflow documented
- [ ] Alert thresholds defined for critical failures

**Evidence Required**: Metrics list, trace event schema, dashboard/alerting plan.

**Blocks**: No scaling (multi-agent, high-traffic) until G4 passes.

### Gate 5: Ingestion/Orchestration Eligibility

**Pass Criteria**:
- [ ] G1-G4 all passed
- [ ] Retrieval contract stable (won't change with ingestion implementation)
- [ ] Foundation maturity score ≥8/10 (see Section 3)
- [ ] Clear requirements for ingestion quality (relevance, freshness, completeness)
- [ ] Rollback plan defined if ingestion quality is poor

**Evidence Required**: Links to passing G1-G4 evals/traces, maturity score justification, ingestion SLA targets.

**Blocks**: This is the final gate. No ingestion pipelines or multi-agent orchestration until G5 passes.

---

## 3. Foundation Maturity Scoring Rubric

Bypass requests require a maturity score. Self-assess using this rubric. Evidence is mandatory — scores without evidence are rejected.

### Scoring Scale

| Score | Maturity Level | What It Means |
|-------|---------------|---------------|
| 1-3 | **Immature** | Foundation not ready for bypass. Build core first. |
| 4-6 | **Developing** | Some pieces in place, but evals/traces incomplete. |
| 7 | **Approaching** | Most pieces present, minor gaps. Proceed with caution. |
| 8-9 | **Mature** | Solid foundation. Bypass justified with evidence. |
| 10 | **Production-Proven** | Battle-tested in production. Full flexibility. |

### Score Criteria

To score yourself, evaluate each dimension:

**Dimension 1: Contracts (0-2 points)**
- 0: No schemas defined
- 1: Informal schemas (no versioning)
- 2: Versioned schemas with compatibility notes

**Dimension 2: Core Reliability (0-2 points)**
- 0: No iteration limits, untyped errors
- 1: Some limits, partial error handling
- 2: Full loop control, typed errors, structured traces

**Dimension 3: Evals (0-2 points)**
- 0: No evals
- 1: Informal tests, no regression gate
- 2: Golden tasks, CI regression gate, trace grading

**Dimension 4: Observability (0-2 points)**
- 0: No tracing, ad-hoc logging
- 1: Basic traces, no metrics
- 2: Structured traces, key metrics, alerting

**Dimension 5: Production Experience (0-2 points)**
- 0: Never deployed
- 1: Deployed but not monitored
- 2: Deployed with monitoring, proven reliability

**Total Score** = sum of all dimensions (max 10).

### Evidence Requirements

For each dimension where you claim points, provide:
- **Links to files** (schemas, eval suites, trace schemas)
- **Links to passing runs** (eval reports, trace logs)
- **Links to monitoring** (dashboards, alert configs)

**Example**:
```
Dimension 2 (Core Reliability): 2/2
Evidence:
- Agent loop with iteration limits: `src/agent/core.py:45-62`
- Typed error envelope: `src/agent/errors.py:10-35`
- Structured trace capture: `src/agent/tracing.py:20-50`
```

---

## 4. Bypass Protocol

Bypass allows skipping the strict build order **only when justified**. This is not a loophole — it's a governed escape hatch for when the foundation is proven.

### When Bypass Is Allowed

Bypass is allowed **only if ALL are true**:
1. Foundation maturity score ≥8/10
2. Existing eval/trace evidence is recent (within last 30 days) and passing
3. Risks and rollback plan are documented
4. Explicit reason why bypass improves delivery without increasing fragility

### Bypass Request Fields

Every bypass request must include these fields in the plan:

**Bypass Requested**: Yes/No

**Bypass Scope**: Which gate(s) are being bypassed? (e.g., "G5 — starting ingestion before G4 complete")

**Foundation Maturity Score**: X/10

**Evidence**: Links to passing evals, traces, schemas that justify the score

**Why Bypass**: Why does skipping the sequence improve delivery? (e.g., "Ingestion is blocking core evals — need real data to test retrieval quality")

**Risks**: What could go wrong? (e.g., "May need to refactor ingestion if core changes")

**Rollback Trigger**: What metric/event triggers rollback? (e.g., "If eval pass rate drops below 70%")

**Rollback Command Path**: What command reverts the change? (e.g., `git revert <commit-hash>`)

**Owner Approval**: User name (required — AI cannot approve bypass)

### Approval Workflow

1. **AI**: Generates bypass request with all fields filled
2. **User**: Reviews and approves (or rejects) in planning conversation
3. **AI**: Proceeds only after explicit user approval
4. **AI**: Documents approval in plan NOTES section

### Bypass Examples

**Example 1: Approved Bypass**
```
Bypass Requested: Yes
Bypass Scope: G5 — starting ingestion before G4 complete
Foundation Maturity Score: 9/10
Evidence:
- G1: `src/schemas/tools.json` (versioned, 3 months stable)
- G2: `src/agent/core.py` (iteration limits, typed errors)
- G3: `tests/evals/golden_tasks.py` (85% pass rate, 30 tasks)
- G4: Basic traces present, metrics defined (no alerts yet)
Why Bypass: Need real data to test retrieval quality evals — stubbed data insufficient
Risks: May need to adjust ingestion if observability reveals issues
Rollback Trigger: If retrieval relevance score <0.7 for 3 consecutive eval runs
Rollback Command Path: `git revert <ingestion-commit-hash>`
Owner Approval: Ryan Jose
```

**Example 2: Rejected Bypass**
```
Bypass Requested: Yes
Bypass Scope: G3 — shipping without eval suite
Foundation Maturity Score: 5/10
Evidence: "Evals are in progress"
Why Bypass: "Need to ship quickly"
Risks: "May have regressions"
Rollback Trigger: "If users report bugs"
Rollback Command Path: "TBD"
Owner Approval: [blank]

REJECTED: Insufficient evidence. Maturity score 5/10 below threshold. "In progress" evals don't count. Define rollback path before requesting bypass.
```

---

## 5. Minimal Metrics + Release Gates

### Required Metrics Per Feature

Every feature must define and track these metrics:

**Workflow Success Metrics**
- Task completion rate (%)
- Human-escalation rate (%)
- Fallback rate (%)

**Tooling Metrics**
- Tool call success rate (%)
- Schema-validation failure rate (%)
- Tool latency (p50, p95, p99)
- Retry rate per tool

**Loop Health Metrics**
- Steps per run (avg, max)
- Iteration-cap hits (count)
- "Stuck" rate (no-progress steps, %)

**Cost Metrics**
- Tokens per run (avg, max)
- Model spend per run
- Tool spend per run

**Quality Metrics**
- Human rating (avg)
- Complaint rate (%)
- Correction rate (%)
- "I don't know" appropriateness (%)

**Retrieval Quality Metrics** (when RAG exists)
- Groundedness (precision of alignment to context)
- Relevance (recall vs ground truth)
- Response completeness (coverage of query intent)
- Retrieval freshness (time from doc update to searchable)

### Release Gates

A feature cannot be released to production without:

**Gate A: Pre-Implementation**
- [ ] Contracts defined and versioned (G1)
- [ ] Bypass approved if skipping sequence

**Gate B: Pre-Integration**
- [ ] Core reliability proven (G2)
- [ ] Eval suite exists with passing baseline (G3)
- [ ] Trace capture working (G4)

**Gate C: Pre-Production**
- [ ] All applicable gates passed (G1-G5)
- [ ] Metrics defined and dashboard exists
- [ ] Alert thresholds configured
- [ ] Rollback plan tested
- [ ] Human review completed (Level 5 validation)

### Release Checklist

Before any production deployment:

```
[ ] G1-G5 status: G1[✓] G2[✓] G3[✓] G4[✓] G5[✓] (or bypass approved)
[ ] Foundation maturity score: X/10
[ ] Eval pass rate: X% (target: ≥80%)
[ ] Trace capture: Working
[ ] Key metrics dashboard: Created
[ ] Alert thresholds: Configured
[ ] Rollback plan: Documented and tested
[ ] Human review: Completed
[ ] Security review: Completed (if applicable)
[ ] Documentation: Updated
```

---

## 6. Build Order Reference

### Default Build Order

```
1. Contracts (G1)
   ↓
2. Core Loop (G2)
   ↓
3. Eval/Trace Gate (G3 + G4)
   ↓
4. Durable State/Memory
   ↓
5. Orchestration (only if needed)
   ↓
6. Ingestion (G5)
```

### Dependency Rules

- **Structure before ingestion**: Build memory/models/schemas before data pipelines
- **Agent core before tool integrations**: Reasoning loop must be stable before adding tools
- **Eval gate before scaling**: No multi-agent or high-traffic without regression gate
- **API contracts before frontend**: Backend interfaces stable before UI implementation

### Component Build Checklist

**Phase A: Agent Core (Weeks 1-3)**
- [ ] AgentCore with iteration/time limits
- [ ] ToolRegistry + 2-3 tools (at least one read-only)
- [ ] Initial eval harness with 10-30 scenarios
- [ ] Basic tracing enabled
- **Success criteria**: ≥80% task success, <2% schema failures, 0 infinite loops

**Phase B: State/Memory (Weeks 4-8)**
- [ ] StateStore + MemoryPolicy (start with trimming)
- [ ] Optional orchestrator (single-agent or small multi-agent)
- [ ] Expanded evals: tool-call accuracy, memory recall
- **Success criteria**: Run time/cost within budget, measurable reduction in retry loops

**Phase C: Ingestion (Weeks 9-16)**
- [ ] Ingestion pipeline with idempotency, caching, monitoring
- [ ] Retrieval quality evals: groundedness, relevance, completeness
- [ ] Governance: RBAC, audit logs, retention, redaction
- **Success criteria**: Retrieval scores meet thresholds, freshness SLA met, 0 critical security incidents

---

## 7. Integration with PIV Loop

### During Planning

Every `/planning` output must include:
- Architecture Slice (which phase this feature belongs to)
- Gate Status (G1-G5 pass/fail)
- Foundation Maturity Score (if bypass requested)
- Bypass Request + Evidence (if applicable)

### During Execution

`/execute` must validate:
- Plan includes ARCHITECTURE GUARDRAILS section
- Gate status is declared
- If bypass was used, evidence is present
- No ingestion/orchestration tasks without G5 pass or approved bypass

### During Validation

Validation must include:
- Gate Compliance: Verify plan includes gates with passing status
- Bypass Audit: If bypass was used, verify evidence is sufficient
- Metric Verification: Confirm defined metrics are captured

---

## 8. FAQ

### Q: Can I skip gates for quick prototypes?

A: No. Prototypes benefit most from discipline — you're exploring unknown territory. Skipping gates leads to throwaway code that becomes production.

### Q: What if a gate is clearly wrong for my use case?

A: Challenge the gate in planning. If there's strong justification, use bypass protocol. But "this is easier" is not sufficient — you need evidence.

### Q: How do I handle legacy systems that don't have gates?

A: Retrofit gates incrementally. Start with G1 (contracts) and G2 (core reliability). Add G3 (evals) as you make changes. Document the migration path.

### Q: Can an AI approve a bypass request?

A: No. Bypass requires human judgment. AI generates the request; human approves.

### Q: What if I bypass and it goes wrong?

A: Execute the rollback plan. Then do a post-mortem: why did the bypass fail? Was evidence insufficient? Were risks underestimated? Update the bypass protocol if needed.

### Q: How often should I expect to use bypass?

A: Rarely. If you're using bypass for more than 10-20% of features, your gates may be too rigid — or you're taking shortcuts. Aim for bypass to be the exception, not the norm.

---

## 9. Reference Files

**Related Guides**:
- `reference/validation-discipline.md` — 5-level validation pyramid
- `reference/piv-loop-practice.md` — PIV loop execution patterns
- `reference/implementation-discipline.md` — Execute phase best practices

**Templates**:
- `templates/STRUCTURED-PLAN-TEMPLATE.md` — Plan template with ARCHITECTURE GUARDRAILS section
- `templates/VIBE-PLANNING-GUIDE.md` — Pre-planning exploration guide

**Commands**:
- `.opencode/commands/planning.md` — Planning command with gate enforcement
- `.opencode/commands/execute.md` — Execution command with gate validation
