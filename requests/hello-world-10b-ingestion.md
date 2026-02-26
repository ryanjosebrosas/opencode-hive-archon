# Feature: Hello World 10b — Markdown Ingestion Pipeline

The following plan should be complete, but validate documentation, codebase patterns, and task sanity before implementation.

Pay close attention to naming of existing utils, types, and models. Import from the correct files.

## Feature Description

Build a markdown ingestion pipeline that reads local `.md` files, chunks them by heading boundaries, embeds each chunk via Voyage AI, and stores the documents + chunks in Supabase. This is the data input layer — without it the retrieval pipeline has nothing to search.

## User Story

As a lifelong learner with Obsidian/markdown notes,
I want to ingest my notes into the Second Brain knowledge base,
So that the retrieval pipeline can search my actual knowledge.

## Problem Statement

The knowledge schema contracts (`KnowledgeDocument`, `KnowledgeChunk`) exist. The SQL migration for 5 tables exists. The Supabase provider can search `knowledge_chunks` via `match_knowledge_chunks` RPC. But there is zero ingestion — nothing feeds data INTO the system. The database is empty.

## Solution Statement

- Decision 1: **Markdown-first** — ingest local `.md` files only. No Notion/email/web APIs. Simplest path to real data.
- Decision 2: **Heading-based chunking** — split on `## ` headings, paragraph-split oversized sections, merge tiny sections. Preserves semantic boundaries.
- Decision 3: **Voyage AI embeddings** — use existing `voyageai` SDK pattern. `voyage-4-large` outputs 1024-dim vectors matching the SQL migration.
- Decision 4: **Direct Supabase insert** — use Supabase Python client `.table().insert()` for documents and chunks.
- Decision 5: **Add voyageai + supabase to pyproject.toml** — they were optional before, now required for ingestion.
- Decision 6: **Dry-run mode** — `dry_run=True` chunks and counts but doesn't call APIs. For testing without credentials.

## Feature Metadata

- **Feature Type**: New Capability
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: new `ingestion/` module, `pyproject.toml`
- **Dependencies**: `voyageai>=0.3` (existing code pattern), `supabase>=2.0` (existing code pattern)

### Slice Guardrails (Required)

- **Single Outcome**: Can ingest a directory of .md files into Supabase with Voyage embeddings
- **Expected Files Touched**: 4 files (2 new, 1 modified, 1 new test)
- **Scope Boundary**: Does NOT modify planner, MCP server, or retrieval pipeline. Does NOT add CLI. Ingestion is a Python function call only.
- **Split Trigger**: N/A — already minimal

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/contracts/knowledge.py` (full file) — Why: Contains `KnowledgeDocument` and `KnowledgeChunk` Pydantic models that ingestion must produce. Check exact field names, types, and defaults.
- `backend/src/second_brain/services/supabase.py` (lines 44-60) — Why: Shows Supabase client lazy-loading pattern (`from supabase import create_client`). Ingestion uses same pattern for inserts.
- `backend/src/second_brain/services/voyage.py` (lines 50-67) — Why: Shows Voyage `embed()` call pattern. Ingestion embeds each chunk the same way but with `input_type="document"` (not "query").
- `backend/migrations/001_knowledge_schema.sql` (full file) — Why: Defines `knowledge_documents` and `knowledge_chunks` table schemas. Ingestion inserts must match column names exactly.
- `backend/pyproject.toml` (full file) — Why: Must add `voyageai` and `supabase` to dependencies.
- `tests/test_knowledge_schema.py` (lines 1-30) — Why: Test pattern reference for knowledge model tests.

### New Files to Create

- `backend/src/second_brain/ingestion/__init__.py` — Module init
- `backend/src/second_brain/ingestion/markdown.py` — Markdown ingestion: read, chunk, embed, store
- `tests/test_ingestion.py` — Unit tests for chunking and file reading

### Related Memories (from memory.md)

- Memory: "Embedding dimension alignment: Voyage voyage-4-large outputs 1024 dims; Supabase pgvector column must match (vector(1024)) — mismatch causes silent RPC failures" — Relevance: CRITICAL — embeddings MUST be 1024-dim
- Memory: "Python-first with framework-agnostic contracts" — Relevance: Ingestion module must be plain Python, no framework coupling

### Relevant Documentation

- [Voyage AI Python SDK — embed()](https://docs.voyageai.com/docs/embeddings)
  - Why: Confirm `client.embed([text], model="voyage-4-large", input_type="document")` API
- [Supabase Python Client — Insert](https://supabase.com/docs/reference/python/insert)
  - Why: `client.table("knowledge_chunks").insert({...}).execute()` pattern

### Patterns to Follow

**Supabase Client Init** (from `backend/src/second_brain/services/supabase.py:44-60`):
```python
def _load_client(self) -> Any | None:
    if self._client is not None:
        return self._client
    try:
        from supabase import create_client
        if not self._supabase_url or not self._supabase_key:
            logger.debug("Supabase credentials not configured")
            return None
        self._client = create_client(self._supabase_url, self._supabase_key)
        return self._client
    except ImportError:
        logger.debug("supabase SDK not installed")
    except Exception as e:
        logger.warning("Supabase client init failed: %s", type(e).__name__)
    return None
```

**Knowledge Model Fields** (from `backend/src/second_brain/contracts/knowledge.py`):
```python
class KnowledgeDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    knowledge_type: KnowledgeTypeValue = "document"
    source_origin: SourceOriginValue = "manual"
    source_url: str | None = None
    raw_content: str | None = None
    ...

class KnowledgeChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    chunk_index: int = 0
    knowledge_type: KnowledgeTypeValue = "document"
    source_origin: SourceOriginValue = "manual"
    ...
```

---

## STEP-BY-STEP TASKS

### UPDATE `backend/pyproject.toml` — Add voyageai and supabase dependencies

- **IMPLEMENT**: Change the dependencies list:

  **Current**:
  ```toml
  dependencies = [
      "pydantic>=2.0",
      "httpx>=0.27",
  ]
  ```

  **Replace with**:
  ```toml
  dependencies = [
      "pydantic>=2.0",
      "httpx>=0.27",
      "voyageai>=0.3",
      "supabase>=2.0",
  ]
  ```

  Then run: `cd backend && pip install -e .`

- **PATTERN**: `pyproject.toml:6-9`
- **IMPORTS**: N/A
- **GOTCHA**: `supabase` pulls in `postgrest`, `gotrue`, `realtime`, `storage3` — large dependency tree. First install may take a minute.
- **VALIDATE**: `cd backend && pip install -e . 2>&1 | tail -3 && python -c "import voyageai; import supabase; print('OK')"`

### CREATE `backend/src/second_brain/ingestion/__init__.py` — Module init

- **IMPLEMENT**:
  ```python
  """Ingestion pipeline for feeding knowledge into Second Brain."""
  ```
- **PATTERN**: `backend/src/second_brain/contracts/__init__.py`
- **IMPORTS**: None
- **GOTCHA**: Just a docstring.
- **VALIDATE**: `cd backend && python -c "import second_brain.ingestion"`

### CREATE `backend/src/second_brain/ingestion/markdown.py` — Markdown ingestion

- **IMPLEMENT**: Create new file with these components:

  **1. `chunk_markdown(content, max_chars=2000, min_chars=100) -> list[str]`**
  - Split on `## ` headings
  - If a section exceeds `max_chars`, split on paragraphs (`\n\n`)
  - Merge tiny sections (< `min_chars`) into previous chunk
  - Return list of chunk strings, filtering empty

  **2. `read_markdown_file(path: Path) -> tuple[str, str]`**
  - Read file as UTF-8
  - Extract title from first `# ` heading (not `## `), fallback to filename stem
  - Return `(title, content)`

  **3. `ingest_markdown_directory(directory, supabase_url=None, supabase_key=None, voyage_api_key=None, embed_model="voyage-4-large", knowledge_type="note", source_origin="obsidian", dry_run=False) -> dict[str, Any]`**
  - Resolve credentials from args or env vars (`SUPABASE_URL`, `SUPABASE_KEY`, `VOYAGE_API_KEY`)
  - Validate: directory exists, credentials present (unless dry_run), SDK available
  - Discover `*.md` files in directory (non-recursive, sorted)
  - For each file:
    - `read_markdown_file()` to get title + content
    - `chunk_markdown()` to get chunks
    - Create `KnowledgeDocument` Pydantic model instance
    - If not dry_run: insert document into `knowledge_documents` table
    - For each chunk:
      - Call `voyage_client.embed([chunk_text], model=embed_model, input_type="document")`
      - Create `KnowledgeChunk` Pydantic model instance
      - If not dry_run: insert chunk (with embedding vector) into `knowledge_chunks` table
  - Return summary dict: `{files, chunks, documents_created, chunks_embedded, chunks_stored, errors, dry_run}`

  Full implementation:
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
          dry_run: If True, chunk and count but don't call external APIs

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

      if not dry_run and not _voyage_key:
          return {"error": "VOYAGE_API_KEY required for embedding"}

      # Load Voyage client for embeddings (skip in dry_run)
      voyage_client = None
      if not dry_run:
          try:
              import voyageai
              voyage_client = voyageai.Client(api_key=_voyage_key)
          except ImportError:
              return {"error": "voyageai SDK not installed. Run: pip install voyageai"}
          except Exception as e:
              return {"error": f"Voyage client init failed: {e}"}

      # Load Supabase client (skip in dry_run)
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
                  supa_client.table("knowledge_documents").insert(
                      {
                          "id": doc.id,
                          "title": doc.title,
                          "knowledge_type": doc.knowledge_type,
                          "source_origin": doc.source_origin,
                          "source_url": doc.source_url,
                          "raw_content": doc.raw_content,
                      }
                  ).execute()
                  results["documents_created"] += 1

              # Embed and store chunks
              for i, chunk_text in enumerate(chunks):
                  try:
                      if not dry_run and voyage_client:
                          embed_result = voyage_client.embed(
                              [chunk_text],
                              model=embed_model,
                              input_type="document",
                          )
                          if not embed_result.embeddings:
                              results["errors"].append(
                                  f"{md_file.name} chunk {i}: empty embedding"
                              )
                              continue
                          embedding = embed_result.embeddings[0]
                          results["chunks_embedded"] += 1
                      else:
                          embedding = None

                      chunk = KnowledgeChunk(
                          document_id=doc_id,
                          content=chunk_text,
                          chunk_index=i,
                          knowledge_type=knowledge_type,
                          source_origin=source_origin,
                      )

                      if not dry_run and supa_client and embedding is not None:
                          supa_client.table("knowledge_chunks").insert(
                              {
                                  "id": chunk.id,
                                  "document_id": chunk.document_id,
                                  "content": chunk.content,
                                  "embedding": embedding,
                                  "knowledge_type": chunk.knowledge_type,
                                  "chunk_index": chunk.chunk_index,
                                  "source_origin": chunk.source_origin,
                              }
                          ).execute()
                          results["chunks_stored"] += 1

                  except Exception as e:
                      results["errors"].append(
                          f"{md_file.name} chunk {i}: {type(e).__name__}: {str(e)[:100]}"
                      )

              results["chunks"] += len(chunks)
              logger.info("Ingested %s: %d chunks", md_file.name, len(chunks))

          except Exception as e:
              results["errors"].append(
                  f"{md_file.name}: {type(e).__name__}: {str(e)[:100]}"
              )

      return results
  ```

- **PATTERN**: `services/supabase.py:44-60` for Supabase client, `services/voyage.py:50-67` for Voyage embed
- **IMPORTS**: `pathlib.Path`, `uuid`, `second_brain.contracts.knowledge.KnowledgeDocument`, `KnowledgeChunk`
- **GOTCHA**: Voyage `embed()` takes a LIST of strings, not a single string. `input_type="document"` for ingestion, `input_type="query"` for search queries. The embedding is a plain `list[float]` — Supabase pgvector accepts it directly. Must use `service_role` key (not anon key) for inserts. In dry_run mode, skip all external API calls — only chunk and count.
- **VALIDATE**: `cd backend && python -m ruff check src/second_brain/ingestion/markdown.py && python -m mypy src/second_brain/ingestion/markdown.py --ignore-missing-imports`

### CREATE `tests/test_ingestion.py` — Markdown ingestion tests

- **IMPLEMENT**: Create unit tests for chunking and file reading (NO external API calls):

  ```python
  """Tests for markdown ingestion."""

  from pathlib import Path

  import pytest

  from second_brain.ingestion.markdown import (
      chunk_markdown,
      read_markdown_file,
      ingest_markdown_directory,
  )


  class TestChunkMarkdown:
      """Test chunk_markdown function."""

      def test_empty_content(self):
          assert chunk_markdown("") == []
          assert chunk_markdown("   ") == []

      def test_single_section(self):
          content = "# Title\n\nSome content here."
          chunks = chunk_markdown(content)
          assert len(chunks) == 1
          assert "Some content" in chunks[0]

      def test_split_on_h2(self):
          content = (
              "# Title\n\nIntro paragraph\n\n"
              "## Section 1\n\nContent 1\n\n"
              "## Section 2\n\nContent 2"
          )
          chunks = chunk_markdown(content)
          assert len(chunks) >= 2

      def test_large_section_splits_on_paragraphs(self):
          content = "## Big Section\n\n" + "\n\n".join(
              [f"Paragraph {i} " * 50 for i in range(10)]
          )
          chunks = chunk_markdown(content, max_chars=500)
          assert len(chunks) > 1
          for chunk in chunks:
              # Allow some overshoot from paragraph boundaries
              assert len(chunk) <= 700

      def test_tiny_chunks_merged(self):
          content = (
              "## A\n\nOk\n\n"
              "## B\n\nAlso short\n\n"
              "## C\n\nThis is a much longer section with real content "
              "that should stand on its own."
          )
          chunks = chunk_markdown(content, min_chars=50)
          # Tiny "Ok" and "Also short" should be merged
          assert len(chunks) <= 3

      def test_no_headings(self):
          content = "Just plain text\n\nWith paragraphs\n\nAnd more text"
          chunks = chunk_markdown(content)
          assert len(chunks) >= 1
          assert "Just plain text" in chunks[0]

      def test_preserves_content(self):
          content = "## Section\n\nImportant content that must be preserved."
          chunks = chunk_markdown(content)
          full_text = " ".join(chunks)
          assert "Important content" in full_text

      def test_only_whitespace_sections_filtered(self):
          content = "## A\n\n\n\n## B\n\nReal content"
          chunks = chunk_markdown(content)
          for chunk in chunks:
              assert chunk.strip()


  class TestReadMarkdownFile:
      """Test read_markdown_file function."""

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

      def test_title_with_extra_spaces(self, tmp_path):
          md_file = tmp_path / "test.md"
          md_file.write_text("#   Spaced Title  \n\nContent", encoding="utf-8")
          title, content = read_markdown_file(md_file)
          assert title == "Spaced Title"


  class TestIngestMarkdownDirectory:
      """Test ingest_markdown_directory function."""

      def test_nonexistent_directory(self):
          result = ingest_markdown_directory("/nonexistent/path")
          assert "error" in result
          assert result["files"] == 0

      def test_empty_directory(self, tmp_path):
          result = ingest_markdown_directory(tmp_path)
          assert "error" in result
          assert "No .md files" in result["error"]

      def test_dry_run_no_credentials_needed(self, tmp_path):
          (tmp_path / "note1.md").write_text("# Note 1\n\nContent 1", encoding="utf-8")
          (tmp_path / "note2.md").write_text("# Note 2\n\nContent 2", encoding="utf-8")
          result = ingest_markdown_directory(tmp_path, dry_run=True)
          assert result.get("error") is None
          assert result["files"] == 2
          assert result["chunks"] >= 2
          assert result["dry_run"] is True
          assert result["chunks_stored"] == 0
          assert result["documents_created"] == 0

      def test_dry_run_counts_chunks(self, tmp_path):
          content = "# Big Note\n\n## Section 1\n\nContent 1\n\n## Section 2\n\nContent 2"
          (tmp_path / "big.md").write_text(content, encoding="utf-8")
          result = ingest_markdown_directory(tmp_path, dry_run=True)
          assert result["chunks"] >= 2

      def test_missing_supabase_creds_without_dry_run(self, tmp_path):
          (tmp_path / "note.md").write_text("# Note\n\nContent", encoding="utf-8")
          result = ingest_markdown_directory(tmp_path, voyage_api_key="fake")
          assert "error" in result
          assert "SUPABASE" in result["error"]

      def test_missing_voyage_key_without_dry_run(self, tmp_path):
          (tmp_path / "note.md").write_text("# Note\n\nContent", encoding="utf-8")
          result = ingest_markdown_directory(
              tmp_path, supabase_url="https://x.supabase.co", supabase_key="key"
          )
          assert "error" in result
          assert "VOYAGE" in result["error"]
  ```

- **PATTERN**: `tests/test_knowledge_schema.py` test structure
- **IMPORTS**: `pathlib.Path`, `pytest`
- **GOTCHA**: Use `tmp_path` fixture for file I/O tests (auto-cleanup). Don't test actual Voyage/Supabase in unit tests — only test chunking logic, file reading, and dry_run mode. The `ingest_markdown_directory` tests with missing credentials verify early-exit error messages.
- **VALIDATE**: `cd backend && python -m pytest ../tests/test_ingestion.py -v`

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```
cd backend && python -m ruff check src/second_brain/ingestion/ ../tests/test_ingestion.py
```

### Level 2: Type Safety
```
cd backend && python -m mypy src/second_brain/ingestion/ --ignore-missing-imports
```

### Level 3: Unit Tests
```
cd backend && python -m pytest ../tests/test_ingestion.py -v
```

### Level 4: Full Regression
```
cd backend && python -m pytest ../tests/ -q
```

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] `pyproject.toml` has `voyageai>=0.3` and `supabase>=2.0` in dependencies
- [ ] `ingestion/__init__.py` exists
- [ ] `ingestion/markdown.py` exists with `chunk_markdown`, `read_markdown_file`, `ingest_markdown_directory`
- [ ] `chunk_markdown` splits on ## headings, handles oversized sections, merges tiny chunks
- [ ] `ingest_markdown_directory` has `dry_run` mode that skips all API calls
- [ ] All 275+ existing tests still pass
- [ ] 15+ new tests pass in `test_ingestion.py`
- [ ] Ruff clean, mypy clean

### Confidence Score: 8/10
- **Strengths**: Pure Python logic for chunking, well-defined Pydantic models to produce, existing SDK patterns to follow
- **Uncertainties**: `supabase` package version compatibility, `voyageai` SDK API stability
- **Mitigations**: Dry-run mode for testing without credentials, error handling around all SDK calls
