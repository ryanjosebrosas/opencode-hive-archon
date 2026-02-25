# /planning: Ultima Second Brain - Hybrid Retrieval Foundation Brick

Generated: 2026-02-25
Planning mode: discovery + research + architecture synthesis only (no code implementation)
Research scope: local repository analysis only
Primary source analyzed: `C:\Users\Utopia\Documents\MEGA\Template`

---

## Phase 0 - MVP Discovery and Alignment

## MVP status

- `mvp.md` exists in planning workspace and was revised with your feedback.
- MVP now explicitly includes:
  - Mem0-style repeat memory behavior
  - Reranking and fallback in retrieval
  - Hybrid memory architecture
  - Medium-flexible outputs (LinkedIn, blog, YouTube, future channels)

## Confirmed big idea (locked)

`Ultima Second Brain` is a personal learning OS that prioritizes persistent, accurate context retrieval and synthesis, then routes that context into specialized output flows so learning compounds and output quality scales.

## MVP-to-feature alignment

Requested feature is aligned as the first foundation brick:

- Brick goal: establish retrieval trust layer before broad integrations.
- Why first: without retrieval reliability, all downstream agents and mediums degrade.

---

## Phase 1 - Feature Understanding

## Feature framing

Feature: Hybrid retrieval foundation (RAG + semantic + episodic + pattern memory) with reranker and fallback contract.

## Feature metadata

- Feature Type: New Capability
- Complexity: High
- Primary Systems Affected:
  - `.claude/commands/plan.md`
  - `.claude/commands/ask.md`
  - `.claude/commands/recall.md`
  - `.claude/commands/work.md`
  - `.claude/skills/memory-recall/SKILL.md`
  - `memory/patterns/INDEX.md`
  - `memory/examples/INDEX.md`
  - `brain-health/INDEX.md`

## User story

As a lifelong learner,
I want retrieval to consistently produce accurate, medium-relevant context with fallback support,
So that I can create better outputs faster across LinkedIn, blog, YouTube, and future channels.

## Problem statement

The current system has strong memory assets and command workflows, but retrieval behavior is fragmented and only partially formalized. Ranking exists, but reranking and fallback are not standardized. This creates inconsistent context quality and weaker trust in outputs.

## Solution statement

Define and align a contract-first hybrid retrieval layer that all command paths use:

1. multi-store retrieval
2. normalized candidate set
3. reranking pass
4. deterministic fallback chain
5. standardized `context_packet` output
6. medium-aware routing to pattern/example stores

Checkpoint result: Phase 1 framing is complete and consistent with your latest direction.

---

## Phase 2 - Codebase Intelligence Gathering (Research)

## 2.1 Structure and workflow research findings

Evidence:

- Core workflow is explicitly `/plan -> /work -> /review -> /learn`.
  - `C:\Users\Utopia\Documents\MEGA\Template\README.md:49`
  - `C:\Users\Utopia\Documents\MEGA\Template\AGENTS.md:110`

- Memory architecture split is explicit and reusable for retrieval layer design:
  - semantic-like stores under `memory/`
  - episodic stores under `experiences/`
  - health telemetry under `brain-health/`
  - `C:\Users\Utopia\Documents\MEGA\Template\README.md:69`

## 2.2 Retrieval behavior research findings

Existing ranking logic already documented:

- `/recall` ranking dimensions (direct match, confidence relevance, recency, success signal)
  - `C:\Users\Utopia\Documents\MEGA\Template\.claude\commands\recall.md:54`

- memory-recall skill includes multi-memory search and rank criteria
  - `C:\Users\Utopia\Documents\MEGA\Template\.claude\skills\memory-recall\SKILL.md:43`
  - `C:\Users\Utopia\Documents\MEGA\Template\.claude\skills\memory-recall\SKILL.md:84`

Gap identified:

- No explicit shared retrieval contract document
- No normalized output payload shared by all commands
- No deterministic fallback policy documented across commands

## 2.3 Pattern and medium coverage research findings

Strong LinkedIn readiness:

- Hook library and structure references
  - `C:\Users\Utopia\Documents\MEGA\Template\memory\examples\linkedin\hooks-that-work.md:1`
  - `C:\Users\Utopia\Documents\MEGA\Template\memory\examples\linkedin\README.md:39`

- Process and messaging patterns available
  - `C:\Users\Utopia\Documents\MEGA\Template\memory\patterns\content-patterns.md:7`
  - `C:\Users\Utopia\Documents\MEGA\Template\memory\patterns\messaging-patterns.md:18`

Gap identified:

- Blog and YouTube example categories not equally structured in index-driven way
  - `C:\Users\Utopia\Documents\MEGA\Template\memory\examples\INDEX.md:42`

## 2.4 Confidence and metrics research findings

- Confidence taxonomy exists and should be reused for reranking features:
  - `C:\Users\Utopia\Documents\MEGA\Template\memory\patterns\INDEX.md:111`

- Brain health has quality and confidence files, but no retrieval-specific KPI file:
  - `C:\Users\Utopia\Documents\MEGA\Template\brain-health\INDEX.md:21`
  - `C:\Users\Utopia\Documents\MEGA\Template\brain-health\quality-metrics.md:13`
  - `C:\Users\Utopia\Documents\MEGA\Template\brain-health\pattern-confidence.md:13`

## 2.5 Existing usage evidence

Growth log shows real pattern extraction history and strong LinkedIn concentration, validating your concern about channel breadth:

- `C:\Users\Utopia\Documents\MEGA\Template\brain-health\growth-log.md:18`

Checkpoint result: research confirms architecture opportunity and supports hybrid retrieval as the right first brick.

---

## Phase 3 - Local Documentation and Constraints

## Relevant documentation (local only)

- `C:\Users\Utopia\Documents\MEGA\Template\README.md`
  - Why: baseline user workflow and command expectations
- `C:\Users\Utopia\Documents\MEGA\Template\AGENTS.md`
  - Why: codex-specific operational behavior and command contract expectations
- `C:\Users\Utopia\Documents\MEGA\Template\.claude\commands\plan.md`
  - Why: planning command context-loading behavior to be upgraded
- `C:\Users\Utopia\Documents\MEGA\Template\.claude\commands\ask.md`
  - Why: fast-path retrieval flow
- `C:\Users\Utopia\Documents\MEGA\Template\.claude\commands\recall.md`
  - Why: direct ranking baseline and no-result behavior
- `C:\Users\Utopia\Documents\MEGA\Template\.claude\commands\work.md`
  - Why: context handoff to execution
- `C:\Users\Utopia\Documents\MEGA\Template\.claude\skills\memory-recall\SKILL.md`
  - Why: retrieval/ranking logic reference
- `C:\Users\Utopia\Documents\MEGA\Template\memory\patterns\INDEX.md`
  - Why: confidence signals for ranking
- `C:\Users\Utopia\Documents\MEGA\Template\memory\examples\INDEX.md`
  - Why: medium category registration point
- `C:\Users\Utopia\Documents\MEGA\Template\brain-health\INDEX.md`
  - Why: retrieval KPI registration point

## Constraints and gotchas

- Preserve `/plan -> /work -> /review -> /learn` mental model.
- Keep command text concise; put detail in architecture docs.
- Do not hardcode provider-specific assumptions where adapter pattern is better.
- Keep retrieval behavior deterministic and explainable.

---

## Phase 4 - Strategic Design and Synthesis

## Architecture direction

Use a contract-first retrieval architecture with these blocks:

1. Source adapters (local first, external-ready)
2. Candidate normalization
3. Reranking layer
4. Fallback policy engine
5. `context_packet` payload
6. Channel router (LinkedIn/blog/YouTube/future)

## Reranking criteria

- Confidence weight (LOW/MEDIUM/HIGH mapped numerically)
- Recency weight
- Query relevance weight
- Channel fit weight
- Proven success signal weight (where data exists)

## Fallback policy

1. Primary retrieval
2. Threshold check
3. Controlled broadening pass
4. Low-confidence best-effort response
5. No-result guidance with explicit next actions

## Risks and mitigations

- Risk: command docs diverge from contract
  - Mitigation: single architecture doc + mandatory cross-reference section in each command
- Risk: medium mismatch in retrieval
  - Mitigation: channel-fit scoring + dedicated `channel-patterns.md`
- Risk: overfitting to LinkedIn data
  - Mitigation: bootstrap blog and YouTube example folders now
- Risk: no quality observability
  - Mitigation: `brain-health/retrieval-quality.md`

PRD direction statement:

This is the implementation bridge from MVP to delivery for Brick 1 (retrieval trust layer) before broader connector rollout.

Checkpoint result: direction is finalized based on your provided inputs and local research.

---

## Phase 5 - Execution Plan Output

Output plan file (PRD-style) already created:

- `.agents/plans/build-hybrid-retrieval-foundation-brick.md`

This `/planning` artifact (current file) is the research-backed bridge document.

---

## Task Graph (Atomic, ordered)

### 1) CREATE docs architecture contract

- Target: `docs/architecture/hybrid-retrieval-contract.md`
- Implement: unified retrieval contract, scoring model, fallback thresholds, `context_packet` schema
- Validate: `rg "context_packet|rerank|fallback|threshold" "C:/Users/Utopia/Documents/MEGA/Template/docs/architecture/hybrid-retrieval-contract.md"`

### 2) CREATE fallback operational playbook

- Target: `memory/procedural/retrieval-fallback-playbook.md`
- Implement: deterministic decision tree for degraded retrieval
- Validate: `rg "Decision Tree|Fallback|Threshold" "C:/Users/Utopia/Documents/MEGA/Template/memory/procedural/retrieval-fallback-playbook.md"`

### 3) CREATE channel pattern registry

- Target: `memory/patterns/channel-patterns.md`
- Implement: channel-specific pattern index with confidence and source refs
- Validate: `rg "Channel|Confidence|Source" "C:/Users/Utopia/Documents/MEGA/Template/memory/patterns/channel-patterns.md"`

### 4) CREATE medium example categories

- Targets:
  - `memory/examples/blog/README.md`
  - `memory/examples/youtube/README.md`
- Implement: metadata templates and quality criteria similar to LinkedIn examples
- Validate:
  - `rg "Why This Works|Patterns to Extract" "C:/Users/Utopia/Documents/MEGA/Template/memory/examples/blog/README.md"`
  - `rg "hook|segment|CTA|Patterns to Extract" "C:/Users/Utopia/Documents/MEGA/Template/memory/examples/youtube/README.md"`

### 5) CREATE retrieval quality metrics file

- Target: `brain-health/retrieval-quality.md`
- Implement: KPI table (precision proxy, fallback rate, no-result rate, channel-fit score)
- Validate: `rg "fallback rate|no-result|channel-fit|precision" "C:/Users/Utopia/Documents/MEGA/Template/brain-health/retrieval-quality.md"`

### 6) UPDATE command docs to contract

- Targets:
  - `.claude/commands/recall.md`
  - `.claude/commands/plan.md`
  - `.claude/commands/ask.md`
  - `.claude/commands/work.md`
- Implement: consume shared retrieval contract + `context_packet`
- Validate: `rg "retrieval contract|context_packet|rerank|fallback" "C:/Users/Utopia/Documents/MEGA/Template/.claude/commands/*.md"`

### 7) UPDATE skill doc to contract

- Target: `.claude/skills/memory-recall/SKILL.md`
- Implement: align ranking + fallback wording to contract terminology
- Validate: `rg "context_packet|rerank|fallback" "C:/Users/Utopia/Documents/MEGA/Template/.claude/skills/memory-recall/SKILL.md"`

### 8) UPDATE indexes and top-level docs

- Targets:
  - `memory/examples/INDEX.md`
  - `brain-health/INDEX.md`
  - `README.md`
  - `AGENTS.md`
- Implement: register new files and architecture references
- Validate: `rg "hybrid retrieval|retrieval-quality|channel" "C:/Users/Utopia/Documents/MEGA/Template/README.md" "C:/Users/Utopia/Documents/MEGA/Template/AGENTS.md" "C:/Users/Utopia/Documents/MEGA/Template/brain-health/INDEX.md"`

---

## Validation Pyramid

### Level 1 - Syntax/style

Run path and keyword integrity checks (`ls`, `rg`) for all created/updated docs.

### Level 2 - Unit scope

Per-file keyword assertions for contract terms.

### Level 3 - Integration scope

Cross-command consistency check for retrieval flow terms.

### Level 4 - Manual validation

Scenario walkthroughs:

1. LinkedIn post request
2. Blog draft request
3. YouTube script request
4. No-match request

### Level 5 - Optional extension

Adapter readiness checklist for Supabase, Mem0-style memory, Notion, Obsidian, email.

---

## Acceptance Criteria

- [ ] Shared retrieval contract exists and is referenced by affected commands
- [ ] Reranking criteria and fallback chain are explicit and deterministic
- [ ] `context_packet` schema is defined and consistently referenced
- [ ] Blog and YouTube memory/example structures are added
- [ ] Retrieval KPIs are defined in brain-health docs
- [ ] Existing 4-command workflow remains intact

---

## Complexity, Risks, Confidence

- Complexity: High
- Key risk: doc drift between command/skill specs and architecture contract
- Mitigation: architecture doc as source of truth + command-level cross-reference block
- Confidence for one-pass execution success: 8.9/10

---

## Next PIV Loop Suggestion

After Brick 1, execute Brick 2:

- Supabase + Mem0 adapter mapping spec
- source-specific normalization rules
- retrieval quality gates before orchestration expansion
