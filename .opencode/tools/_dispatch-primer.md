# Dispatch Primer — Every Dispatched Agent Reads This First

## STEP 0: Archon Preflight (MANDATORY — do this before anything else)

You have full access to Archon MCP tools. Run these in order before doing any work:

```
1. archon_health_check()                          # confirm Archon is reachable
2. archon_rag_get_available_sources()             # see all indexed docs (Supabase, pgvector, Pydantic, etc.)
3. archon_find_projects(query="Second Brain")     # find the active project
4. archon_find_tasks(query="{spec or task name}") # find existing tasks for this work
```

If Archon is unreachable, log it and continue — but always attempt the preflight first.

---

## STEP 1: RAG Search — Always Run Before Planning or Implementing

Extract 2-3 search terms from your task. Run these in parallel:

```
archon_rag_search_knowledge_base(query="{primary term}", match_count=3)
archon_rag_search_code_examples(query="{implementation term}", match_count=3)
```

For top results (similarity > 0.80), read the full page:
```
archon_rag_read_full_page(page_id="...")
```

**This is not optional.** Archon has indexed Supabase, pgvector, Pydantic, FastAPI, Voyage AI, Mem0, PostgreSQL, and more. Always check before guessing.

Keep queries SHORT — 2-5 keywords:
- `"pg_trgm trigram index"` ✅
- `"supabase rpc security definer"` ✅
- `"how to create a trigram fuzzy search index in postgresql"` ❌ too long

---

## STEP 2: Task Tracking — Register and Update as You Work

If implementing a named spec:

```
# Create tasks if none exist yet
archon_manage_task(action="create", project_id="...", title="...", status="todo")

# Mark in progress when you start a task
archon_manage_task(action="update", task_id="...", status="doing")

# Mark done immediately when finished
archon_manage_task(action="update", task_id="...", status="done")
```

Only one task in `doing` at a time. Update status in real-time, not in batches at the end.

---

## STEP 3: Project Rules

Read `AGENTS.md` for all project principles, conventions, and patterns.
Read `memory.md` for gotchas and lessons learned.

Key standards:
- `from __future__ import annotations` at top of every Python file
- mypy strict: all functions typed, no bare `Any` without justification
- ruff clean: no unused imports, consistent formatting
- Run `ruff check` and `mypy --strict` after every file change
- Run `pytest` after all files are in place
- Fix all errors before reporting done
- Never include `Co-Authored-By` in commits
