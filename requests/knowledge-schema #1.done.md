# Feature: knowledge-schema

The following plan should be complete, but validate documentation, codebase patterns, and task sanity before implementation.

Pay close attention to naming of existing utils, types, and models. Import from the correct files.

## Feature Description

Define and implement the canonical knowledge data model for the Ultima Second Brain system. The system currently has retrieval plumbing (router, fallbacks, providers, tracing) but zero definition of what a knowledge unit actually *is*. The Supabase `match_vectors` RPC calls a non-existent table structure, `content` is buried in a `metadata` JSON blob, and there is no schema for chunks, documents, entities, or relationships.

This slice delivers:
1. **Pydantic knowledge contracts** — typed models for `KnowledgeChunk`, `KnowledgeDocument`, `KnowledgeEntity`, `KnowledgeRelationship`, `KnowledgeSource`, and their shared enums (`KnowledgeType`, `RelationshipType`, `SourceOrigin`)
2. **Supabase SQL migration** — proper table schema with correct columns, HNSW index on `embedding vector(1024)`, and an updated `match_knowledge_chunks` RPC function aligned to the new table structure
3. **SupabaseProvider fix** — `_normalize_results` reads from real columns (`content`, `document_id`, `knowledge_type`, `chunk_index`, `source_origin`) instead of nested `metadata` blob
4. **Mem0 metadata conventions** — `MemoryService._search_with_provider` and `_normalize_mem0_results` attach and read `knowledge_type`, `document_id`, `chunk_index`, `source_origin` from the Mem0 `metadata` dict
5. **Graphiti type stubs** — `GraphitiNodeType` and `GraphitiEdgeType` enums defined in `knowledge.py` for future graph provider wiring (no Graphiti SDK dependency yet)
6. **Unit tests** — validate all Pydantic models, normalization paths, and enum constraints

## User Story

As a developer building the Second Brain retrieval system
I want a stable, typed knowledge schema shared across Supabase, Mem0, and Graphiti
So that every retrieval result carries consistent, structured metadata regardless of which provider served it

## Problem Statement

The existing `SupabaseProvider` calls `match_vectors` with no real table behind it — content is stored inside a JSON `metadata` blob, making filtering, indexing, and graph linking impossible. There is no canonical definition of what a "memory" is: its type, its parent document, its chunk position, its source origin, or its relationships to other knowledge nodes. This blocks all future work: ingestion, agentic retrieval, specialist agents, and graph traversal.

## Solution Statement

Introduce a `contracts/knowledge.py` module that defines the canonical per-provider knowledge models and shared enums. Update the Supabase migration to match, fix `SupabaseProvider._normalize_results` to read real columns, establish Mem0 metadata key conventions in `MemoryService`, and define Graphiti node/edge type stubs as pure enums (no SDK dependency). The `ContextCandidate` output contract stays unchanged — providers map their native models INTO it, so the retrieval pipeline above this layer requires zero changes.

## Feature Metadata

**Feature Type**: New Capability + Enhancement (schema foundation + provider fix)
**Estimated Complexity**: Medium
**Primary Systems Affected**: `contracts/`, `services/supabase.py`, `services/memory.py`, `migrations/`
**Dependencies**: Pydantic v2 (already installed), no new packages required

---

## CONTEXT REFERENCES

### Relevant Codebase Files — IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `backend/src/second_brain/contracts/context_packet.py` (lines 1-59) — Why: Mirror this exact Pydantic v2 pattern (BaseModel, Field, Literal, datetime defaults). All new models follow the same style.
- `backend/src/second_brain/contracts/conversation.py` (lines 1-40) — Why: Secondary pattern reference — shows uuid, datetime factories, Literal role fields.
- `backend/src/second_brain/services/supabase.py` (lines 40-111) — Why: The `search()` and `_normalize_results()` methods are being fixed. Read the current broken pattern before updating.
- `backend/src/second_brain/services/memory.py` (lines 282-323) — Why: `_normalize_mem0_results()` is being updated to attach knowledge metadata. Read the existing dict traversal pattern.
- `backend/src/second_brain/deps.py` (lines 106-121) — Why: `get_default_config()` may need new keys for `knowledge_type_default`. Follow the existing dict pattern.
- `backend/src/second_brain/contracts/trace.py` — Why: Tertiary pattern reference for enum-style string fields and optional fields with None defaults.

### New Files to Create

- `backend/src/second_brain/contracts/knowledge.py` — Canonical knowledge models and enums
- `backend/migrations/001_knowledge_schema.sql` — Supabase pgvector migration
- `tests/test_knowledge_schema.py` — Unit tests for all new models and normalization

### Relevant Documentation — YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Supabase pgvector HNSW table creation](https://supabase.com/llms/guides.txt)
  - Specific section: "Create Vector Embeddings Table" + "HNSW indexes"
  - Why: Exact SQL pattern for `CREATE EXTENSION`, `CREATE TABLE`, `CREATE INDEX USING hnsw`, `vector_cosine_ops`
- [Mem0 Custom Categories](https://docs.mem0.ai/platform/features/custom-categories)
  - Specific section: "Sample memory payload" — shows `categories`, `structured_attributes`, `metadata` shape
  - Why: Mem0 doesn't have a strict schema — metadata dict is the only extension point. The `knowledge_type` and `document_id` fields must live there.
- [Graphiti Overview](https://help.getzep.com/graphiti/getting-started/overview.mdx)
  - Specific section: "Custom Entity Types" + triplet model (node, edge, relationship)
  - Why: Graphiti entity types map to `GraphitiNodeType` enum values; edge types map to `GraphitiEdgeType` enum values

### Patterns to Follow

**Pydantic model pattern** (mirror `context_packet.py:6-13`):
```python
from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime, timezone

class SomeModel(BaseModel):
    id: str
    field: str
    optional_field: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

**Enum-as-Literal pattern** (use `Literal` for small closed sets, plain `str` for open-ended):
```python
KnowledgeTypeValue = Literal[
    "note", "document", "decision", "conversation",
    "task", "signal", "playbook", "case_study", "transcript"
]
```

**Provider normalization pattern** (mirror `supabase.py:83-109`):
```python
for i, row in enumerate(rpc_results):
    similarity = row.get("similarity", 0.0)
    confidence = max(0.0, min(1.0, float(similarity)))
    results.append(MemorySearchResult(
        id=str(row.get("id", f"supa-{i}")),
        content=str(row.get("content", "")),   # <-- real column, not metadata blob
        source="supabase",
        confidence=confidence,
        metadata={
            "real_provider": True,
            "knowledge_type": row.get("knowledge_type", "document"),
            "document_id": row.get("document_id"),
            "chunk_index": row.get("chunk_index", 0),
            "source_origin": row.get("source_origin", "manual"),
        },
    ))
```

**SQL migration pattern** (from Archon RAG / Supabase docs):
```sql
create extension if not exists vector with schema extensions;

create table knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  embedding extensions.vector(1024) not null,
  knowledge_type text not null default 'document',
  document_id uuid references knowledge_documents(id) on delete cascade,
  chunk_index integer not null default 0,
  source_origin text not null default 'manual',
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index on knowledge_chunks using hnsw (embedding extensions.vector_cosine_ops);
```

### Code Samples to Mirror (required)

- `backend/src/second_brain/contracts/context_packet.py:6` — `ContextCandidate` BaseModel — mirror field style, type annotations, Field defaults
- `backend/src/second_brain/services/supabase.py:71` — `_normalize_results` loop — fix this method, keep the loop structure, change column reads
- `backend/src/second_brain/services/memory.py:294` — `_normalize_mem0_results` dict traversal — extend this method to extract metadata keys
- Archon sample: `supabase.com/llms/guides.txt` (chunk 696) — SQL `CREATE TABLE` + `CREATE INDEX USING hnsw` pattern

**Naming Conventions:**
- Model names: `KnowledgeChunk`, `KnowledgeDocument`, `KnowledgeEntity`, `KnowledgeRelationship`, `KnowledgeSource`
- Enum type aliases: `KnowledgeTypeValue`, `RelationshipTypeValue`, `SourceOriginValue`
- Graphiti stubs: `GraphitiNodeType`, `GraphitiEdgeType` (plain Python classes with class-level string constants, not stdlib Enum — avoids import complexity)
- SQL table names: `knowledge_chunks`, `knowledge_documents`, `knowledge_entities`, `knowledge_relationships`
- RPC function: `match_knowledge_chunks` (replaces `match_vectors`)
- Metadata keys in Mem0: `knowledge_type`, `document_id`, `chunk_index`, `source_origin`

**Error Handling:**
- Follow `supabase.py:63-69` pattern: catch `Exception`, log `type(e).__name__`, return `[]` + metadata with `fallback_reason`
- In normalization: use `.get()` with safe defaults everywhere — never assume columns exist

**Logging Pattern:**
- Follow existing `logger = logging.getLogger(__name__)` at module top
- Log at `DEBUG` for missing columns, `WARNING` for parse failures

**Other Relevant Patterns:**
- `mypy strict=true` is enforced — all new code must be fully typed, no implicit `Any` without `# Intentional Any:` comment
- `ruff line-length = 100` — keep lines ≤ 100 chars
- Tests follow the existing pattern in the project: plain `pytest` functions with `assert`, no test classes needed

---

## IMPLEMENTATION PLAN

### Phase 1: Contracts — knowledge.py

Define all Pydantic models and type aliases. No external dependencies. Pure Python.

**Tasks:**
- Define `KnowledgeTypeValue` Literal type alias covering all 9 knowledge types
- Define `RelationshipTypeValue` Literal type alias covering all 5 relationship types
- Define `SourceOriginValue` Literal type alias covering: `notion`, `obsidian`, `email`, `manual`, `youtube`, `web`, `other`
- Define `GraphitiNodeType` and `GraphitiEdgeType` as simple classes with string constants (no stdlib Enum)
- Define `KnowledgeSource` — integration origin record
- Define `KnowledgeDocument` — parent container for chunks
- Define `KnowledgeChunk` — base retrieval unit with parent ref, embedding dims hint, knowledge type
- Define `KnowledgeEntity` — named concept/person/tool for graph nodes
- Define `KnowledgeRelationship` — typed edge between two nodes with valid_from/valid_to for temporality
- Export all from `contracts/__init__.py`

### Phase 2: SQL Migration

Create `backend/migrations/001_knowledge_schema.sql` with the full Supabase schema.

**Tasks:**
- Enable `vector` extension
- Create `knowledge_sources` table (integration origin registry)
- Create `knowledge_documents` table (parent container, FK to sources)
- Create `knowledge_chunks` table (base unit, FK to documents, `embedding vector(1024)`, HNSW index)
- Create `knowledge_entities` table (graph nodes: name, type, description, metadata)
- Create `knowledge_relationships` table (typed edges: source_node_id, target_node_id, relationship_type, valid_from, valid_to)
- Create `match_knowledge_chunks` RPC function replacing old `match_vectors` — returns `id`, `content`, `similarity`, `knowledge_type`, `document_id`, `chunk_index`, `source_origin`, `metadata`
- Add RLS enable statements on all tables (no policies — leave for auth slice)

### Phase 3: Provider fixes

Fix `SupabaseProvider` and `MemoryService` to use the real schema.

**Tasks:**
- `SupabaseProvider.search()` — update RPC call from `match_vectors` → `match_knowledge_chunks`, update params to match new function signature
- `SupabaseProvider._normalize_results()` — read `content`, `knowledge_type`, `document_id`, `chunk_index`, `source_origin` from top-level row columns (not `metadata` blob)
- `MemoryService._normalize_mem0_results()` — extract and forward `knowledge_type`, `document_id`, `chunk_index`, `source_origin` from Mem0 result `metadata` dict into `MemorySearchResult.metadata`

### Phase 4: Tests

**Tasks:**
- `KnowledgeChunk` round-trip: create → `model_dump()` → reconstruct, assert field equality
- `KnowledgeDocument` → `KnowledgeChunk` parent ref: assert `chunk.document_id == doc.id`
- `KnowledgeEntity` and `KnowledgeRelationship` instantiation with all relationship types
- `KnowledgeTypeValue` invalid value raises `ValidationError`
- `SupabaseProvider._normalize_results` with new column shape: assert `content`, `knowledge_type`, `document_id`, `chunk_index`, `source_origin` all present in result metadata
- `SupabaseProvider._normalize_results` with missing optional columns: assert safe defaults, no crash
- `MemoryService._normalize_mem0_results` with metadata dict carrying knowledge keys: assert forwarded correctly
- `MemoryService._normalize_mem0_results` with empty metadata: assert defaults, no crash

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task must be atomic and independently testable.

---

### CREATE `backend/src/second_brain/contracts/knowledge.py`

- **IMPLEMENT**: Define all type aliases, Graphiti stubs, and five Pydantic models in this order: type aliases → GraphitiNodeType/EdgeType → KnowledgeSource → KnowledgeDocument → KnowledgeChunk → KnowledgeEntity → KnowledgeRelationship. Full file content:

```python
"""Canonical knowledge schema contracts for all providers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Type aliases — closed sets enforced at model level
# ---------------------------------------------------------------------------

KnowledgeTypeValue = Literal[
    "note",
    "document",
    "decision",
    "conversation",
    "task",
    "signal",
    "playbook",
    "case_study",
    "transcript",
]

RelationshipTypeValue = Literal[
    "topic_link",
    "provenance",
    "temporal",
    "entity_mention",
    "supports",
    "contradicts",
]

SourceOriginValue = Literal[
    "notion",
    "obsidian",
    "email",
    "manual",
    "youtube",
    "web",
    "other",
]


# ---------------------------------------------------------------------------
# Graphiti node/edge type stubs — pure string constants, no SDK dependency
# ---------------------------------------------------------------------------

class GraphitiNodeType:
    """Node type constants for Graphiti graph provider (stub — no SDK dep)."""
    CHUNK = "KnowledgeChunk"
    DOCUMENT = "KnowledgeDocument"
    ENTITY = "KnowledgeEntity"
    SOURCE = "KnowledgeSource"


class GraphitiEdgeType:
    """Edge type constants for Graphiti graph provider (stub — no SDK dep)."""
    TOPIC_LINK = "TOPIC_LINK"
    PROVENANCE = "PROVENANCE"
    TEMPORAL = "TEMPORAL"
    ENTITY_MENTION = "ENTITY_MENTION"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"


# ---------------------------------------------------------------------------
# Core knowledge models
# ---------------------------------------------------------------------------

class KnowledgeSource(BaseModel):
    """Integration origin — where content came from."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    origin: SourceOriginValue
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class KnowledgeDocument(BaseModel):
    """Parent container for knowledge chunks."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    knowledge_type: KnowledgeTypeValue
    source_id: str | None = None
    source_url: str | None = None
    source_origin: SourceOriginValue = "manual"
    author: str | None = None
    raw_content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    ingested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class KnowledgeChunk(BaseModel):
    """
    Base retrieval unit — chunk of a document stored with an embedding.

    This is the atomic unit stored in Supabase knowledge_chunks table
    and the primary retrieval target for semantic search.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str | None = None
    content: str
    knowledge_type: KnowledgeTypeValue = "document"
    chunk_index: int = Field(default=0, ge=0)
    source_origin: SourceOriginValue = "manual"
    # embedding is not stored on the model — it lives in the DB column
    # and is produced by VoyageRerankService.embed() at ingestion time
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class KnowledgeEntity(BaseModel):
    """
    Named concept, person, tool, or organisation — graph node.

    Extracted from chunks during ingestion. Used by Graphiti provider
    and for entity-based retrieval filtering.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    entity_type: str  # open-ended: "person", "tool", "concept", "org", etc.
    description: str | None = None
    source_chunk_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class KnowledgeRelationship(BaseModel):
    """
    Typed edge between two knowledge nodes.

    Supports bi-temporal tracking via valid_from / valid_to
    (aligned with Graphiti's temporal edge model).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipTypeValue
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    valid_from: str | None = None
    valid_to: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

- **PATTERN**: `backend/src/second_brain/contracts/context_packet.py:6-59`
- **IMPORTS**: `from __future__ import annotations`, `uuid`, `datetime`, `timezone`, `Any`, `Literal`, `BaseModel`, `Field`
- **GOTCHA**: Do NOT use `stdlib.Enum` for `GraphitiNodeType`/`GraphitiEdgeType` — plain class with string constants avoids mypy Enum subclassing issues and keeps it SDK-free. Do NOT store `embedding: list[float]` on `KnowledgeChunk` — embeddings live in DB only, never on the in-memory model.
- **VALIDATE**: `cd backend && python -c "from second_brain.contracts.knowledge import KnowledgeChunk, KnowledgeDocument, KnowledgeEntity, KnowledgeRelationship, KnowledgeSource; print('OK')"`

---

### UPDATE `backend/src/second_brain/contracts/__init__.py`

- **IMPLEMENT**: Export all new knowledge models from the contracts package
- **PATTERN**: Check existing `__init__.py` content first — add exports without removing existing ones
- **IMPORTS**: None new — just re-exports
- **GOTCHA**: Do not create a circular import — `knowledge.py` must NOT import from other contracts modules
- **VALIDATE**: `cd backend && python -c "from second_brain.contracts import KnowledgeChunk; print('OK')"`

---

### CREATE `backend/migrations/001_knowledge_schema.sql`

- **IMPLEMENT**: Full Supabase pgvector migration. Write exactly this content:

```sql
-- Migration 001: Knowledge schema foundation
-- Establishes canonical tables for Ultima Second Brain storage layer.
-- Run in Supabase SQL editor or via supabase db push.

-- Enable pgvector extension
create extension if not exists vector with schema extensions;

-- -------------------------------------------------------------------------
-- knowledge_sources: integration origin registry
-- -------------------------------------------------------------------------
create table if not exists knowledge_sources (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  origin      text not null check (origin in (
                'notion','obsidian','email','manual','youtube','web','other'
              )),
  config      jsonb not null default '{}',
  created_at  timestamptz not null default now()
);

alter table knowledge_sources enable row level security;

-- -------------------------------------------------------------------------
-- knowledge_documents: parent containers for chunks
-- -------------------------------------------------------------------------
create table if not exists knowledge_documents (
  id             uuid primary key default gen_random_uuid(),
  title          text not null,
  knowledge_type text not null default 'document' check (knowledge_type in (
                   'note','document','decision','conversation',
                   'task','signal','playbook','case_study','transcript'
                 )),
  source_id      uuid references knowledge_sources(id) on delete set null,
  source_url     text,
  source_origin  text not null default 'manual' check (source_origin in (
                   'notion','obsidian','email','manual','youtube','web','other'
                 )),
  author         text,
  raw_content    text,
  metadata       jsonb not null default '{}',
  ingested_at    timestamptz not null default now(),
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

alter table knowledge_documents enable row level security;

create index if not exists knowledge_documents_knowledge_type_idx
  on knowledge_documents (knowledge_type);

create index if not exists knowledge_documents_source_origin_idx
  on knowledge_documents (source_origin);

-- -------------------------------------------------------------------------
-- knowledge_chunks: base retrieval unit (semantic search target)
-- embedding dimension 1024 aligned to voyage-4-large
-- -------------------------------------------------------------------------
create table if not exists knowledge_chunks (
  id             uuid primary key default gen_random_uuid(),
  document_id    uuid references knowledge_documents(id) on delete cascade,
  content        text not null,
  embedding      extensions.vector(1024) not null,
  knowledge_type text not null default 'document' check (knowledge_type in (
                   'note','document','decision','conversation',
                   'task','signal','playbook','case_study','transcript'
                 )),
  chunk_index    integer not null default 0 check (chunk_index >= 0),
  source_origin  text not null default 'manual' check (source_origin in (
                   'notion','obsidian','email','manual','youtube','web','other'
                 )),
  metadata       jsonb not null default '{}',
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

alter table knowledge_chunks enable row level security;

-- HNSW index for cosine similarity (recommended for normalized voyage embeddings)
create index if not exists knowledge_chunks_embedding_idx
  on knowledge_chunks using hnsw (embedding extensions.vector_cosine_ops);

create index if not exists knowledge_chunks_document_id_idx
  on knowledge_chunks (document_id);

create index if not exists knowledge_chunks_knowledge_type_idx
  on knowledge_chunks (knowledge_type);

-- -------------------------------------------------------------------------
-- knowledge_entities: graph nodes (named concepts, people, tools)
-- -------------------------------------------------------------------------
create table if not exists knowledge_entities (
  id               uuid primary key default gen_random_uuid(),
  name             text not null,
  entity_type      text not null,
  description      text,
  source_chunk_ids uuid[] not null default '{}',
  metadata         jsonb not null default '{}',
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

alter table knowledge_entities enable row level security;

create index if not exists knowledge_entities_name_idx
  on knowledge_entities (name);

create index if not exists knowledge_entities_entity_type_idx
  on knowledge_entities (entity_type);

-- -------------------------------------------------------------------------
-- knowledge_relationships: typed edges between nodes (semantic graph)
-- valid_from / valid_to support bi-temporal Graphiti-style tracking
-- -------------------------------------------------------------------------
create table if not exists knowledge_relationships (
  id                uuid primary key default gen_random_uuid(),
  source_node_id    uuid not null,
  target_node_id    uuid not null,
  relationship_type text not null check (relationship_type in (
                      'topic_link','provenance','temporal',
                      'entity_mention','supports','contradicts'
                    )),
  weight            float not null default 1.0 check (weight >= 0.0 and weight <= 1.0),
  valid_from        timestamptz,
  valid_to          timestamptz,
  metadata          jsonb not null default '{}',
  created_at        timestamptz not null default now()
);

alter table knowledge_relationships enable row level security;

create index if not exists knowledge_relationships_source_idx
  on knowledge_relationships (source_node_id);

create index if not exists knowledge_relationships_target_idx
  on knowledge_relationships (target_node_id);

create index if not exists knowledge_relationships_type_idx
  on knowledge_relationships (relationship_type);

-- -------------------------------------------------------------------------
-- match_knowledge_chunks: RPC for semantic similarity search
-- Replaces the old match_vectors stub function.
-- Returns top-k chunks by cosine similarity above threshold.
-- -------------------------------------------------------------------------
create or replace function match_knowledge_chunks(
  query_embedding   extensions.vector(1024),
  match_count       int             default 5,
  match_threshold   float           default 0.6,
  filter_type       text            default null
)
returns table (
  id             uuid,
  content        text,
  similarity     float,
  knowledge_type text,
  document_id    uuid,
  chunk_index    integer,
  source_origin  text,
  metadata       jsonb
)
language sql stable
as $$
  select
    kc.id,
    kc.content,
    1 - (kc.embedding <=> query_embedding) as similarity,
    kc.knowledge_type,
    kc.document_id,
    kc.chunk_index,
    kc.source_origin,
    kc.metadata
  from knowledge_chunks kc
  where
    1 - (kc.embedding <=> query_embedding) >= match_threshold
    and (filter_type is null or kc.knowledge_type = filter_type)
  order by kc.embedding <=> query_embedding
  limit match_count;
$$;
```

- **PATTERN**: Archon RAG sample from `supabase.com/llms/guides.txt` chunk 696 — `CREATE TABLE` + `CREATE INDEX USING hnsw`
- **GOTCHA**: Use `extensions.vector(1024)` NOT `vector(1024)` — Supabase puts the extension in the `extensions` schema. Cosine distance operator `<=>` with `vector_cosine_ops` is correct for normalized Voyage embeddings. The `1 - (embedding <=> query_embedding)` converts cosine *distance* to cosine *similarity*.
- **VALIDATE**: This file is SQL — validate by reviewing it manually. No local execution needed (Supabase-side migration). Mark valid when file is written and content matches spec.

---

### UPDATE `backend/src/second_brain/services/supabase.py`

- **IMPLEMENT**: Two targeted changes:
  1. In `search()`: change RPC name from `match_vectors` → `match_knowledge_chunks`, update params to include `match_threshold` and `filter_type` (pass `threshold` and `None` respectively)
  2. In `_normalize_results()`: read `content`, `knowledge_type`, `document_id`, `chunk_index`, `source_origin` from top-level row keys instead of nested `row_metadata` blob

Full updated `search()` method:
```python
def search(
    self,
    query_embedding: list[float],
    top_k: int = 5,
    threshold: float = 0.6,
    filter_type: str | None = None,
) -> tuple[list[MemorySearchResult], dict[str, Any]]:
    """Search using Supabase pgvector. Returns (results, metadata)."""
    metadata: dict[str, Any] = {"provider": "supabase"}
    try:
        client = self._load_client()
        if client is None:
            return [], {**metadata, "fallback_reason": "client_unavailable"}
        response = client.rpc(
            "match_knowledge_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "match_threshold": threshold,
                "filter_type": filter_type,
            },
        ).execute()
        results = self._normalize_results(response.data or [], top_k, threshold)
        return results, {
            **metadata,
            "real_provider": True,
            "raw_count": len(response.data or []),
        }
    except Exception as e:
        logger.warning("Supabase search failed: %s", type(e).__name__)
        return [], {
            **metadata,
            "fallback_reason": "provider_error",
            "error_type": type(e).__name__,
            "error_message": self._sanitize_error_message(e),
        }
```

Full updated `_normalize_results()` method:
```python
def _normalize_results(
    self,
    rpc_results: list[dict[str, Any]],
    top_k: int,
    threshold: float,
) -> list[MemorySearchResult]:
    """Normalize match_knowledge_chunks RPC results to MemorySearchResult."""
    results: list[MemorySearchResult] = []

    if not rpc_results:
        return results

    for i, row in enumerate(rpc_results):
        similarity = row.get("similarity", 0.0)
        try:
            confidence = max(0.0, min(1.0, float(similarity)))
        except (TypeError, ValueError):
            confidence = 0.0

        # Read from real columns — not nested metadata blob
        content = str(row.get("content", ""))
        knowledge_type = str(row.get("knowledge_type", "document"))
        document_id = row.get("document_id")
        chunk_index_raw = row.get("chunk_index", 0)
        try:
            chunk_index = int(chunk_index_raw)
        except (TypeError, ValueError):
            chunk_index = 0
        source_origin = str(row.get("source_origin", "manual"))

        # Preserve any extra jsonb metadata from the row
        extra_metadata = row.get("metadata", {})
        if not isinstance(extra_metadata, dict):
            extra_metadata = {}

        results.append(
            MemorySearchResult(
                id=str(row.get("id", f"supa-{i}")),
                content=content,
                source="supabase",
                confidence=confidence,
                metadata={
                    "real_provider": True,
                    "knowledge_type": knowledge_type,
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "source_origin": source_origin,
                    **extra_metadata,
                },
            )
        )

        if len(results) >= top_k:
            break

    return results
```

- **PATTERN**: `backend/src/second_brain/services/supabase.py:40-110` — keep exception handling, sanitize_error_message call, and logging style intact
- **IMPORTS**: No new imports needed — `MemorySearchResult` already imported
- **GOTCHA**: The `filter_type` param is added to `search()` signature — update the call site in `MemoryService._search_with_supabase()` in `memory.py` to pass `filter_type=None` explicitly. Also update the type signature to include `filter_type: str | None = None`.
- **VALIDATE**: `cd backend && python -m mypy src/second_brain/services/supabase.py --ignore-missing-imports`

---

### UPDATE `backend/src/second_brain/services/memory.py`

- **IMPLEMENT**: Two targeted changes:
  1. In `_search_with_supabase()`: forward `filter_type=None` to `provider.search()`
  2. In `_normalize_mem0_results()`: extract and forward knowledge metadata keys from the Mem0 result `metadata` dict

Updated `_search_with_supabase()` call to provider (only the `provider.search()` line changes):
```python
results, search_meta = provider.search(embedding, top_k, threshold, filter_type=None)
```

Updated `_normalize_mem0_results()` — in the loop, after building `metadata`, extend it:
```python
# Extract knowledge schema metadata forwarded via Mem0 metadata dict
raw_metadata = item.get("metadata", {})
knowledge_meta: dict[str, Any] = {}
if isinstance(raw_metadata, dict):
    for key in ("knowledge_type", "document_id", "chunk_index", "source_origin"):
        if key in raw_metadata:
            knowledge_meta[key] = raw_metadata[key]

metadata = {
    "real_provider": True,
    **(raw_metadata if isinstance(raw_metadata, dict) else {}),
    **knowledge_meta,  # ensure knowledge keys are present even if already in raw_metadata
}
```

- **PATTERN**: `backend/src/second_brain/services/memory.py:282-323` — keep the existing loop structure, just extend the metadata dict construction
- **IMPORTS**: No new imports needed
- **GOTCHA**: The `_search_with_supabase()` method signature stays the same — only the internal `provider.search()` call gets `filter_type=None`. Do NOT add `filter_type` to `search_memories()` public API in this slice (deferred).
- **VALIDATE**: `cd backend && python -m mypy src/second_brain/services/memory.py --ignore-missing-imports`

---

### CREATE `tests/test_knowledge_schema.py`

- **IMPLEMENT**: Full test file covering all models and normalization paths:

```python
"""Tests for knowledge schema contracts and provider normalization."""

import pytest
from pydantic import ValidationError

from second_brain.contracts.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeEntity,
    KnowledgeRelationship,
    KnowledgeSource,
    GraphitiNodeType,
    GraphitiEdgeType,
)
from second_brain.services.supabase import SupabaseProvider
from second_brain.services.memory import MemoryService


# ---------------------------------------------------------------------------
# KnowledgeSource
# ---------------------------------------------------------------------------

def test_knowledge_source_defaults() -> None:
    src = KnowledgeSource(name="My Notion", origin="notion")
    assert src.origin == "notion"
    assert src.id  # uuid generated
    assert src.config == {}


def test_knowledge_source_invalid_origin() -> None:
    with pytest.raises(ValidationError):
        KnowledgeSource(name="X", origin="twitter")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# KnowledgeDocument
# ---------------------------------------------------------------------------

def test_knowledge_document_round_trip() -> None:
    doc = KnowledgeDocument(title="My Note", knowledge_type="note")
    dumped = doc.model_dump()
    restored = KnowledgeDocument(**dumped)
    assert restored.id == doc.id
    assert restored.knowledge_type == "note"
    assert restored.source_origin == "manual"


def test_knowledge_document_invalid_type() -> None:
    with pytest.raises(ValidationError):
        KnowledgeDocument(title="X", knowledge_type="unknown_type")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# KnowledgeChunk
# ---------------------------------------------------------------------------

def test_knowledge_chunk_defaults() -> None:
    chunk = KnowledgeChunk(content="Hello world")
    assert chunk.chunk_index == 0
    assert chunk.knowledge_type == "document"
    assert chunk.source_origin == "manual"
    assert chunk.document_id is None


def test_knowledge_chunk_parent_ref() -> None:
    doc = KnowledgeDocument(title="Parent Doc", knowledge_type="playbook")
    chunk = KnowledgeChunk(content="Chunk 1", document_id=doc.id, knowledge_type="playbook")
    assert chunk.document_id == doc.id
    assert chunk.knowledge_type == "playbook"


def test_knowledge_chunk_invalid_chunk_index() -> None:
    with pytest.raises(ValidationError):
        KnowledgeChunk(content="X", chunk_index=-1)


def test_knowledge_chunk_all_knowledge_types() -> None:
    types = [
        "note", "document", "decision", "conversation",
        "task", "signal", "playbook", "case_study", "transcript",
    ]
    for kt in types:
        chunk = KnowledgeChunk(content="test", knowledge_type=kt)  # type: ignore[arg-type]
        assert chunk.knowledge_type == kt


# ---------------------------------------------------------------------------
# KnowledgeEntity
# ---------------------------------------------------------------------------

def test_knowledge_entity_instantiation() -> None:
    entity = KnowledgeEntity(name="Claude Code", entity_type="tool")
    assert entity.name == "Claude Code"
    assert entity.source_chunk_ids == []
    assert entity.description is None


# ---------------------------------------------------------------------------
# KnowledgeRelationship
# ---------------------------------------------------------------------------

def test_knowledge_relationship_all_types() -> None:
    types = ["topic_link", "provenance", "temporal", "entity_mention", "supports", "contradicts"]
    for rt in types:
        rel = KnowledgeRelationship(
            source_node_id="a",
            target_node_id="b",
            relationship_type=rt,  # type: ignore[arg-type]
        )
        assert rel.relationship_type == rt
        assert rel.weight == 1.0
        assert rel.valid_from is None
        assert rel.valid_to is None


def test_knowledge_relationship_invalid_type() -> None:
    with pytest.raises(ValidationError):
        KnowledgeRelationship(
            source_node_id="a",
            target_node_id="b",
            relationship_type="unknown",  # type: ignore[arg-type]
        )


def test_knowledge_relationship_weight_bounds() -> None:
    with pytest.raises(ValidationError):
        KnowledgeRelationship(
            source_node_id="a",
            target_node_id="b",
            relationship_type="supports",
            weight=1.5,
        )


# ---------------------------------------------------------------------------
# GraphitiNodeType / GraphitiEdgeType stubs
# ---------------------------------------------------------------------------

def test_graphiti_node_type_constants() -> None:
    assert GraphitiNodeType.CHUNK == "KnowledgeChunk"
    assert GraphitiNodeType.DOCUMENT == "KnowledgeDocument"
    assert GraphitiNodeType.ENTITY == "KnowledgeEntity"
    assert GraphitiNodeType.SOURCE == "KnowledgeSource"


def test_graphiti_edge_type_constants() -> None:
    assert GraphitiEdgeType.SUPPORTS == "SUPPORTS"
    assert GraphitiEdgeType.CONTRADICTS == "CONTRADICTS"
    assert GraphitiEdgeType.TOPIC_LINK == "TOPIC_LINK"


# ---------------------------------------------------------------------------
# SupabaseProvider._normalize_results — new column schema
# ---------------------------------------------------------------------------

def test_supabase_normalize_new_columns() -> None:
    provider = SupabaseProvider()
    rpc_results = [
        {
            "id": "abc-123",
            "content": "This is a playbook chunk",
            "similarity": 0.88,
            "knowledge_type": "playbook",
            "document_id": "doc-456",
            "chunk_index": 2,
            "source_origin": "notion",
            "metadata": {"extra": "value"},
        }
    ]
    results = provider._normalize_results(rpc_results, top_k=5, threshold=0.6)
    assert len(results) == 1
    r = results[0]
    assert r.id == "abc-123"
    assert r.content == "This is a playbook chunk"
    assert r.confidence == pytest.approx(0.88)
    assert r.metadata["knowledge_type"] == "playbook"
    assert r.metadata["document_id"] == "doc-456"
    assert r.metadata["chunk_index"] == 2
    assert r.metadata["source_origin"] == "notion"
    assert r.metadata["extra"] == "value"


def test_supabase_normalize_missing_optional_columns() -> None:
    """Should not crash when optional columns are absent — use safe defaults."""
    provider = SupabaseProvider()
    rpc_results = [
        {
            "id": "xyz",
            "content": "Minimal chunk",
            "similarity": 0.75,
        }
    ]
    results = provider._normalize_results(rpc_results, top_k=5, threshold=0.6)
    assert len(results) == 1
    r = results[0]
    assert r.content == "Minimal chunk"
    assert r.metadata["knowledge_type"] == "document"
    assert r.metadata["chunk_index"] == 0
    assert r.metadata["source_origin"] == "manual"


def test_supabase_normalize_empty() -> None:
    provider = SupabaseProvider()
    results = provider._normalize_results([], top_k=5, threshold=0.6)
    assert results == []


# ---------------------------------------------------------------------------
# MemoryService._normalize_mem0_results — knowledge metadata forwarding
# ---------------------------------------------------------------------------

def test_memory_normalize_mem0_forwards_knowledge_keys() -> None:
    service = MemoryService(provider="mem0")
    mem0_results = [
        {
            "id": "m1",
            "memory": "A note about Claude Code",
            "score": 0.91,
            "metadata": {
                "knowledge_type": "note",
                "document_id": "doc-abc",
                "chunk_index": 0,
                "source_origin": "manual",
            },
        }
    ]
    results = service._normalize_mem0_results(mem0_results, top_k=5, threshold=0.6)
    assert len(results) == 1
    r = results[0]
    assert r.content == "A note about Claude Code"
    assert r.metadata["knowledge_type"] == "note"
    assert r.metadata["document_id"] == "doc-abc"
    assert r.metadata["chunk_index"] == 0
    assert r.metadata["source_origin"] == "manual"


def test_memory_normalize_mem0_empty_metadata() -> None:
    """Should not crash when Mem0 result has no metadata — knowledge keys absent is fine."""
    service = MemoryService(provider="mem0")
    mem0_results = [
        {
            "id": "m2",
            "memory": "Bare result",
            "score": 0.80,
        }
    ]
    results = service._normalize_mem0_results(mem0_results, top_k=5, threshold=0.6)
    assert len(results) == 1
    assert results[0].content == "Bare result"
    assert results[0].metadata.get("real_provider") is True
```

- **PATTERN**: Plain `pytest` functions, no test classes, `assert` style — consistent with existing project test files
- **IMPORTS**: Import from `second_brain.contracts.knowledge`, `second_brain.services.supabase`, `second_brain.services.memory`
- **GOTCHA**: `SupabaseProvider()` can be instantiated without credentials for unit tests — `_normalize_results` is a pure function (no network). `MemoryService()` constructor is safe without config. Use `# type: ignore[arg-type]` on intentionally-invalid test values to satisfy mypy.
- **VALIDATE**: `cd backend && python -m pytest tests/test_knowledge_schema.py -v`

---

## TESTING STRATEGY

### Unit Tests

All in `tests/test_knowledge_schema.py`. Cover:
- All 5 Pydantic models: valid construction, round-trip, defaults
- All 9 `KnowledgeTypeValue` values accepted
- All 6 `RelationshipTypeValue` values accepted
- Invalid values raise `ValidationError`
- `KnowledgeChunk.chunk_index < 0` raises `ValidationError`
- `KnowledgeRelationship.weight > 1.0` raises `ValidationError`
- `GraphitiNodeType` / `GraphitiEdgeType` string constants correct
- `SupabaseProvider._normalize_results` with full column set → correct metadata
- `SupabaseProvider._normalize_results` with missing optional columns → safe defaults
- `SupabaseProvider._normalize_results` with empty list → empty result
- `MemoryService._normalize_mem0_results` with knowledge keys in metadata → forwarded
- `MemoryService._normalize_mem0_results` with no metadata → no crash

### Integration Tests

None in this slice — the schema is wired but no live Supabase connection is tested here. Live integration is deferred to the ingestion slice.

### Edge Cases

- `chunk_index` = 0 (minimum valid)
- `weight` = 0.0 and 1.0 (boundary valid)
- `document_id` = None (chunk without parent — valid)
- `metadata` dict empty — valid everywhere
- RPC result with non-dict `metadata` value — `_normalize_results` must not crash
- Mem0 result with `None` metadata — `_normalize_mem0_results` must not crash

---

## VALIDATION COMMANDS

Execute every command in order. All must pass before marking complete.

### Level 1: Syntax and Style

```bash
cd backend && python -m ruff check src/second_brain/contracts/knowledge.py src/second_brain/services/supabase.py src/second_brain/services/memory.py
cd backend && python -m ruff check ../tests/test_knowledge_schema.py
```

### Level 2: Type Safety

```bash
cd backend && python -m mypy src/second_brain/contracts/knowledge.py --ignore-missing-imports
cd backend && python -m mypy src/second_brain/services/supabase.py --ignore-missing-imports
cd backend && python -m mypy src/second_brain/services/memory.py --ignore-missing-imports
```

### Level 3: Unit Tests

```bash
cd backend && python -m pytest ../tests/test_knowledge_schema.py -v
```

### Level 4: Full Suite (zero regression check)

```bash
cd backend && python -m pytest ../tests/ -v
```

### Level 5: Import smoke test

```bash
cd backend && python -c "
from second_brain.contracts.knowledge import (
    KnowledgeChunk, KnowledgeDocument, KnowledgeEntity,
    KnowledgeRelationship, KnowledgeSource,
    GraphitiNodeType, GraphitiEdgeType,
    KnowledgeTypeValue, RelationshipTypeValue, SourceOriginValue,
)
from second_brain.services.supabase import SupabaseProvider
from second_brain.services.memory import MemoryService
print('All imports OK')
"
```

---

## ACCEPTANCE CRITERIA

- [ ] `contracts/knowledge.py` defines all 5 models + 3 type aliases + 2 Graphiti stubs
- [ ] All 9 knowledge types enforced by `KnowledgeTypeValue` Literal
- [ ] All 6 relationship types enforced by `RelationshipTypeValue` Literal
- [ ] All 7 source origins enforced by `SourceOriginValue` Literal
- [ ] `001_knowledge_schema.sql` creates 5 tables + HNSW index + `match_knowledge_chunks` RPC
- [ ] `SupabaseProvider.search()` calls `match_knowledge_chunks` with `match_threshold` and `filter_type`
- [ ] `SupabaseProvider._normalize_results()` reads real columns, not metadata blob
- [ ] `MemoryService._normalize_mem0_results()` forwards knowledge metadata keys
- [ ] All 235+ existing tests still pass (zero regression)
- [ ] `tests/test_knowledge_schema.py` — all new tests pass
- [ ] `ruff check` clean on all touched files
- [ ] `mypy` clean on all touched files (strict mode)

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately after implementation
- [ ] Full validation command set executed successfully
- [ ] Full test suite passes (existing + new)
- [ ] No linting, formatting, or type-check errors
- [ ] `requests/execution-reports/knowledge-schema-report.done.md` written after completion

---

## NOTES

### Why per-provider models instead of a single canonical model?
Each provider has different native shapes: Supabase returns flat SQL rows, Mem0 returns `{"memory": ..., "metadata": {...}}` dicts, Graphiti returns triplets. Forcing a single storage model across all three creates impedance mismatch. Instead, each provider normalizes its native response into `MemorySearchResult` (intermediate) and then into `ContextCandidate` (output contract). `KnowledgeChunk` is the canonical *definition* of what we store, not a transport format.

### Why no embedding on KnowledgeChunk model?
Embeddings (1024-dim float lists) are expensive to hold in memory and belong in the database column. The `VoyageRerankService.embed()` produces them at ingestion time. Storing them on the model would make every in-memory chunk object ~4KB heavier with no retrieval benefit.

### Why HNSW over IVFFlat?
Supabase docs recommend HNSW for changing datasets (IVFFlat requires `VACUUM ANALYZE` after inserts to stay performant). Since this system will have frequent ingestion, HNSW is the right default.

### Why cosine similarity for Voyage embeddings?
Voyage `voyage-4-large` produces normalized vectors. Cosine similarity is the correct metric for normalized embeddings and is what the Voyage reranker also uses internally, ensuring consistency between storage-side similarity and rerank-side scoring.

### Archon RAG Evidence
- `supabase.com/llms/guides.txt` chunk 696: SQL CREATE TABLE + HNSW index pattern
- `docs.mem0.ai/platform/features/custom-categories`: Mem0 metadata dict shape + `categories` field
- `help.getzep.com/graphiti/getting-started/overview.mdx`: Graphiti triplet model + Custom Entity Types + temporal edge tracking
- `docs.pydantic.dev` chunks 740, 611: `Literal` validation pattern + `ValidationError` behavior
