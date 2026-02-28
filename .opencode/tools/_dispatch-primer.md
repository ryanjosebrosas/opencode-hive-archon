# Dispatch Primer — Every Dispatched Agent Reads This First

## 1. Project Rules

Read `AGENTS.md` for all project principles, conventions, patterns, and methodology before doing anything else.

---

## 2. Archon MCP — Knowledge Base & Task Tracking

You have access to Archon MCP tools for knowledge retrieval and task tracking. Use them.

### Available Archon tools

| Tool | When to use |
|------|-------------|
| `archon_health_check` | Verify Archon is reachable before starting work |
| `archon_rag_get_available_sources` | List all indexed documentation sources |
| `archon_rag_search_knowledge_base(query, match_count)` | Search docs by keyword (2-5 word queries) |
| `archon_rag_search_code_examples(query, match_count)` | Find reference implementations |
| `archon_rag_read_full_page(page_id)` | Read a full documentation page by ID |
| `archon_find_projects` / `archon_find_tasks` | Find existing project/task records |
| `archon_manage_task` | Update task status (todo → doing → done) |

### When to search Archon

**Before implementing** — run a targeted RAG search if any of these apply:
- You are working with an external library (supabase, pydantic, structlog, voyageai, mem0)
- The plan references a pattern you haven't seen in this codebase
- You are unsure about an API call, method signature, or config option

**During implementation** — search on-demand when you hit an ambiguity:
- Plan reference is unclear or conflicts with what you find in the code
- You need to verify an import path, class name, or config key
- Integration point wasn't covered by the plan

**Keep queries SHORT** (2-5 keywords). Examples:
- `"supabase rpc error"` ✅
- `"pydantic settings env validation"` ✅
- `"how do I configure pydantic settings to read from environment variables"` ❌ (too long)

### How to search

```
1. archon_rag_get_available_sources()          # see what's indexed
2. archon_rag_search_knowledge_base(
     query="supabase connection pool",
     match_count=5
   )                                            # find relevant pages
3. archon_rag_read_full_page(page_id="...")    # read a specific page in full
4. archon_rag_search_code_examples(
     query="pydantic BaseModel validator"
   )                                            # find reference code
```

If Archon is unavailable (health check fails), proceed without it — do not block on Archon.

---

## 3. Task Tracking (if working on a named spec)

If you are implementing a spec from `specs/BUILD_ORDER.md`:

1. `archon_find_projects(query="Second Brain")` — find the project
2. `archon_find_tasks(query="{spec-name}")` — find existing tasks
3. Update task status as you work: `archon_manage_task(action="update", task_id="...", status="doing")`
4. Mark done when complete: `archon_manage_task(action="update", task_id="...", status="done")`

---

## 4. Implementation Standards

- Follow all patterns in `AGENTS.md` and `memory.md`
- `from __future__ import annotations` at top of every Python file
- mypy strict: all functions typed, no `Any` without justification
- ruff clean: no unused imports, consistent formatting
- Run `ruff check` and `mypy --strict` after every file change
- Run `pytest` after all files are in place
- Fix all errors before reporting done
