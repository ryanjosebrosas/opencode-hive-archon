---
description: Prime agent with codebase understanding
agent: build
---

# Prime: Load Project Context

Load project context using parallel agents for speed and context isolation. Each agent analyzes one aspect and returns its formatted report section. Only the assembled report stays in this conversation.

## Step 1: Detect Context Mode

Check for code directories using a **single** Glob call with brace expansion:

```
{src,app,frontend,backend,lib,api,server,client}/**
```

**If ANY files found** → **Codebase Mode** (go to Step 2B)
**If no files found** → **System Mode** (go to Step 2A)

---

## Step 2A: System Mode — Launch 5 Parallel Agents

Launch ALL of the following Task agents **simultaneously**:

### Agent 1: Commands Inventory (Sonnet)
- **subagent_type**: `general`
- **description**: "Inventory slash commands"
- **prompt**: |
    You are analyzing an OpenCode project's available commands.
    Run: `grep -r "^description:" .opencode/commands/ 2>/dev/null` via Bash to get all command descriptions.
    Also check for skills: `ls .opencode/skills/ 2>/dev/null` via Bash.

    Return ONLY this formatted section (nothing else):

    ## Available Resources
    ### Commands
    | Command | Purpose |
    |---------|---------|
    {one row per command found}

    ### Agents
    (Skip this section — another agent handles it)

    ### Skills
    {list any skills found, or "None" if empty}

### Agent 2: Agents Inventory (Sonnet)
- **subagent_type**: `general`
- **description**: "Inventory subagents"
- **prompt**: |
    You are analyzing an OpenCode project's available agents.
    Read the file `.opencode/agents/README.md` for the complete agent catalog.
    Extract each agent's name, category, and one-line purpose.

    Return ONLY this formatted section (nothing else):

    ### Agents
    - **Research**: {agent names and purposes}
    - **Code Review**: {agent names and purposes}
    - **Utility**: {agent names and purposes}
    - **Specialist**: {agent names and purposes}

### Agent 3: Project Structure (Haiku)
- **subagent_type**: `explore`
- **description**: "Map project structure"
- **prompt**: |
    You are mapping a methodology/documentation project's structure.
    Use Glob to find all .md files in: root, sections/, reference/, templates/, requests/.
    Identify the key directories and their purposes.

    Return ONLY this formatted section (nothing else):

    ## Detection
    - **Mode**: System
    - **Signals**: {what you found — no code directories, only docs/templates}

    ## Project Overview
    - **Type**: {project description based on what you found}
    - **Tech Stack**: {languages, frameworks, tools — e.g., "Markdown, OpenCode CLI, Git"}
    - **Structure**: {key directories and their purposes, 1 line each}

### Agent 4: Memory Context (Haiku)
- **subagent_type**: `explore`
- **description**: "Read project memory"
- **prompt**: |
    You are extracting cross-session memory context.
    Read the file `memory.md` if it exists. If it doesn't exist, note that.

    Return ONLY this formatted section (nothing else):

    ## Memory Context
    - **Last Session**: {most recent date from Session Notes, or "No memory.md found"}
    - **Key Decisions**: {bullet list from Key Decisions section, or "None recorded"}
    - **Active Patterns**: {from Architecture Patterns section, or "None recorded"}
    - **Gotchas**: {from Gotchas section, or "None recorded"}
    - **Memory Health**: {if last session date is >7 days ago, warn "Stale — last updated {date}". Otherwise "Fresh"}

### Agent 5: Git State (Haiku)
- **subagent_type**: `explore`
- **description**: "Get git state"
- **prompt**: |
    You are checking the current git state of a project.
    Run via Bash: `git log -10 --oneline` and `git status`

    Return ONLY this formatted section (nothing else):

    ## Current State
    - **Branch**: {current branch name}
    - **Status**: {clean/dirty, summary of changes if any}
    - **Recent Work**: {list each of the last 10 commits as "- `hash` message"}

---

## Step 2B: Codebase Mode — Launch 6 Parallel Agents

Launch ALL of the following Task agents **simultaneously**:

### Agent 1: Architecture & Structure (Sonnet)
- **subagent_type**: `general`
- **description**: "Analyze project architecture"
- **prompt**: |
    You are analyzing a codebase's architecture and structure.
    Run via Bash: `git ls-files` to list tracked files.
    Run via Bash: `tree -L 3 -I 'node_modules|__pycache__|.git|dist|build' 2>/dev/null || ls -la`
    Detect architectural layers by checking for these directory patterns:
    - Routing/API: routes/, pages/, app/ (Next.js), controllers/, api/
    - Business Logic: services/, use-cases/, domain/, agents/
    - Data Layer: models/, schemas/, prisma/, migrations/, entities/
    - Middleware: middleware/, guards/, interceptors/
    - UI: components/, views/, layouts/, hooks/
    - Utilities: utils/, helpers/, lib/, common/
    - Config: config/, env/
    - Tests: tests/, test/, __tests__/, spec/

    Return ONLY this formatted section (nothing else):

    ## Detection
    - **Mode**: Codebase
    - **Signals**: {what code directories you found}

    ## Architecture
    - **Entry Points**: {main files found — e.g., src/index.ts, main.py}
    - **Layers**: {which architectural layers exist and how they connect}
    - **Data Flow**: {how data moves through the system based on layers found}
    - **Key Directories**: {important dirs and their purposes}

### Agent 2: Tech Stack & Dependencies (Sonnet)
- **subagent_type**: `general`
- **description**: "Analyze tech stack and dependencies"
- **prompt**: |
    You are analyzing a codebase's tech stack and dependencies.
    Read the package manifest: look for package.json, pyproject.toml, Cargo.toml, go.mod, or similar.
    Extract: language, framework, key dependencies with versions, dev dependencies, available scripts/commands, package manager, testing framework.

    Return ONLY these formatted sections (nothing else):

    ## Tech Stack
    - **Language**: {language and version if detectable}
    - **Framework**: {primary framework and version}
    - **Database**: {DB technology if found, or "None detected"}
    - **Testing**: {test framework and approach}
    - **Build Tools**: {package manager, bundler, etc.}

    ## Dependencies & Tooling
    - **Key Dependencies**: {top 5-10 with versions}
    - **Dev Dependencies**: {linter, formatter, type checker}
    - **Scripts**: {available npm/make/task commands}

### Agent 3: Code Conventions (Sonnet)
- **subagent_type**: `general`
- **description**: "Identify code conventions"
- **prompt**: |
    You are identifying a codebase's conventions and patterns.
    Read 1-2 representative service or controller files (pick files that look like core business logic).
    Read the main entry point if present (main.py, index.ts, app.py, server.ts).
    Also read schema/model definitions if present (prisma/schema.prisma, models.py, schema.graphql).
    Skip .opencode/ directory contents — those are tooling, not the app.
    Limit: Read at most 4 files total.

    Return ONLY these formatted sections (nothing else):

    ## Project Overview
    - **Purpose**: {what this application does, based on what you read}
    - **Version**: {from manifest if available, or "Not specified"}

    ## Core Principles
    - **Naming**: {conventions observed — camelCase, snake_case, PascalCase, etc.}
    - **Error Handling**: {pattern used — try/catch, Result types, error middleware, etc.}
    - **Code Organization**: {how files/modules are structured}
    - **Testing Approach**: {unit, integration, e2e — what's present based on test files found}

### Agent 4: README (Haiku)
- **subagent_type**: `explore`
- **description**: "Read project README"
- **prompt**: |
    Read README.md if it exists. If no README exists, return "No README.md found."

    Return ONLY this formatted section (nothing else):

    ### README Summary
    - **Purpose**: {what this project does — 1 sentence}
    - **Key Capabilities**: {main features — comma-separated list}
    - **Setup**: {setup instructions summary, or "None specified"}

### Agent 5: Memory Context (Haiku)
- **subagent_type**: `explore`
- **description**: "Read project memory"
- **prompt**: |
    You are extracting cross-session memory context.
    Read the file `memory.md` if it exists. If it doesn't exist, note that.

    Return ONLY this formatted section (nothing else):

    ## Memory Context
    - **Last Session**: {most recent date from Session Notes, or "No memory.md found"}
    - **Key Decisions**: {bullet list from Key Decisions section, or "None recorded"}
    - **Active Patterns**: {from Architecture Patterns section, or "None recorded"}
    - **Gotchas**: {from Gotchas section, or "None recorded"}
    - **Memory Health**: {if last session date is >7 days ago, warn "Stale". Otherwise "Fresh"}

### Agent 6: Git State (Haiku)
- **subagent_type**: `explore`
- **description**: "Get git state"
- **prompt**: |
    You are checking the current git state of a project.
    Run via Bash: `git log -10 --oneline` and `git status`

    Return ONLY this formatted section (nothing else):

    ## Current State
    - **Branch**: {current branch name}
    - **Status**: {clean/dirty, summary of changes if any}
    - **Recent Work**: {list each of the last 10 commits as "- `hash` message"}

---

## Step 3: Assemble Report

After ALL agents return, assemble the Prime Context Report:

1. Start with `# Prime Context Report`
2. Add each agent's returned section in this order:
   - **System Mode**: Detection → Project Overview → Current State → Memory Context → Available Resources (Commands + Agents + Skills) → Suggested Next Steps
   - **Codebase Mode**: Detection → Project Overview (merge Agent 3's overview with Agent 4's README Summary into one section) → Architecture → Tech Stack → Core Principles → Dependencies & Tooling → Current State → Memory Context → Suggested Next Steps
3. Add a `## Suggested Next Steps` section — synthesize from Current State + Memory Context to suggest what to work on next
4. Present the assembled report to the user

**CRITICAL**: Do NOT re-read files or re-run git commands. The agents already did all the work. Just assemble and present.