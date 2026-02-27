# Infrastructure Pillars
<!-- Generated: 2026-02-27 | Source: PRD.md | Status: 0/5 complete -->
<!-- Council validated: 5 models (Claude, GPT, Qwen, GLM-5, DeepSeek), 3 rounds structured debate -->
<!-- PLUS ULTRA: Pillar 1 expanded from 4 → 63 specs based on world-class data infrastructure research -->

## Pillar 1: Data Infrastructure (PLUS ULTRA)
- **Status**: [ ] not started
- **Why first**: Every downstream pillar reads from the knowledge schema, uses Ollama for LLM synthesis, and depends on reliable storage, search, and retrieval primitives. This pillar builds the fortress — hybrid search, graph traversal, content deduplication, embedding versioning, audit logs, disaster recovery, temporal queries — all at the database level where they're fastest. Without this, Pillars 2-5 build on sand.
- **Scope** (12 sub-sections):
  - **A. Type Safety & Config (4)**: mypy strict, Pydantic Settings config, structured JSON logging, error taxonomy
  - **B. Schema & Migrations (5)**: flexible metadata, schema versioning with checksums, migration runner, schema docs, additive-only migration policy
  - **C. Database Core (7)**: connection pool + circuit breaker, transaction management, concurrent write safety, data integrity constraints, content-addressable deduplication (SHA-256), chunk status lifecycle (active/superseded/archived/deleted), optimistic locking
  - **D. Supabase Search Infrastructure (8)**: full-text search (tsvector + GIN), hybrid search RPC (vector + keyword with RRF fusion), trigram fuzzy entity search, graph traversal recursive CTEs, temporal query functions, database views, materialized views, statistics functions
  - **E. Indexing & Query Optimization (5)**: HNSW tuning (m=24, ef_construction=128), partial HNSW indexes per knowledge_type, halfvec migration (50% storage reduction), composite/covering indexes, query performance baselines with EXPLAIN ANALYZE
  - **F. Knowledge Graph Infrastructure (4)**: entity contract hardening, entity alias table with trigram index, entity name embedding (halfvec), temporal relationship indexing
  - **G. Embedding Infrastructure (4)**: embedding model registry, embedding cache table, batch re-embedding pipeline, embedding pipeline validation
  - **H. Data Quality (4)**: input validation layer, chunk quality scoring, metadata enrichment (word count, language, topic), data lineage tracking (source_chain)
  - **I. Pipeline Resilience (4)**: ingestion job tracking with idempotency keys, dead letter queue for failed chunks, provider rate limiter (token bucket), unified provider health monitor
  - **J. Data Operations (5)**: backup/restore (full JSON), embedding-free backup (vendor independence), bulk operations (re-embed, re-index), data cleanup tools, TTL/staleness scoring
  - **K. Audit, Compliance & Recovery (5)**: trigger-based audit log, full data export (GDPR-style), source priority system, conflict detection view, disaster recovery prep (PITR + nightly backup)
  - **L. Multi-Modal & Future-Proofing (3)**: content_type column, multi-vector readiness, metadata conventions doc
  - **Integration Proof + Tests (6)**: storage metrics dashboard, E2E fortress test, test fixtures/seed data, real provider test harness, RLS policies prep, Ollama cloud auth
- **Not included**: Entity extraction logic (Pillar 2), new file format parsers (Pillar 3), retrieval accuracy harness (Pillar 4), Pydantic AI migration (Pillar 5), content generation agents (Phase 2)
- **Depends on**: None (foundation)
- **Estimated specs**: ~63 (light: 10, standard: 50, heavy: 3)
- **Gate criteria**:
  - [ ] `mypy --strict backend/src/second_brain` = 0 errors
  - [ ] Centralized config validates on startup — bad config = immediate structured error
  - [ ] Structured JSON logs with correlation IDs on all operations
  - [ ] Error taxonomy: every error has code + context + retry hint
  - [ ] Schema versioning with drift detection operational
  - [ ] Migration runner: auto-apply, dry-run, rollback, concurrent lock
  - [ ] Supabase pool: retry, circuit breaker, health check, metrics
  - [ ] Transactions: multi-table writes atomic, partial writes roll back
  - [ ] Concurrent safety: parallel ingestion jobs don't corrupt data
  - [ ] Content dedup: same content ingested twice = update not duplicate (SHA-256)
  - [ ] Chunk lifecycle: active/superseded/archived/deleted status enforced
  - [ ] Full-text search: tsvector + GIN index on chunks, fulltext RPC works
  - [ ] Hybrid search: vector + keyword with RRF fusion returns better results than either alone
  - [ ] Fuzzy entity search: trigram matching handles typos
  - [ ] Graph traversal: recursive CTE traverses 2+ hops in Postgres
  - [ ] Temporal queries: "knowledge since last week" returns correct results
  - [ ] HNSW tuned with benchmarks at 1K/10K/100K documented
  - [ ] Partial HNSW indexes per knowledge_type operational
  - [ ] Query baselines: p50/p95 for 10+ core queries established
  - [ ] Entity alias table: "John" = "John Smith" = "J. Smith" resolved
  - [ ] Entity name embedding: semantic entity search works
  - [ ] Embedding model registry: model version tracked per chunk
  - [ ] Embedding cache: re-ingestion skips already-embedded content
  - [ ] Data validation: malformed data rejected with structured errors
  - [ ] Chunk quality: low-quality chunks flagged/rejected
  - [ ] Metadata enrichment: word count, language auto-extracted
  - [ ] Data lineage: provenance chain queryable
  - [ ] Ingestion jobs: idempotency prevents double-ingestion
  - [ ] Dead letter queue: failed chunks isolated, pipeline continues
  - [ ] Provider rate limiter: no 429 errors mid-batch
  - [ ] Provider health monitor: all providers checked on startup
  - [ ] Backup/restore: dump → fresh DB → restore → identical results
  - [ ] Embedding-free backup: export without vectors, re-embeddable
  - [ ] Audit log: all INSERT/UPDATE/DELETE captured with old/new data
  - [ ] Conflict detection: duplicate content from different sources surfaced
  - [ ] Disaster recovery: PITR enabled or documented, nightly backup configured
  - [ ] RLS policies: written but disabled, user_id column on all tables
  - [ ] Content type + multi-vector readiness columns present
  - [ ] Ollama local + cloud both work with health + model availability check
  - [ ] Test fixtures: 12+ sample files across 4 formats with edge cases
  - [ ] Real provider tests: Supabase + Voyage + Ollama integration verified
  - [ ] E2E fortress test: ingest → deduplicate → embed → store → hybrid search → entity search → graph traverse → temporal query → backup → restore → concurrent ingestion → soft delete → restore → audit log — ALL PASS
  - [ ] `ruff check backend/src/ && python -m pytest tests/ -q` all pass

## Pillar 2: Entity Extraction Pipeline
- **Status**: [ ] not started
- **Why next**: The `knowledge_entities` and `knowledge_relationships` tables exist (migration 001) but nothing populates them. Pillar 4's graph/entity retrieval ("What do I know about person X?") is blocked until entities are extracted and stored. This is a distinct ML/NLP capability — not just parsing. Pillar 1's alias table, entity embeddings, and graph traversal functions are ready and waiting for data.
- **Scope**:
  - LLM-based Named Entity Recognition (NER) from text chunks — extract people, companies, projects, topics
  - Relationship inference between entities (e.g., "person X works at company Y", "project Z uses technology W")
  - Entity deduplication and linking (same person mentioned differently across sources) — leverages Pillar 1's alias table
  - Supabase writes to `knowledge_entities`, `knowledge_relationships`, and `knowledge_entity_aliases` tables
  - Entity extraction integrated as post-ingestion step (runs after chunks are stored)
- **Not included**: New file format parsers (Pillar 3), entity-based retrieval queries (Pillar 4), multi-agent orchestration (Pillar 5)
- **Depends on**: Pillar 1 (hardened entity/relationship contracts, alias table, entity embeddings, validated schema, Ollama auth for LLM-based NER)
- **Estimated specs**: ~4 (light: 1, standard: 2, heavy: 1)
- **Gate criteria**:
  - [ ] All specs for this pillar marked [x] in BUILD_ORDER.md
  - [ ] Entity extraction from a test corpus produces entities in `knowledge_entities` table
  - [ ] Relationship inference populates `knowledge_relationships` with correct source/target node IDs
  - [ ] Entity deduplication: same person mentioned as "John", "John Smith", "J. Smith" maps to one entity via alias table
  - [ ] Entity name embeddings populated for semantic entity search
  - [ ] Integration test: ingest 5 test documents → extract entities → verify entity count and relationship graph
  - [ ] `ruff check backend/src/ && mypy --strict backend/src/second_brain && python -m pytest tests/ -q` all pass
  - [ ] Manual validation: inspect extracted entities from a real Zoom transcript for accuracy

## Pillar 3: Multi-Format Ingestion
- **Status**: [ ] not started
- **Why next**: Current ingestion only handles markdown files. The PRD requires auto-detection and parsing of plain text, JSON, and Zoom transcripts. Without this, the system can't ingest the user's actual data sources (meeting transcripts, leadworks data, misc notes). Pillar 1's ingestion job tracking, dead letter queue, and data validation layer are ready to support robust multi-format ingestion.
- **Scope**:
  - File type auto-detection router (detect markdown, plain text, JSON, Zoom transcript format)
  - Plain text parser (chunk by paragraphs or fixed-size windows)
  - JSON parser (extract content fields, handle nested structures)
  - Zoom transcript parser (speaker turns, timestamps, segment-aware chunking)
  - Batch ingestion with progress reporting (ingest N files, report per-file status)
  - Entity extraction hook (trigger Pillar 2's extraction pipeline after ingestion)
  - Leverages Pillar 1's: ingestion job tracking, idempotency, dead letter queue, content dedup, chunk quality scoring, metadata enrichment
- **Not included**: PDF ingestion (Phase 3), audio/video transcription (Phase 3), retrieval changes (Pillar 4), Pydantic AI agents (Pillar 5)
- **Depends on**: Pillar 1 (flexible schema, ingestion pipeline infrastructure), Pillar 2 (entity extraction to hook into)
- **Estimated specs**: ~4 (light: 1, standard: 2, heavy: 1)
- **Gate criteria**:
  - [ ] All specs for this pillar marked [x] in BUILD_ORDER.md
  - [ ] Auto-detection correctly identifies markdown, plain text, JSON, and Zoom transcript formats
  - [ ] Each parser produces valid KnowledgeChunks with correct metadata (source_origin, knowledge_type)
  - [ ] Zoom transcript parser preserves speaker attribution and temporal ordering
  - [ ] Batch ingestion of 20+ files completes with progress reporting and per-file error handling
  - [ ] Ingestion job tracking: idempotency prevents re-ingestion, dead letters capture failures
  - [ ] Content dedup: re-ingesting same files skips already-stored content
  - [ ] Entity extraction runs automatically after ingestion (entities appear in `knowledge_entities`)
  - [ ] Integration test: ingest mixed-format directory (5 markdown, 3 text, 2 JSON, 2 Zoom) → all stored correctly
  - [ ] `ruff check backend/src/ && mypy --strict backend/src/second_brain && python -m pytest tests/ -q` all pass

## Pillar 4: Retrieval Engine + Accuracy Harness
- **Status**: [ ] not started
- **Why next**: With data flowing in (Pillars 1-3) and entities populated (Pillar 2), the retrieval engine can leverage Pillar 1's hybrid search, graph traversal, and temporal query functions. This pillar wires the Python retrieval layer to those Postgres primitives and measures accuracy. This is the "retrieval layer IS the product" pillar.
- **Scope**:
  - Graph/entity retrieval ("What do I know about person X?" — uses Pillar 1's graph traversal + entity search functions)
  - Multi-provider parallel retrieval (query Supabase pgvector + Mem0 in parallel, merge + deduplicate)
  - Wire hybrid search (Pillar 1's RRF function) into the Python retrieval pipeline
  - Retrieval accuracy evaluation harness (50-query test corpus with ground truth annotations)
  - Reranking A/B framework (compare Voyage rerank vs. no-rerank on the eval corpus)
  - Confidence calibration (tune thresholds based on eval results)
- **Not included**: Content generation agents (Phase 2), Pydantic AI migration (Pillar 5), Docker deployment (Pillar 5)
- **Depends on**: Pillar 1 (hybrid search, graph functions, entity search), Pillar 2 (entities for graph retrieval), Pillar 3 (multi-format data to retrieve from)
- **Estimated specs**: ~5 (light: 1, standard: 3, heavy: 1)
- **Gate criteria**:
  - [ ] All specs for this pillar marked [x] in BUILD_ORDER.md
  - [ ] Entity retrieval: query "What do I know about [person]?" returns relevant entities + connected chunks
  - [ ] Multi-provider: retrieval trace shows parallel queries to Supabase + Mem0 with merged results
  - [ ] Hybrid search: Python layer uses Pillar 1's RRF function, returns better results than vector-only
  - [ ] Precision@5 >= 80% on defined 50-query evaluation corpus with ground truth annotations
  - [ ] Recall@10 >= 80% on the same corpus
  - [ ] Reranking A/B: documented comparison showing Voyage rerank impact on Precision@5
  - [ ] Integration test: ingest test corpus → run 10 eval queries → all return expected top results
  - [ ] `ruff check backend/src/ && mypy --strict backend/src/second_brain && python -m pytest tests/ -q` all pass
  - [ ] Manual validation: 10 real queries against user's own data return relevant, accurate results

## Pillar 5: Pydantic AI Orchestrator + Docker Deployment
- **Status**: [ ] not started
- **Why last**: The current orchestrator (RecallOrchestrator, Planner, route_retrieval) works with 293+ tests. Migrating to Pydantic AI is an architectural upgrade that should happen after all features are proven and stable. Docker deployment is the final production-readiness step.
- **Scope**:
  - Migrate RecallOrchestrator to Pydantic AI Agent framework (agent definitions, tool registration, RunContext)
  - Multi-agent routing by query intent (orchestrator picks recall agent, entity agent, or synthesis agent)
  - Agent collaboration pattern (e.g., research agent feeds context to synthesis agent)
  - Conversation state integration with Pydantic AI agent context
  - MCP server rewired to use Pydantic AI agents as backend
  - Docker Compose setup (Postgres + backend service, health checks, auto-migration on startup)
  - New MCP tools: entity queries, trace inspection, provider health check
  - End-to-end integration test (ingest → extract entities → retrieve → chat → verify)
  - `.env.example` with documented configuration
- **Not included**: Content generation agents (Phase 2 — downstream consumer), web UI, multi-user auth
- **Depends on**: Pillars 1-4 (all features must be proven before architectural migration)
- **Estimated specs**: ~6 (light: 1, standard: 3, heavy: 2)
- **Gate criteria**:
  - [ ] All specs for this pillar marked [x] in BUILD_ORDER.md
  - [ ] RecallOrchestrator is a Pydantic AI Agent with tool registration and RunContext
  - [ ] Multi-agent routing: "What do I know about X?" routes to entity agent, "Summarize my notes on Y" routes to recall agent
  - [ ] `docker compose up` starts Postgres + backend, runs migrations, MCP server accessible
  - [ ] Same Docker Compose works on local machine and VPS (tested or documented)
  - [ ] All MCP tools (recall_search, chat, ingest_markdown, entity_query, trace, health) respond correctly
  - [ ] End-to-end test: ingest 10 docs → extract entities → query → chat → verify response grounded in context
  - [ ] All previous tests still pass (293+ baseline maintained or exceeded)
  - [ ] `ruff check backend/src/ && mypy --strict backend/src/second_brain && python -m pytest tests/ -q` all pass
  - [ ] Manual validation: full user workflow (ingest meeting notes → ask questions → get accurate answers)

## Pillar Order Summary
| # | Pillar | Depends On | Est. Specs | Status |
|---|--------|-----------|------------|--------|
| 1 | Data Infrastructure (PLUS ULTRA) | None | ~63 | [ ] |
| 2 | Entity Extraction Pipeline | 1 | ~4 | [ ] |
| 3 | Multi-Format Ingestion | 1, 2 | ~4 | [ ] |
| 4 | Retrieval Engine + Accuracy | 1, 2, 3 | ~5 | [ ] |
| 5 | Pydantic AI + Docker Deployment | 1, 2, 3, 4 | ~6 | [ ] |

**Total: ~82 specs across 5 pillars**

## Council Validation Notes
- **Validated by**: Claude Sonnet, GPT-5 Codex, Qwen 3.5 Plus, GLM-5, DeepSeek v3.2
- **Rounds**: 3 (propose → rebut → synthesize)
- **Key consensus changes from original proposal**:
  1. Entity extraction elevated to dedicated pillar (was split across Pillars 1-2)
  2. Ollama Cloud auth moved to Pillar 1 (was Pillar 3)
  3. Pydantic AI confirmed as Pillar 5 (council debated Pillar 1 vs 5, settled on 5 to avoid destabilizing 293 passing tests)
  4. Gate criteria tightened: `mypy --strict` specified, 50-query corpus with ground truth required, real Supabase migration validation in Pillar 1
  5. Docker stays in Pillar 5 but Pillar 1 gate includes real Supabase validation to catch "works in mock, fails in prod"
- **PLUS ULTRA expansion**: Pillar 1 expanded from 4 → 63 specs based on comprehensive data infrastructure research covering: Supabase best practices, pgvector optimization (HNSW tuning, partial indexes, halfvec), knowledge graph infrastructure (alias resolution, entity embeddings, temporal relationships), embedding versioning, hybrid search (RRF fusion), pipeline resilience (idempotency, dead letter queues), caching, data compaction, audit/compliance, multi-modal readiness, conflict resolution, query optimization, disaster recovery, data federation, and schema evolution patterns.
