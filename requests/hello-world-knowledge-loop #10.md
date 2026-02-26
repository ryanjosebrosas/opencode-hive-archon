# Feature: Hello World Personal Knowledge Loop (Slice 10)

The following plan should be complete, but validate documentation, codebase patterns, and task sanity before implementation.

Pay close attention to naming of existing utils, types, and models. Import from the correct files.

## Feature Description

Make the Second Brain actually work end-to-end with real data. Currently the pipeline runs but on fake/mock data with no LLM intelligence and no way to feed knowledge in. This slice delivers a minimal but real vertical: ingest local markdown files into Supabase pgvector via Voyage AI embeddings, flip the retrieval flags from mock to real, add LLM synthesis via Ollama (local or cloud), and expose the MCP server over a real wire protocol. The result: you can point it at a folder of `.md` files, run ingestion, ask questions, and get intelligent answers grounded in your actual notes.

## User Story

As a lifelong learner with markdown notes (Obsidian, blog drafts, personal docs),
I want to ingest my notes into Second Brain and ask questions about them,
So that I get intelligent, grounded answers from my own knowledge base instead of starting from zero.

## Problem Statement

The backend has well-architected retrieval plumbing (router, fallbacks, recall orchestrator, tracing) but it runs entirely on mock data. `MemoryService._search_fallback()` returns hardcoded results. `VoyageRerankService._mock_rerank()` does term-overlap scoring. The planner formats f-string templates — no LLM. The MCP server is a Python class with no wire protocol. There is zero ingestion — nothing feeds data into the system. The knowledge schema contracts (`knowledge.py`) and SQL migration exist but nothing uses them. The system cannot answer a single real question.

## Solution Statement

- Decision 1: **Markdown-first ingestion** — ingest local `.md` files only. No Notion/email/web APIs yet. Simplest path to real data. YAGNI on connectors.
- Decision 2: **Voyage AI for embeddings** — code already exists in `voyage.py`, just needs flag flip + API key. 1024-dim vectors match the SQL migration. No new embedding code needed.
- Decision 3: **Ollama for LLM synthesis** — direct REST API call to `http://localhost:11434/api/chat` (local) or cloud endpoint. Zero SDK dependency, just `httpx`. Free, already connected via `ollama-cloud` provider.
- Decision 4: **Env-var config** — replace hardcoded `deps.py` flags with `os.getenv()` reads. No config files or frameworks.
- Decision 5: **FastMCP for wire protocol** — minimal MCP transport via `fastmcp` library. Exposes existing `recall_search`, `chat` methods over stdio so any MCP client can connect.
- Decision 6: **Supabase retrieval goes real** — flip `supabase_use_real_provider=True`, run the SQL migration, test with ingested data.

## Feature Metadata

- **Feature Type**: Enhancement (make existing architecture real)
- **Estimated Complexity**: Medium-High
- **Primary Systems Affected**: `services/`, `deps.py`, `mcp_server.py`, new `ingestion/` module, new `services/llm.py`
- **Dependencies**: `httpx` (Ollama REST), `voyageai` (embeddings — already coded), `supabase` (DB — already coded), `fastmcp` (MCP transport — new)

### Slice Guardrails (Required)

- **Single Outcome**: Ask a question about ingested markdown notes and get a real, grounded LLM answer
- **Expected Files Touched**: ~8 files (4 new, 4 modified)
- **Scope Boundary**: No Notion/email/web ingestion. No Mem0 real provider. No Graphiti. No specialist agents. No eval scoring. No multi-user auth. No fancy chunking (heading-based split only).
- **Split Trigger**: If ingestion alone exceeds 300 lines, split into ingestion-only + retrieval-activation slices

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/deps.py` (lines 1-121) — Why: ALL hardcoded flags live here. This is where `mem0_use_real_provider: False`, `supabase_use_real_provider: False` are set. Must be updated to env-var driven config.
- `backend/src/second_brain/services/voyage.py` (lines 1-68) — Why: `embed()` method already exists but `embed_enabled=False`. Must be flipped on. The `_load_voyage_client()` already reads `VOYAGE_API_KEY` from env.
- `backend/src/second_brain/services/voyage.py` (lines 136-186) — Why: `rerank()` method with `use_real_rerank` flag. Consider flipping to real for full pipeline validation.
- `backend/src/second_brain/services/supabase.py` (lines 62-97) — Why: `search()` method calls `match_knowledge_chunks` RPC. Already real code, just needs a running DB with the migration applied.
- `backend/src/second_brain/services/memory.py` (lines 1-50) — Why: `MemoryService.__init__` and the provider dispatch. When `provider="supabase"`, it creates `SupabaseProvider` and delegates. The `_search_with_supabase()` path needs Voyage embed to produce query vectors.
- `backend/src/second_brain/orchestration/planner.py` (lines 38-101) — Why: `chat()` method is the main loop. Currently `_interpret_action()` formats f-strings. Must be updated to call LLM for synthesis instead.
- `backend/src/second_brain/orchestration/planner.py` (lines 187-221) — Why: `_format_proceed()` is the "success" path that returns retrieved candidates as raw text. This is where LLM synthesis replaces the f-string template.
- `backend/src/second_brain/mcp_server.py` (lines 1-50, 184-238) — Why: The `MCPServer` class and `chat()` method. Must add wire protocol transport around this.
- `backend/src/second_brain/contracts/knowledge.py` (lines 1-156) — Why: `KnowledgeDocument` and `KnowledgeChunk` models for ingestion output typing.
- `backend/migrations/001_knowledge_schema.sql` (full file) — Why: Must be run against Supabase before ingestion works. The `knowledge_chunks` table is the target. The `match_knowledge_chunks` RPC is what `SupabaseProvider.search()` calls.
- `backend/pyproject.toml` (full file) — Why: Must add new dependencies: `httpx`, `voyageai`, `supabase`, `fastmcp`.

### New Files to Create

- `backend/src/second_brain/ingestion/__init__.py` — Module init
- `backend/src/second_brain/ingestion/markdown.py` — Markdown file ingestion: read .md files, chunk by heading, embed via Voyage, store in Supabase
- `backend/src/second_brain/services/llm.py` — Ollama LLM service: send prompt + context to Ollama REST API, return synthesis
- `tests/test_ingestion.py` — Unit tests for markdown chunking and ingestion flow
- `tests/test_llm_service.py` — Unit tests for LLM service (mocked Ollama responses)

### Related Memories (from memory.md)

- Memory: "Build order: Contracts → Core Loop → Eval/Trace → Memory → Orchestration → Ingestion" — Relevance: We've completed through Orchestration. Ingestion is the prescribed next step.
- Memory: "Embedding dimension alignment: Voyage voyage-4-large outputs 1024 dims; Supabase pgvector column must match (vector(1024))" — Relevance: Critical for ingestion — embeddings MUST be 1024-dim or Supabase RPC fails silently.
- Memory: "OpenCode SDK swallows AbortError" — Relevance: Not directly relevant to this slice (no dispatch), but good pattern awareness.
- Memory: "Incremental-by-default slices with full validation every loop" — Relevance: This slice must have full lint + type + unit + integration validation.

### Relevant Documentation

- [Ollama API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion)
  - Specific section: POST /api/chat
  - Why: The LLM synthesis service calls this endpoint. Need request/response format.
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
  - Specific section: Getting started / stdio transport
  - Why: Wire protocol for MCP server exposure.
- [Voyage AI Python SDK](https://docs.voyageai.com/docs/embeddings)
  - Specific section: embed() method
  - Why: Already coded in voyage.py but confirm API hasn't changed.
- [Supabase Python Client](https://supabase.com/docs/reference/python/rpc)
  - Specific section: RPC calls and insert
  - Why: Ingestion writes to `knowledge_documents` and `knowledge_chunks` tables.

### Patterns to Follow

**Lazy Service Init Pattern** (from `backend/src/second_brain/services/voyage.py:31-48`):
```python
def _load_voyage_client(self) -> Any | None:
    if self._voyage_client is not None:
        return self._voyage_client
    try:
        import voyageai
        api_key = os.getenv("VOYAGE_API_KEY")
        if api_key:
            self._voyage_client = voyageai.Client(api_key=api_key)
        else:
            self._voyage_client = voyageai.Client()
        return self._voyage_client
    except ImportError:
        logger.debug("voyageai SDK not installed")
    except Exception as e:
        logger.warning("Voyage client init failed: %s", type(e).__name__)
    return None
```
- Why this pattern: All services use lazy loading with graceful degradation. LLM service should follow the same pattern.
- Common gotchas: ImportError handling for optional deps. Log warning, don't crash.

**SupabaseProvider Search Pattern** (from `backend/src/second_brain/services/supabase.py:62-97`):
```python
def search(self, query_embedding: list[float], top_k: int = 5, threshold: float = 0.6, filter_type: str | None = None):
    client = self._load_client()
    if client is None:
        return [], {**metadata, "fallback_reason": "client_unavailable"}
    response = client.rpc("match_knowledge_chunks", {...}).execute()
    results = self._normalize_results(response.data or [], top_k)
    return results, metadata
```
- Why this pattern: Ingestion will write to Supabase using the same client pattern. Insert, not RPC.
- Common gotchas: `.execute()` is required after `.rpc()` or `.table().insert()`.

**Pydantic Contract Pattern** (from `backend/src/second_brain/contracts/knowledge.py:60-100`):
```python
class KnowledgeChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    chunk_index: int = 0
    knowledge_type: KnowledgeTypeValue = "document"
    source_origin: SourceOriginValue = "manual"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```
- Why this pattern: Ingestion output must produce `KnowledgeChunk` and `KnowledgeDocument` instances before writing to DB.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation (Config + Dependencies)

Make the system configurable and add missing dependencies.

**Tasks:**
- Update `pyproject.toml` with new dependencies (`httpx`, `voyageai`, `supabase`, `fastmcp`)
- Update `deps.py` to read env vars instead of hardcoded False flags
- Create `services/llm.py` — Ollama LLM service

### Phase 2: Core Implementation (Ingestion + LLM)

Build the two missing capabilities: getting data in, and thinking about it.

**Tasks:**
- Create `ingestion/markdown.py` — read .md files, chunk by heading, embed, store
- Update `planner.py` — replace f-string formatting with LLM synthesis call
- Verify Voyage embed path works with real API key

### Phase 3: Integration (Wire Protocol + Real Retrieval)

Connect everything and flip the switches.

**Tasks:**
- Update `mcp_server.py` — add FastMCP stdio transport
- Flip Supabase and Voyage flags to real (via env vars)
- Run SQL migration against Supabase
- Test full pipeline: ingest → query → retrieve → synthesize → respond

### Phase 4: Testing & Validation

**Tasks:**
- Unit tests for markdown chunking
- Unit tests for LLM service (mocked)
- Integration test: end-to-end query flow
- Manual test: ingest real .md files, ask questions, verify answers

---

## STEP-BY-STEP TASKS

### UPDATE `backend/pyproject.toml` — Add new dependencies

- **IMPLEMENT**: Add to `dependencies` list:
  ```toml
  dependencies = [
      "pydantic>=2.0",
      "httpx>=0.27",
      "voyageai>=0.3",
      "supabase>=2.0",
      "fastmcp>=0.1",
  ]
  ```
- **PATTERN**: Existing `pyproject.toml:6-8`
- **IMPORTS**: N/A
- **GOTCHA**: Pin minimum versions, not exact. `voyageai` and `supabase` are already imported in existing code but were optional — now they become required. Run `pip install -e .` after updating.
- **VALIDATE**: `cd backend && pip install -e . 2>&1 | tail -5`

### UPDATE `backend/src/second_brain/deps.py` — Env-var driven config

- **IMPLEMENT**: Replace hardcoded `get_default_config()` with env-var reads:
  ```python
  import os

  def get_default_config() -> dict[str, Any]:
      """Get configuration from environment variables with safe defaults."""
      return {
          "default_mode": "conversation",
          "default_top_k": 5,
          "default_threshold": 0.6,
          "mem0_rerank_native": True,
          "mem0_skip_external_rerank": True,
          "mem0_use_real_provider": os.getenv("MEM0_USE_REAL_PROVIDER", "false").lower() == "true",
          "mem0_user_id": os.getenv("MEM0_USER_ID"),
          "mem0_api_key": os.getenv("MEM0_API_KEY"),
          "supabase_use_real_provider": os.getenv("SUPABASE_USE_REAL_PROVIDER", "false").lower() == "true",
          "supabase_url": os.getenv("SUPABASE_URL"),
          "supabase_key": os.getenv("SUPABASE_KEY"),
          "voyage_embed_model": os.getenv("VOYAGE_EMBED_MODEL", "voyage-4-large"),
      }
  ```
  Also update `create_voyage_rerank_service()`:
  ```python
  def create_voyage_rerank_service(
      enabled: bool = True,
      model: str = "rerank-2",
      embed_model: str | None = None,
      embed_enabled: bool | None = None,
      use_real_rerank: bool | None = None,
  ) -> VoyageRerankService:
      _embed_model = embed_model or os.getenv("VOYAGE_EMBED_MODEL", "voyage-4-large")
      _embed_enabled = embed_enabled if embed_enabled is not None else (os.getenv("VOYAGE_EMBED_ENABLED", "false").lower() == "true")
      _use_real_rerank = use_real_rerank if use_real_rerank is not None else (os.getenv("VOYAGE_USE_REAL_RERANK", "false").lower() == "true")
      return VoyageRerankService(
          enabled=enabled,
          model=model,
          embed_model=_embed_model,
          embed_enabled=_embed_enabled,
          use_real_rerank=_use_real_rerank,
      )
  ```
- **PATTERN**: `deps.py:106-121` existing config function
- **IMPORTS**: `import os` (add to top of file)
- **GOTCHA**: Default is still `"false"` for all real-provider flags — existing tests pass unchanged. Only flipped via env vars in production. The `os.getenv()` returns string, must compare `.lower() == "true"`.
- **VALIDATE**: `cd backend && python -m pytest ../tests/ -q 2>&1 | tail -5` (all existing tests must still pass)

### CREATE `backend/src/second_brain/services/llm.py` — Ollama LLM service

- **IMPLEMENT**:
  ```python
  """LLM synthesis service via Ollama REST API."""

  import logging
  import os
  from typing import Any

  logger = logging.getLogger(__name__)

  DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
  DEFAULT_OLLAMA_MODEL = "qwen3-coder-next"


  class OllamaLLMService:
      """LLM synthesis via Ollama (local or cloud)."""

      def __init__(
          self,
          base_url: str | None = None,
          model: str | None = None,
      ):
          self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
          self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
          self._client: Any | None = None

      def _load_client(self) -> Any | None:
          """Load httpx client lazily."""
          if self._client is not None:
              return self._client
          try:
              import httpx
              self._client = httpx.Client(base_url=self.base_url, timeout=120.0)
              return self._client
          except ImportError:
              logger.debug("httpx not installed")
          except Exception as e:
              logger.warning("httpx client init failed: %s", type(e).__name__)
          return None

      def synthesize(
          self,
          query: str,
          context_candidates: list[dict[str, Any]],
          system_prompt: str | None = None,
      ) -> tuple[str, dict[str, Any]]:
          """
          Generate a synthesis response from retrieved context.

          Args:
              query: The user's original question
              context_candidates: Retrieved context chunks with content and metadata
              system_prompt: Optional custom system prompt

          Returns:
              Tuple of (response_text, metadata)
          """
          metadata: dict[str, Any] = {
              "llm_provider": "ollama",
              "model": self.model,
              "base_url": self.base_url,
          }

          client = self._load_client()
          if client is None:
              return self._fallback_response(query, context_candidates), {
                  **metadata, "fallback": True, "reason": "client_unavailable"
              }

          # Build context block from candidates
          context_block = self._build_context_block(context_candidates)

          default_system = (
              "You are a personal knowledge assistant. Answer the user's question "
              "using ONLY the provided context from their notes. Be specific, cite "
              "which note the information comes from when possible. If the context "
              "doesn't contain enough information to answer, say so honestly."
          )

          messages = [
              {"role": "system", "content": system_prompt or default_system},
              {"role": "user", "content": f"Context from your notes:\n\n{context_block}\n\nQuestion: {query}"},
          ]

          try:
              response = client.post(
                  "/api/chat",
                  json={
                      "model": self.model,
                      "messages": messages,
                      "stream": False,
                  },
              )
              response.raise_for_status()
              data = response.json()
              answer = data.get("message", {}).get("content", "")
              if not answer:
                  return self._fallback_response(query, context_candidates), {
                      **metadata, "fallback": True, "reason": "empty_response"
                  }
              metadata["total_duration"] = data.get("total_duration")
              metadata["eval_count"] = data.get("eval_count")
              return answer, metadata
          except Exception as e:
              logger.warning("Ollama synthesis failed: %s — %s", type(e).__name__, str(e)[:200])
              return self._fallback_response(query, context_candidates), {
                  **metadata, "fallback": True, "reason": type(e).__name__
              }

      def _build_context_block(self, candidates: list[dict[str, Any]]) -> str:
          """Format context candidates into a readable block for the LLM."""
          if not candidates:
              return "(No relevant context found in your notes.)"
          parts = []
          for i, c in enumerate(candidates, 1):
              source = c.get("source", "unknown")
              content = c.get("content", "")
              confidence = c.get("confidence", 0.0)
              doc_id = c.get("metadata", {}).get("document_id", "")
              header = f"[{i}] (source: {source}, confidence: {confidence:.2f}"
              if doc_id:
                  header += f", doc: {doc_id}"
              header += ")"
              parts.append(f"{header}\n{content}")
          return "\n\n---\n\n".join(parts)

      def _fallback_response(self, query: str, candidates: list[dict[str, Any]]) -> str:
          """Generate a non-LLM fallback response when Ollama is unavailable."""
          if not candidates:
              return "I couldn't find relevant context for your query and the LLM is unavailable."
          context_parts = []
          for i, c in enumerate(candidates[:3], 1):
              content = c.get("content", "")
              if len(content) > 300:
                  content = content[:300] + "..."
              context_parts.append(f"[{i}] {content}")
          return (
              f"(LLM unavailable — showing raw retrieved context)\n\n"
              + "\n\n".join(context_parts)
          )

      def health_check(self) -> bool:
          """Check if Ollama is reachable."""
          client = self._load_client()
          if client is None:
              return False
          try:
              resp = client.get("/api/tags")
              return resp.status_code == 200
          except Exception:
              return False
  ```
- **PATTERN**: `services/voyage.py:13-48` lazy client init pattern
- **IMPORTS**: `import logging, os` at top; `httpx` imported lazily inside `_load_client()`
- **GOTCHA**: Ollama `/api/chat` with `stream: false` returns full response as JSON. With `stream: true` it returns NDJSON — we MUST use `stream: false`. Timeout of 120s because LLM generation can be slow on large context. The `total_duration` in response is in nanoseconds.
- **VALIDATE**: `cd backend && python -m ruff check src/second_brain/services/llm.py && python -m mypy src/second_brain/services/llm.py --ignore-missing-imports`

### CREATE `backend/src/second_brain/ingestion/__init__.py` — Module init

- **IMPLEMENT**:
  ```python
  """Ingestion pipeline for feeding knowledge into Second Brain."""
  ```
- **PATTERN**: `backend/src/second_brain/contracts/__init__.py` pattern
- **IMPORTS**: None
- **GOTCHA**: Just a docstring. Keep empty.
- **VALIDATE**: `python -c "import second_brain.ingestion"`

### CREATE `backend/src/second_brain/ingestion/markdown.py` — Markdown ingestion

- **IMPLEMENT**:
  ```python
  """Markdown file ingestion: read, chunk, embed, store."""

  import logging
  import os
  import uuid
  from pathlib import Path
  from typing import Any

  from second_brain.contracts.knowledge import (
      KnowledgeDocument,
      KnowledgeChunk,
  )

  logger = logging.getLogger(__name__)

  DEFAULT_MAX_CHUNK_CHARS = 2000
  DEFAULT_MIN_CHUNK_CHARS = 100


  def chunk_markdown(
      content: str,
      max_chars: int = DEFAULT_MAX_CHUNK_CHARS,
      min_chars: int = DEFAULT_MIN_CHUNK_CHARS,
  ) -> list[str]:
      """
      Split markdown content into chunks by heading boundaries.

      Strategy: Split on ## headings. If a section exceeds max_chars,
      split on paragraphs (double newline). Merge tiny sections into
      the previous chunk.
      """
      if not content.strip():
          return []

      # Split on level-2 headings (## )
      sections: list[str] = []
      current: list[str] = []

      for line in content.split("\n"):
          if line.startswith("## ") and current:
              sections.append("\n".join(current).strip())
              current = [line]
          else:
              current.append(line)
      if current:
          sections.append("\n".join(current).strip())

      # Split oversized sections on paragraphs
      chunks: list[str] = []
      for section in sections:
          if not section:
              continue
          if len(section) <= max_chars:
              chunks.append(section)
          else:
              paragraphs = section.split("\n\n")
              buf = ""
              for para in paragraphs:
                  if buf and len(buf) + len(para) + 2 > max_chars:
                      chunks.append(buf.strip())
                      buf = para
                  else:
                      buf = buf + "\n\n" + para if buf else para
              if buf.strip():
                  chunks.append(buf.strip())

      # Merge tiny chunks into previous
      merged: list[str] = []
      for chunk in chunks:
          if merged and len(chunk) < min_chars:
              merged[-1] = merged[-1] + "\n\n" + chunk
          else:
              merged.append(chunk)

      return [c for c in merged if c.strip()]


  def read_markdown_file(path: Path) -> tuple[str, str]:
      """Read a markdown file and extract title from first heading or filename."""
      content = path.read_text(encoding="utf-8")
      title = path.stem  # Default: filename without extension

      # Try to extract title from first # heading
      for line in content.split("\n"):
          stripped = line.strip()
          if stripped.startswith("# ") and not stripped.startswith("## "):
              title = stripped[2:].strip()
              break

      return title, content


  def ingest_markdown_directory(
      directory: str | Path,
      supabase_url: str | None = None,
      supabase_key: str | None = None,
      voyage_api_key: str | None = None,
      embed_model: str = "voyage-4-large",
      knowledge_type: str = "note",
      source_origin: str = "obsidian",
      dry_run: bool = False,
  ) -> dict[str, Any]:
      """
      Ingest all .md files from a directory into Supabase.

      Args:
          directory: Path to directory containing .md files
          supabase_url: Supabase project URL (or SUPABASE_URL env var)
          supabase_key: Supabase service role key (or SUPABASE_KEY env var)
          voyage_api_key: Voyage AI API key (or VOYAGE_API_KEY env var)
          embed_model: Voyage embedding model (default: voyage-4-large)
          knowledge_type: Default knowledge type for documents
          source_origin: Source origin label
          dry_run: If True, chunk and embed but don't write to DB

      Returns:
          Summary dict with counts and any errors
      """
      dir_path = Path(directory)
      if not dir_path.is_dir():
          return {"error": f"Directory not found: {directory}", "files": 0, "chunks": 0}

      # Resolve credentials
      _supabase_url = supabase_url or os.getenv("SUPABASE_URL")
      _supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
      _voyage_key = voyage_api_key or os.getenv("VOYAGE_API_KEY")

      if not dry_run and (not _supabase_url or not _supabase_key):
          return {"error": "SUPABASE_URL and SUPABASE_KEY required for non-dry-run ingestion"}

      if not _voyage_key:
          return {"error": "VOYAGE_API_KEY required for embedding"}

      # Load Voyage client for embeddings
      try:
          import voyageai
          voyage_client = voyageai.Client(api_key=_voyage_key)
      except ImportError:
          return {"error": "voyageai SDK not installed. Run: pip install voyageai"}
      except Exception as e:
          return {"error": f"Voyage client init failed: {e}"}

      # Load Supabase client (if not dry run)
      supa_client = None
      if not dry_run:
          try:
              from supabase import create_client
              supa_client = create_client(_supabase_url, _supabase_key)
          except ImportError:
              return {"error": "supabase SDK not installed. Run: pip install supabase"}
          except Exception as e:
              return {"error": f"Supabase client init failed: {e}"}

      # Discover .md files
      md_files = sorted(dir_path.glob("*.md"))
      if not md_files:
          return {"error": f"No .md files found in {directory}", "files": 0, "chunks": 0}

      results: dict[str, Any] = {
          "files": len(md_files),
          "chunks": 0,
          "documents_created": 0,
          "chunks_embedded": 0,
          "chunks_stored": 0,
          "errors": [],
          "dry_run": dry_run,
      }

      for md_file in md_files:
          try:
              title, content = read_markdown_file(md_file)
              chunks = chunk_markdown(content)

              if not chunks:
                  results["errors"].append(f"{md_file.name}: no chunks produced")
                  continue

              # Create document record
              doc_id = str(uuid.uuid4())
              doc = KnowledgeDocument(
                  id=doc_id,
                  title=title,
                  knowledge_type=knowledge_type,
                  source_origin=source_origin,
                  source_url=str(md_file.absolute()),
                  raw_content=content,
              )

              if not dry_run and supa_client:
                  supa_client.table("knowledge_documents").insert({
                      "id": doc.id,
                      "title": doc.title,
                      "knowledge_type": doc.knowledge_type,
                      "source_origin": doc.source_origin,
                      "source_url": doc.source_url,
                      "raw_content": doc.raw_content,
                  }).execute()
                  results["documents_created"] += 1

              # Embed and store chunks
              for i, chunk_text in enumerate(chunks):
                  try:
                      embed_result = voyage_client.embed(
                          [chunk_text],
                          model=embed_model,
                          input_type="document",
                      )
                      if not embed_result.embeddings:
                          results["errors"].append(f"{md_file.name} chunk {i}: empty embedding")
                          continue

                      embedding = embed_result.embeddings[0]
                      results["chunks_embedded"] += 1

                      chunk = KnowledgeChunk(
                          document_id=doc_id,
                          content=chunk_text,
                          chunk_index=i,
                          knowledge_type=knowledge_type,
                          source_origin=source_origin,
                      )

                      if not dry_run and supa_client:
                          supa_client.table("knowledge_chunks").insert({
                              "id": chunk.id,
                              "document_id": chunk.document_id,
                              "content": chunk.content,
                              "embedding": embedding,
                              "knowledge_type": chunk.knowledge_type,
                              "chunk_index": chunk.chunk_index,
                              "source_origin": chunk.source_origin,
                          }).execute()
                          results["chunks_stored"] += 1

                  except Exception as e:
                      results["errors"].append(f"{md_file.name} chunk {i}: {type(e).__name__}: {str(e)[:100]}")

              results["chunks"] += len(chunks)
              logger.info("Ingested %s: %d chunks", md_file.name, len(chunks))

          except Exception as e:
              results["errors"].append(f"{md_file.name}: {type(e).__name__}: {str(e)[:100]}")

      return results
  ```
- **PATTERN**: `services/supabase.py:44-60` for Supabase client lazy loading, `services/voyage.py:50-67` for Voyage embed call
- **IMPORTS**: `pathlib.Path`, `uuid`, `second_brain.contracts.knowledge.KnowledgeDocument`, `KnowledgeChunk`
- **GOTCHA**: Voyage `embed()` takes a LIST of strings, not a single string. `input_type="document"` for ingestion, `input_type="query"` for search. The embedding vector is a plain list[float] — Supabase pgvector accepts it directly in insert. Must use `service_role` key (not anon key) for Supabase inserts.
- **VALIDATE**: `cd backend && python -m ruff check src/second_brain/ingestion/markdown.py && python -m mypy src/second_brain/ingestion/markdown.py --ignore-missing-imports`

### UPDATE `backend/src/second_brain/orchestration/planner.py` — LLM synthesis

- **IMPLEMENT**: Replace the f-string templates in `_format_proceed()` with LLM synthesis:

  a) Add `llm_service` parameter to `__init__`:
  ```python
  def __init__(
      self,
      recall_orchestrator: RecallOrchestrator,
      conversation_store: ConversationStore,
      trace_collector: TraceCollector | None = None,
      llm_service: Any | None = None,
  ):
      self.recall = recall_orchestrator
      self.conversations = conversation_store
      self.trace_collector = trace_collector
      self.llm_service = llm_service
  ```

  b) Update `_format_proceed()` to use LLM when available:
  ```python
  def _format_proceed(self, packet, branch, session_id, metadata):
      candidates = packet.candidates
      if not candidates:
          return self._format_fallback(packet, branch, session_id, metadata)

      # Try LLM synthesis if service available
      if self.llm_service is not None:
          candidate_dicts = [
              {
                  "content": c.content,
                  "source": c.source,
                  "confidence": c.confidence,
                  "metadata": c.metadata,
              }
              for c in candidates
          ]
          # Get original query from the last user turn in conversation
          query = self._get_last_user_query(session_id)
          response_text, llm_metadata = self.llm_service.synthesize(
              query=query,
              context_candidates=candidate_dicts,
          )
          metadata["llm"] = llm_metadata
          return PlannerResponse(
              response_text=response_text,
              action_taken="proceed",
              branch_code=branch,
              session_id=session_id,
              candidates_used=len(candidates),
              confidence=packet.summary.top_confidence,
              retrieval_metadata=metadata,
          )

      # Fallback: f-string formatting (no LLM)
      context_parts = []
      for i, c in enumerate(candidates[:3], 1):
          content = c.content
          if len(content) > MAX_CANDIDATE_CHARS:
              content = f"{content[:MAX_CANDIDATE_CHARS]}..."
          context_parts.append(f"[{i}] {content}")

      response_text = (
          f"Based on {len(candidates)} retrieved context(s) "
          f"(top confidence: {packet.summary.top_confidence:.2f}):\n\n"
          + "\n\n".join(context_parts)
      )

      return PlannerResponse(
          response_text=response_text,
          action_taken="proceed",
          branch_code=branch,
          session_id=session_id,
          candidates_used=len(candidates),
          confidence=packet.summary.top_confidence,
          retrieval_metadata=metadata,
      )
  ```

  c) Add helper to retrieve last user query:
  ```python
  def _get_last_user_query(self, session_id: str) -> str:
      """Get the last user message from the conversation."""
      state = self.conversations.get_or_create(session_id)
      for turn in reversed(state.turns):
          if turn.role == "user":
              return turn.content
      return ""
  ```
- **PATTERN**: `planner.py:187-221` existing `_format_proceed`
- **IMPORTS**: No new imports (llm_service is typed as `Any`)
- **GOTCHA**: `llm_service` is optional — when `None`, falls back to existing f-string formatting. This means ALL existing tests pass unchanged. Only when LLM service is injected does synthesis happen. The `_get_last_user_query` needs access to conversation store which Planner already has.
- **VALIDATE**: `cd backend && python -m pytest ../tests/ -q 2>&1 | tail -5` (all existing tests must still pass)

### UPDATE `backend/src/second_brain/deps.py` — Wire LLM service into planner

- **IMPLEMENT**: Update `create_planner()` to optionally inject LLM service:
  ```python
  def create_llm_service() -> Any:
      """Create LLM service if Ollama is configured."""
      from second_brain.services.llm import OllamaLLMService
      return OllamaLLMService()

  def create_planner(
      memory_service: MemoryService | None = None,
      rerank_service: VoyageRerankService | None = None,
      conversation_store: ConversationStore | None = None,
      trace_collector: TraceCollector | None = None,
      llm_service: Any | None = None,
  ) -> Planner:
      """Create planner with default dependencies."""
      from second_brain.orchestration.planner import Planner
      from second_brain.agents.recall import RecallOrchestrator

      _memory = memory_service or create_memory_service()
      _rerank = rerank_service or create_voyage_rerank_service()
      _conversations = conversation_store or create_conversation_store()
      _llm = llm_service  # None by default — caller opts in

      orchestrator = RecallOrchestrator(
          memory_service=_memory,
          rerank_service=_rerank,
          feature_flags=get_feature_flags(),
          provider_status=get_provider_status(),
          trace_collector=trace_collector,
      )

      return Planner(
          recall_orchestrator=orchestrator,
          conversation_store=_conversations,
          trace_collector=trace_collector,
          llm_service=_llm,
      )
  ```
- **PATTERN**: `deps.py:77-103` existing `create_planner`
- **IMPORTS**: No new top-level imports (lazy import inside `create_llm_service`)
- **GOTCHA**: LLM service is NOT auto-injected by default — must be explicitly passed. This preserves backward compatibility. The `MCPServer.chat()` will need to create and inject it.
- **VALIDATE**: `cd backend && python -m pytest ../tests/ -q`

### UPDATE `backend/src/second_brain/mcp_server.py` — Inject LLM + add FastMCP transport

- **IMPLEMENT**:

  a) Update `chat()` to inject LLM service:
  ```python
  def chat(self, query, session_id=None, mode="conversation", top_k=5, threshold=0.6):
      from second_brain.deps import create_planner, create_llm_service

      with self._chat_lock:
          if self._conversation_store is None:
              self._conversation_store = ConversationStore()

          safe_session_id = session_id
          if safe_session_id and safe_session_id not in self._issued_session_ids:
              safe_session_id = None
          if safe_session_id and not self._conversation_store.has_session(safe_session_id):
              safe_session_id = None

          if self._planner is None:
              llm = create_llm_service()
              self._planner = create_planner(
                  conversation_store=self._conversation_store,
                  trace_collector=self.trace_collector,
                  llm_service=llm,
              )

          response = self._planner.chat(
              query=query,
              session_id=safe_session_id,
              mode=mode,
              top_k=top_k,
              threshold=threshold,
          )
          self._issued_session_ids.add(response.session_id)
          self._issued_session_ids.intersection_update(
              self._conversation_store.list_session_ids()
          )
      return response.model_dump()
  ```

  b) Add FastMCP transport at bottom of file:
  ```python
  def create_fastmcp_server():
      """Create FastMCP server wrapping MCPServer methods."""
      try:
          from fastmcp import FastMCP
      except ImportError:
          logger.warning("fastmcp not installed — MCP transport unavailable")
          return None

      mcp = FastMCP("Second Brain")
      server = get_mcp_server()

      @mcp.tool()
      def recall_search(
          query: str,
          mode: str = "conversation",
          top_k: int = 5,
          threshold: float = 0.6,
      ) -> dict:
          """Search your knowledge base for relevant context."""
          return server.recall_search(query=query, mode=mode, top_k=top_k, threshold=threshold)

      @mcp.tool()
      def chat(
          query: str,
          session_id: str | None = None,
          mode: str = "conversation",
      ) -> dict:
          """Ask a question and get an answer grounded in your knowledge base."""
          return server.chat(query=query, session_id=session_id, mode=mode)

      @mcp.tool()
      def ingest_markdown(
          directory: str,
          knowledge_type: str = "note",
          source_origin: str = "obsidian",
      ) -> dict:
          """Ingest markdown files from a directory into your knowledge base."""
          from second_brain.ingestion.markdown import ingest_markdown_directory
          return ingest_markdown_directory(
              directory=directory,
              knowledge_type=knowledge_type,
              source_origin=source_origin,
          )

      return mcp


  if __name__ == "__main__":
      mcp = create_fastmcp_server()
      if mcp:
          mcp.run()
  ```
- **PATTERN**: `mcp_server.py:184-238` existing `chat()` method
- **IMPORTS**: `from fastmcp import FastMCP` (lazy, inside function)
- **GOTCHA**: FastMCP `@mcp.tool()` decorator auto-generates tool schema from type hints. The `mcp.run()` starts stdio transport. The `if __name__ == "__main__"` guard allows `python -m second_brain.mcp_server` to start the server. Keep all existing methods unchanged — FastMCP wraps them.
- **VALIDATE**: `cd backend && python -m ruff check src/second_brain/mcp_server.py && python -m mypy src/second_brain/mcp_server.py --ignore-missing-imports`

### CREATE `tests/test_ingestion.py` — Markdown ingestion tests

- **IMPLEMENT**: Unit tests for `chunk_markdown` and `read_markdown_file`:
  ```python
  """Tests for markdown ingestion."""
  import tempfile
  from pathlib import Path

  import pytest

  from second_brain.ingestion.markdown import chunk_markdown, read_markdown_file


  class TestChunkMarkdown:
      def test_empty_content(self):
          assert chunk_markdown("") == []
          assert chunk_markdown("   ") == []

      def test_single_section(self):
          content = "# Title\n\nSome content here."
          chunks = chunk_markdown(content)
          assert len(chunks) == 1
          assert "Some content" in chunks[0]

      def test_split_on_h2(self):
          content = "# Title\n\nIntro\n\n## Section 1\n\nContent 1\n\n## Section 2\n\nContent 2"
          chunks = chunk_markdown(content)
          assert len(chunks) >= 2

      def test_large_section_splits_on_paragraphs(self):
          content = "## Big Section\n\n" + "\n\n".join([f"Paragraph {i} " * 50 for i in range(10)])
          chunks = chunk_markdown(content, max_chars=500)
          assert len(chunks) > 1
          for chunk in chunks:
              assert len(chunk) <= 600  # Allow some overshoot from merging

      def test_tiny_chunks_merged(self):
          content = "## A\n\nOk\n\n## B\n\nAlso short\n\n## C\n\nThis is a much longer section with real content."
          chunks = chunk_markdown(content, min_chars=50)
          # Tiny sections should be merged
          assert len(chunks) <= 3

      def test_no_headings(self):
          content = "Just plain text\n\nWith paragraphs\n\nAnd more text"
          chunks = chunk_markdown(content)
          assert len(chunks) >= 1


  class TestReadMarkdownFile:
      def test_reads_file_and_extracts_title(self, tmp_path):
          md_file = tmp_path / "test.md"
          md_file.write_text("# My Title\n\nSome content.", encoding="utf-8")
          title, content = read_markdown_file(md_file)
          assert title == "My Title"
          assert "Some content" in content

      def test_no_heading_uses_filename(self, tmp_path):
          md_file = tmp_path / "notes.md"
          md_file.write_text("Just content, no heading.", encoding="utf-8")
          title, content = read_markdown_file(md_file)
          assert title == "notes"

      def test_h2_not_used_as_title(self, tmp_path):
          md_file = tmp_path / "doc.md"
          md_file.write_text("## Section\n\nContent", encoding="utf-8")
          title, content = read_markdown_file(md_file)
          assert title == "doc"  # Falls back to filename
  ```
- **PATTERN**: `tests/test_knowledge_schema.py` test structure
- **IMPORTS**: `pytest`, `pathlib.Path`, `tempfile`
- **GOTCHA**: Use `tmp_path` fixture for file I/O tests. Don't test actual Voyage/Supabase calls in unit tests — that's integration.
- **VALIDATE**: `cd backend && python -m pytest ../tests/test_ingestion.py -q`

### CREATE `tests/test_llm_service.py` — LLM service tests

- **IMPLEMENT**: Unit tests with mocked httpx:
  ```python
  """Tests for Ollama LLM service."""
  from unittest.mock import MagicMock, patch

  import pytest


  class TestOllamaLLMService:
      def test_init_defaults(self):
          from second_brain.services.llm import OllamaLLMService
          svc = OllamaLLMService()
          assert svc.base_url == "http://localhost:11434"
          assert svc.model == "qwen3-coder-next"

      def test_init_custom(self):
          from second_brain.services.llm import OllamaLLMService
          svc = OllamaLLMService(base_url="http://custom:1234", model="llama3")
          assert svc.base_url == "http://custom:1234"
          assert svc.model == "llama3"

      def test_init_from_env(self, monkeypatch):
          monkeypatch.setenv("OLLAMA_BASE_URL", "http://envhost:5555")
          monkeypatch.setenv("OLLAMA_MODEL", "envmodel")
          from second_brain.services.llm import OllamaLLMService
          svc = OllamaLLMService()
          assert svc.base_url == "http://envhost:5555"
          assert svc.model == "envmodel"

      def test_synthesize_success(self):
          from second_brain.services.llm import OllamaLLMService
          svc = OllamaLLMService()

          mock_response = MagicMock()
          mock_response.status_code = 200
          mock_response.json.return_value = {
              "message": {"content": "Based on your notes, the answer is X."},
              "total_duration": 1000000,
              "eval_count": 50,
          }
          mock_response.raise_for_status = MagicMock()

          mock_client = MagicMock()
          mock_client.post.return_value = mock_response
          svc._client = mock_client

          answer, meta = svc.synthesize(
              query="What is X?",
              context_candidates=[{"content": "X is defined as...", "source": "supabase", "confidence": 0.9}],
          )
          assert "answer is X" in answer
          assert meta["llm_provider"] == "ollama"
          assert meta.get("fallback") is None

      def test_synthesize_fallback_on_error(self):
          from second_brain.services.llm import OllamaLLMService
          svc = OllamaLLMService()

          mock_client = MagicMock()
          mock_client.post.side_effect = Exception("connection refused")
          svc._client = mock_client

          answer, meta = svc.synthesize(
              query="What is X?",
              context_candidates=[{"content": "some context", "source": "supabase", "confidence": 0.8}],
          )
          assert "LLM unavailable" in answer or "raw retrieved context" in answer
          assert meta["fallback"] is True

      def test_synthesize_no_client(self):
          from second_brain.services.llm import OllamaLLMService
          svc = OllamaLLMService()
          # Don't load client — _client stays None, _load_client will fail without httpx
          svc._client = None
          # Mock _load_client to return None (simulating missing httpx)
          svc._load_client = MagicMock(return_value=None)

          answer, meta = svc.synthesize(
              query="test",
              context_candidates=[],
          )
          assert meta["fallback"] is True
          assert meta["reason"] == "client_unavailable"

      def test_build_context_block_empty(self):
          from second_brain.services.llm import OllamaLLMService
          svc = OllamaLLMService()
          block = svc._build_context_block([])
          assert "No relevant context" in block

      def test_build_context_block_with_candidates(self):
          from second_brain.services.llm import OllamaLLMService
          svc = OllamaLLMService()
          block = svc._build_context_block([
              {"content": "Note about RAG", "source": "supabase", "confidence": 0.9, "metadata": {}},
              {"content": "Note about LLMs", "source": "supabase", "confidence": 0.8, "metadata": {}},
          ])
          assert "RAG" in block
          assert "LLMs" in block
          assert "[1]" in block
          assert "[2]" in block

      def test_health_check_success(self):
          from second_brain.services.llm import OllamaLLMService
          svc = OllamaLLMService()

          mock_response = MagicMock()
          mock_response.status_code = 200

          mock_client = MagicMock()
          mock_client.get.return_value = mock_response
          svc._client = mock_client

          assert svc.health_check() is True

      def test_health_check_failure(self):
          from second_brain.services.llm import OllamaLLMService
          svc = OllamaLLMService()

          mock_client = MagicMock()
          mock_client.get.side_effect = Exception("down")
          svc._client = mock_client

          assert svc.health_check() is False
  ```
- **PATTERN**: `tests/test_supabase_provider.py` mock patterns
- **IMPORTS**: `unittest.mock.MagicMock`, `unittest.mock.patch`, `pytest`
- **GOTCHA**: Don't import at module level — import inside test methods to avoid import errors if httpx isn't installed. Use `monkeypatch.setenv` for env var tests.
- **VALIDATE**: `cd backend && python -m pytest ../tests/test_llm_service.py -q`

### VALIDATE — Full test suite + lint + type check

- **IMPLEMENT**:
  1. `cd backend && python -m ruff check src/second_brain/ ../tests/`
  2. `cd backend && python -m mypy src/second_brain/ --ignore-missing-imports`
  3. `cd backend && python -m pytest ../tests/ -q`
  4. Manual: Set env vars and test ingestion + query (integration test)
- **PATTERN**: Existing validation approach
- **GOTCHA**: New dependencies must be installed first (`pip install -e .`). Existing 235+ tests must still pass. New tests add ~20 more.
- **VALIDATE**: All commands above pass with zero errors

---

## TESTING STRATEGY

### Unit Tests

- `test_ingestion.py`: `chunk_markdown` (empty, single, split on h2, oversized, tiny merge, no headings), `read_markdown_file` (title extraction, filename fallback, h2 not title)
- `test_llm_service.py`: init defaults, custom config, env vars, synthesize success, fallback on error, no client, context block formatting, health check

### Integration Tests

- End-to-end: ingest a test .md file → query via MCPServer.chat() → verify response contains content from the ingested file
- Requires: `SUPABASE_URL`, `SUPABASE_KEY`, `VOYAGE_API_KEY`, `OLLAMA_BASE_URL` env vars set
- NOT run in CI — manual validation only

### Edge Cases

- Edge case 1: Empty markdown file → `chunk_markdown` returns empty list, ingestion skips file
- Edge case 2: Ollama unreachable → LLM synthesis falls back to raw context display
- Edge case 3: Voyage API key invalid → ingestion returns clear error message
- Edge case 4: Supabase table doesn't exist (migration not run) → search returns empty with error metadata
- Edge case 5: Very large .md file (>100KB) → chunks stay under 2000 chars each

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```
cd backend && python -m ruff check src/second_brain/ ../tests/
```

### Level 2: Type Safety
```
cd backend && python -m mypy src/second_brain/ --ignore-missing-imports
```

### Level 3: Unit Tests
```
cd backend && python -m pytest ../tests/test_ingestion.py ../tests/test_llm_service.py -q
```

### Level 4: Integration Tests
```
cd backend && python -m pytest ../tests/ -q
```

### Level 5: Manual Validation

1. Run SQL migration against Supabase: Copy `backend/migrations/001_knowledge_schema.sql` into Supabase SQL editor and execute
2. Set env vars:
   ```bash
   export SUPABASE_URL="https://your-project.supabase.co"
   export SUPABASE_KEY="your-service-role-key"
   export SUPABASE_USE_REAL_PROVIDER="true"
   export VOYAGE_API_KEY="your-voyage-key"
   export VOYAGE_EMBED_ENABLED="true"
   export OLLAMA_BASE_URL="http://localhost:11434"
   export OLLAMA_MODEL="qwen3-coder-next"
   ```
3. Ingest test markdown:
   ```python
   from second_brain.ingestion.markdown import ingest_markdown_directory
   result = ingest_markdown_directory("path/to/your/notes")
   print(result)
   ```
4. Query:
   ```python
   from second_brain.mcp_server import get_mcp_server
   server = get_mcp_server()
   response = server.chat("What did I write about retrieval-augmented generation?")
   print(response["response_text"])
   ```
5. Verify: Response should reference actual content from your ingested notes

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] `pyproject.toml` has `httpx`, `voyageai`, `supabase`, `fastmcp` dependencies
- [ ] `deps.py` reads all config from env vars (no more hardcoded `False`)
- [ ] `services/llm.py` exists with `OllamaLLMService` class
- [ ] `ingestion/markdown.py` exists with `chunk_markdown` and `ingest_markdown_directory`
- [ ] `planner.py` uses LLM synthesis when `llm_service` is injected
- [ ] `planner.py` falls back to f-string when `llm_service` is None (backward compat)
- [ ] `mcp_server.py` injects LLM service into planner
- [ ] `mcp_server.py` has FastMCP transport (`create_fastmcp_server()`)
- [ ] All existing 235+ tests still pass
- [ ] New tests for ingestion (~10) and LLM service (~10) pass
- [ ] Ruff clean, mypy clean

### Runtime (verify after testing/deployment)

- [ ] Markdown files can be ingested into Supabase (documents + chunks created)
- [ ] Voyage embeddings are 1024-dim and stored correctly in pgvector
- [ ] `match_knowledge_chunks` RPC returns relevant results for ingested content
- [ ] Ollama synthesis produces contextual answers (not just raw chunks)
- [ ] FastMCP server starts and accepts MCP client connections
- [ ] Full loop works: ingest → query → retrieve → synthesize → respond

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms end-to-end flow works
- [ ] Acceptance criteria all met

---

## NOTES

### Key Design Decisions

- **Ollama over OpenAI/Anthropic for LLM**: Free, local, already connected via `ollama-cloud`. No new API costs. User has 33 Ollama models available. Direct REST API avoids SDK dependency.
- **Heading-based chunking**: Simplest approach that preserves semantic boundaries in markdown. No need for sentence-level or token-level splitting yet (YAGNI). Headings are natural topic boundaries.
- **LLM service is optional**: Injected explicitly, not auto-created. This means the entire existing test suite (235+ tests) runs without change — no Ollama dependency in tests.
- **FastMCP over raw stdio**: FastMCP handles MCP protocol serialization, tool schema generation, and transport. Less code than hand-rolling stdio JSON-RPC.
- **No Mem0 real provider**: Only Supabase goes real in this slice. Mem0 remains mock. One real provider is enough to prove the pipeline. Mem0 activation is a follow-up slice.

### Risks

- Risk 1: **Voyage API costs** — Embedding all your notes costs money. Mitigation: Start with a small test directory (10-20 files). `dry_run=True` mode for testing without API calls.
- Risk 2: **Ollama latency** — Local Ollama can be slow on large context. Mitigation: 120s timeout. Cloud Ollama (`ollama-cloud`) is faster if available.
- Risk 3: **Supabase migration breaks existing data** — Mitigation: The migration uses `CREATE TABLE IF NOT EXISTS` — safe to re-run. No existing data to break (tables are new).
- Risk 4: **FastMCP compatibility** — New library, might have quirks. Mitigation: FastMCP wraps existing methods — if it doesn't work, the Python API still works directly.

### Confidence Score: 7/10
- **Strengths**: All service code patterns exist (Voyage, Supabase, lazy loading). SQL migration is written. Knowledge contracts are defined. The architecture is proven (routing, fallbacks, tracing all work on mock data).
- **Uncertainties**: FastMCP integration untested. Real Voyage/Supabase interaction untested in this project. Ollama response quality with retrieved context unknown. Chunking strategy may need tuning.
- **Mitigations**: Each component can be tested independently. LLM service has fallback mode. Ingestion has dry_run mode. All flags default to off for backward compat.
