```
CLAUDE.md                              # Layer 1: Global rules (slim, @references)
README.md                              # Public-facing project README with PIV Loop diagrams
AGENTS.md                              # Agent guidance for AI assistants
LICENSE                                # MIT License
.gitignore                             # Protects secrets, personal config, plans
memory.md                              # Cross-session memory (optional, from MEMORY-TEMPLATE.md)
sections/                              # Auto-loaded rule sections (every session)
  01_core_principles.md                #   YAGNI, KISS, DRY, Limit AI Assumptions, ABP
  02_piv_loop.md                       #   Plan, Implement, Validate methodology (slim)
  03_context_engineering.md            #   4 Pillars: Memory, RAG, Prompts, Tasks
  04_git_save_points.md                #   Commit plans before implementing
  05_decision_framework.md             #   When to proceed vs ask
  06_archon_workflow.md                #   Archon integration pointer (not @referenced — kept for reference only)
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
  github-workflows/                    #   GitHub Actions workflow templates
    claude-fix.yml                     #     Auto-fix workflow for Claude Code
    claude-fix-coderabbit.yml          #     Auto-fix workflow with CodeRabbit integration
    README.md                          #     Workflow setup instructions
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
  system-reviews/                      # System review output directory
.claude/settings.json                  # Hooks configuration (auto-compact memory recovery)
.claude/commands/                      # Slash commands (reusable prompts)
  agents.md                            #   /agents — generate subagent definition files
  init-c.md                            # /init-c — generate CLAUDE.md for a new project
  prime.md                             # /prime — load codebase context
  planning.md                          # /planning — create implementation plan
  execute.md                           # /execute — implement from plan
  commit.md                            # /commit — conventional git commit
  rca.md                               # /rca — root cause analysis (GitHub issues)
  implement-fix.md                     # /implement-fix — fix from RCA document
  end-to-end-feature.md                # /end-to-end-feature — autonomous workflow
  create-prd.md                        # /create-prd — generate PRD from conversation
  code-review.md                       # /code-review — technical code review
  code-review-fix.md                   # /code-review-fix — fix issues from code review
  execution-report.md                  # /execution-report — implementation report
  system-review.md                     # /system-review — divergence analysis
  create-pr.md                         # /create-pr — create GitHub PR
.claude/skills/                        # Cloud Skills (progressive loading)
  planning-methodology/                #   6-phase planning methodology
    SKILL.md                           #   Entry point + frontmatter (Tier 1+2)
    references/                        #   Detailed docs (Tier 3, on-demand)
      6-phase-process.md               #     Phase-by-phase methodology
      template-guide.md                #     Template section-filling guide
  {skill-name}/                        #   Additional skills follow same structure
    SKILL.md                           #   Entry point + frontmatter (required)
    references/                        #   Detailed docs (loaded on-demand)
    examples/                          #   Example outputs
    scripts/                           #   Executable scripts
.claude/agents/                        # Custom subagents (active, automatically loaded)
  research-codebase.md                 #   Sonnet codebase exploration agent
  research-external.md                 #   Sonnet documentation research agent
  code-review-type-safety.md           #   Type safety reviewer (parallel review)
  code-review-security.md              #   Security vulnerability reviewer
  code-review-architecture.md          #   Architecture & patterns reviewer
  code-review-performance.md           #   Performance & optimization reviewer
  plan-validator.md                    #   Plan structure validation agent
  test-generator.md                    #   Test case suggestion agent
  specialist-devops.md                 #   DevOps & infrastructure specialist
  specialist-data.md                   #   Database & data pipeline specialist
  specialist-copywriter.md             #   UI copy & UX writing specialist
  specialist-tech-writer.md            #   Technical documentation specialist
  README.md                            #   Agent overview and usage guide
```
