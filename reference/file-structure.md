```
CLAUDE.md                              # Layer 1: Global rules (slim, @references)
README.md                              # Public-facing project README with PIV Loop diagrams
AGENTS.md                              # Agent guidance for AI assistants
LICENSE                                # MIT License
.gitignore                             # Protects secrets, personal config, plans
memory.md                              # Cross-session memory (optional, from MEMORY-TEMPLATE.md)
mvp.md                                 # Product vision and scope (Ultima Second Brain)

sections/                              # Auto-loaded rule sections (every session)
  01_core_principles.md                #   YAGNI, KISS, DRY, Limit AI Assumptions, ABP
  02_piv_loop.md                       #   Plan, Implement, Validate methodology (slim)
  03_context_engineering.md            #   4 Pillars: Memory, RAG, Prompts, Tasks
  04_git_save_points.md                #   Commit plans before implementing
  05_decision_framework.md             #   When to proceed vs ask

reference/                             # On-demand guides (loaded when needed)
  archon-workflow.md                   #   Archon task management & RAG workflow
  layer1-guide.md                      #   How to build CLAUDE.md for real projects
  file-structure.md                    #   This file — project directory layout
  system-foundations.md                #   System gap, mental models, self-assessment
  piv-loop-practice.md                 #   PIV Loop in practice, 4 Pillars, validation
  global-rules-optimization.md         #   Modular CLAUDE.md, Two-Question Framework
  command-design-framework.md          #   Slash commands, INPUT→PROCESS→OUTPUT
  implementation-discipline.md         #   Execute command, meta-reasoning, save states
  validation-discipline.md             #   5-level pyramid, code review, system review
  subagents-deep-dive.md               #   Subagents, context handoff, agent design framework
  sustainable-agent-architecture.md    #   Strict gates G1-G5, Python-first portability
  python-first-portability-guide.md    #   Framework-agnostic contract patterns

templates/
  PRD-TEMPLATE.md                      # Template for Layer 1 PRD (what to build)
  STRUCTURED-PLAN-TEMPLATE.md          # Template for Layer 2 plans (per feature)
  SUB-PLAN-TEMPLATE.md                 # Individual sub-plan template (500-700 lines, self-contained)
  VIBE-PLANNING-GUIDE.md               # Example prompts for vibe planning
  PLAN-OVERVIEW-TEMPLATE.md            # Master file for decomposed plan series (overview + index)
  MEMORY-TEMPLATE.md                   # Template for project memory (cross-session context)
  COMMAND-TEMPLATE.md                  # How to design new slash commands
  AGENT-TEMPLATE.md                    # How to design new subagents

requests/
  .gitkeep                             # Preserves directory in git (plans are gitignored)
  {feature}-plan.md                    # Layer 2: Feature plans go here
  execution-reports/                   # Implementation reports (saved after /execute)
    {feature}-report.md                #   Execution report with validation results

backend/                               # Backend application (Second Brain implementation)
  pyproject.toml                       # Python project config (dependencies, pytest, ruff, mypy)
  src/second_brain/
    __init__.py                        #   Package init
    contracts/                         #   Typed contract models
      __init__.py                      #     Package init
      context_packet.py                #     ContextCandidate, ConfidenceSummary, ContextPacket, NextAction
    orchestration/                     #   Retrieval routing and fallback logic
      __init__.py                      #     Package init
      retrieval_router.py              #     Deterministic provider selection, Mem0 rerank policy
      fallbacks.py                     #     Branch emitters (EMPTY_SET, LOW_CONFIDENCE, etc.)
    agents/                            #   Agent implementations
      __init__.py                      #     Package init
      recall.py                        #     Recall agent for retrieval orchestration
    services/                          #   Service layer implementations
      __init__.py                      #     Package init
      memory.py                        #     Memory service (Mem0 provider)
      voyage.py                        #     Voyage AI reranking service
      graphiti_memory.py               #     Graph memory adapter (optional)
      storage.py                       #     Hybrid retrieval and data access
    schemas.py                         # Pydantic schemas (shared)
    deps.py                            # Dependency injection helpers
    mcp_server.py                      # MCP tool exposure

docs/                                  # Architecture documentation
  architecture/
    conversational-retrieval-contract.md      # Runtime contract, branch semantics, output guarantees
    retrieval-planning-separation.md          # Responsibility boundaries, data flow
    retrieval-overlap-policy.md               # Rerank policy, Mem0 duplicate prevention

tests/                                 # Test files
  test_context_packet_contract.py      # Contract model and fallback emitter tests
  test_retrieval_router_policy.py      # Router determinism and Mem0 policy tests
  test_recall.py                       # Recall agent integration tests (TODO)
  test_memory.py                       # Memory service tests (TODO)
  test_mcp.py                          # MCP tool compatibility tests (TODO)

.opencode/                             # OpenCode configuration
  commands/                            # Slash commands
    prime.md                           #   /prime — load codebase context
    planning.md                        #   /planning — create implementation plan
    execute.md                         #   /execute — implement from plan
    commit.md                          #   /commit — conventional git commit
    code-review.md                     #   /code-review — technical review
    code-loop.md                       #   /code-loop — automated review → fix → commit
    system-review.md                   #   /system-review — divergence analysis
  agents/                              # Custom subagents
    research-codebase.md               #   Codebase exploration
    research-external.md               #   Documentation research
    research-ai-patterns.md            #   AI/LLM integration patterns
    code-review.md                     #   Generalist code review
    plan-validator.md                  #   Plan validation
    memory-curator.md                  #   Memory suggestions
  skills/                              # Agent skills
    planning-methodology/              #   6-phase systematic planning
      SKILL.md                         #     Entry point

.claude/                               # Claude Code compatibility (symlinks to .opencode)
  commands/                            #   Symlinked to .opencode/commands/
  agents/                              #   Symlinked to .opencode/agents/
  settings.json                        #   Hooks configuration
```

## Directory Purposes

### Core Directories

| Directory | Purpose | Git Tracked |
|-----------|---------|-------------|
| `sections/` | Auto-loaded methodology rules | Yes |
| `reference/` | On-demand deep guides | Yes |
| `templates/` | Reusable plan/doc templates | Yes |
| `requests/` | Feature plans (per-session) | No (gitignored) |
| `backend/` | Second Brain application | Yes |
| `docs/` | Architecture documentation | Yes |
| `tests/` | Test files | Yes |
| `.opencode/` | OpenCode config (commands, agents) | Yes |
| `.claude/` | Claude Code compatibility | Yes |

### Backend Structure

| Module | Purpose | Key Files |
|--------|---------|-----------|
| `contracts/` | Typed output contracts | `context_packet.py` |
| `orchestration/` | Routing and fallbacks | `retrieval_router.py`, `fallbacks.py` |
| `agents/` | Agent implementations | `recall.py` |
| `services/` | Provider adapters | `memory.py`, `voyage.py`, `graphiti_memory.py` |

### Test Structure

| Test File | Coverage | Status |
|-----------|----------|--------|
| `test_context_packet_contract.py` | Contract models, fallback emitters | 28 tests, passing |
| `test_retrieval_router_policy.py` | Router determinism, Mem0 policy | 13 tests, passing |
| `test_recall.py` | Recall agent integration | TODO |
| `test_memory.py` | Memory service | TODO |
| `test_mcp.py` | MCP tool compatibility | TODO |

## File Naming Conventions

- **Plans**: `requests/{feature-name}-plan.md` (e.g., `hybrid-retrieval-conversational-orchestrator-plan.md`)
- **Reports**: `requests/execution-reports/{feature-name}-report.md`
- **Architecture docs**: `docs/architecture/{topic}.md`
- **Test files**: `tests/test_{module_name}.py`
- **Python modules**: snake_case (e.g., `retrieval_router.py`)
- **OpenCode commands**: kebab-case (e.g., `code-review.md`)
- **Subagents**: kebab-case (e.g., `research-codebase.md`)
