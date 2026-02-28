# Build Order — Ultima Second Brain

Generated: 2026-02-27 | Pillars: 5 | Total Specs: 83 | Status: 9/83 complete

## Pillar 1: Data Infrastructure — PLUS ULTRA (64 specs)

### A. Type Safety & Config (4 specs)

- [x] `P1-01` **mypy-strict-compliance** (light) — Fix 5 mypy errors in schemas.py, retrieval_router.py, voyage.py to achieve zero-error mypy --strict
  - depends: none
  - touches: schemas.py, orchestration/retrieval_router.py, services/voyage.py
  - acceptance: `mypy --strict backend/src/second_brain` = 0 errors. All 293 existing tests pass.

- [x] `P1-02` **pydantic-settings-config** (standard) — Replace scattered os.getenv() in deps.py with a single Pydantic Settings class. Validate on startup. Bad config = immediate structured error with field name + expected type.
  - depends: P1-01
  - touches: deps.py (refactor), config.py (new), tests/test_config.py (new)
  - acceptance: All env vars read from one Settings class. Missing required var raises ValidationError with field name. Existing tests pass with env vars set.

- [x] `P1-03` **structured-json-logging** (standard) — Replace print/logging.info with structlog JSON output. Add correlation_id to all operations. Log level configurable via Settings.
  - depends: P1-02
  - touches: logging_config.py (new), all service files (add correlation_id), deps.py
  - acceptance: All log output is valid JSON with timestamp, level, correlation_id, module. Log level changes via env var. No bare print() statements remain.

- [x] `P1-04` **error-taxonomy** (standard) — Define error hierarchy: SecondBrainError base, with ProviderError, ValidationError, SchemaError, IngestionError, RetrievalError subtypes. Each error has code + context dict + retry_hint bool.
  - depends: P1-02
  - touches: errors.py (new), all service files (replace generic exceptions), tests/test_errors.py (new)
  - acceptance: All service methods raise typed errors from taxonomy. Each error serializes to {code, message, context, retry_hint}. Generic Exception catches replaced.

### B. Schema & Migrations (5 specs)

- [x] `P1-05` **flexible-metadata-schema** (standard) — Extend SourceOriginValue to include zoom, json, text, leadworks. Ensure KnowledgeChunk.metadata accepts arbitrary source-specific data via dict[str, Any].
  - depends: P1-01
  - touches: contracts/knowledge.py, migrations/ (002_extend_source_origin.sql)
  - acceptance: KnowledgeChunk instantiates with source_origin="zoom". Metadata field accepts nested dicts. Existing tests pass.

- [x] `P1-06` **schema-versioning** (standard) — Add schema_versions table tracking migration checksums. Drift detection: compare expected vs actual schema on startup. Alert on mismatch.
  - depends: P1-05
  - touches: migrations/003_schema_versions.sql (new), services/schema_manager.py (new), tests/test_schema_manager.py (new)
  - acceptance: schema_versions table tracks all applied migrations with SHA-256 checksums. Startup check detects drift (modified migration file). Drift = structured error with details.

- [x] `P1-07` **migration-runner** (standard) — Python migration runner: auto-apply pending, dry-run mode, rollback support, concurrent lock (advisory lock prevents parallel runs).
  - depends: P1-06
  - touches: services/migration_runner.py (new), tests/test_migration_runner.py (new)
  - acceptance: Runner applies pending migrations in order. Dry-run shows SQL without executing. Two concurrent runners: one waits, other proceeds. Rollback reverses last migration.

- [x] `P1-08` **schema-documentation** (light) — Auto-generate schema docs from migration files. Table descriptions, column types, indexes, constraints in markdown.
  - depends: P1-06
  - touches: scripts/generate_schema_docs.py (new), docs/schema.md (generated)
  - acceptance: Running script produces accurate markdown doc matching actual DB schema. All tables, columns, indexes documented.

- [x] `P1-09` **additive-migration-policy** (light) — CI check that new migrations are additive-only (no DROP COLUMN, no ALTER TYPE to smaller). Enforced via simple SQL parser.
  - depends: P1-07
  - touches: scripts/check_migrations.py (new), tests/test_migration_policy.py (new)
  - acceptance: Migration with DROP COLUMN fails check. Migration with ADD COLUMN passes. ALTER TYPE from text to varchar fails.

### C. Database Core (7 specs)

- [ ] `P1-10` **connection-pool-circuit-breaker** (standard) — Supabase connection pool with retry logic and circuit breaker. Pool configurable via Settings. Health check endpoint. Metrics: active connections, failed attempts, circuit state.
  - depends: P1-02, P1-04
  - touches: services/supabase.py (refactor), services/pool.py (new), tests/test_pool.py (new)
  - acceptance: Pool retries 3x on connection failure. Circuit opens after 5 consecutive failures, half-opens after 30s. Health check returns pool stats. Metrics dict available.

- [ ] `P1-11` **transaction-management** (standard) — Transaction context manager for multi-table atomic writes. Partial writes roll back. Nested transaction support via savepoints.
  - depends: P1-10
  - touches: services/supabase.py, services/transaction.py (new), tests/test_transactions.py (new)
  - acceptance: Multi-table insert in transaction: success = all committed, failure = all rolled back. Savepoint in nested transaction: inner failure rolls back to savepoint, outer succeeds.

- [ ] `P1-12` **concurrent-write-safety** (standard) — Ensure parallel ingestion jobs don't corrupt data. Row-level locking on chunk upserts. Conflict resolution: last-write-wins with audit trail.
  - depends: P1-11
  - touches: services/supabase.py, tests/test_concurrent_writes.py (new)
  - acceptance: Two parallel ingestion jobs writing overlapping chunks: no data corruption, no lost updates. Audit log shows conflict resolution.

- [ ] `P1-13` **data-integrity-constraints** (standard) — Add NOT NULL, CHECK, UNIQUE, FK constraints to all tables. Enforce at DB level what contracts enforce at Python level.
  - depends: P1-05
  - touches: migrations/004_integrity_constraints.sql (new), tests/test_constraints.py (new)
  - acceptance: Insert with NULL required field fails at DB. Duplicate content_hash rejected by UNIQUE. FK violation on non-existent source_id rejected. All constraints documented.

- [ ] `P1-14` **content-addressable-dedup** (standard) — SHA-256 hash of chunk content stored in content_hash column. UNIQUE constraint. On duplicate: update metadata, don't create new row. Track superseded chunks.
  - depends: P1-13
  - touches: contracts/knowledge.py, services/supabase.py, migrations/005_content_hash.sql (new), tests/test_dedup.py (new)
  - acceptance: Same content ingested twice = one row. content_hash matches SHA-256 of content. Metadata updated on re-ingestion. Superseded chunk has status="superseded".

- [ ] `P1-15` **chunk-status-lifecycle** (standard) — Chunks have status: active, superseded, archived, deleted (soft). Status transitions enforced (active->superseded, active->archived, any->deleted). Only active chunks returned in search by default.
  - depends: P1-14
  - touches: contracts/knowledge.py, services/supabase.py, migrations/006_chunk_status.sql (new), tests/test_chunk_lifecycle.py (new)
  - acceptance: New chunk = active. Re-ingested chunk supersedes old. Archived chunk excluded from search. Deleted = soft delete, restorable. Invalid transition (deleted->active) raises error.

- [ ] `P1-16` **optimistic-locking** (light) — Add version column to knowledge_chunks. Updates must include current version. Concurrent update to same chunk: one succeeds, other gets StaleDataError.
  - depends: P1-15
  - touches: contracts/knowledge.py, services/supabase.py, migrations/007_optimistic_locking.sql (new), tests/test_optimistic_locking.py (new)
  - acceptance: Update with correct version succeeds, version incremented. Update with stale version raises StaleDataError. Concurrent updates: exactly one wins.

### D. Supabase Search Infrastructure (8 specs)

- [ ] `P1-17` **full-text-search** (standard) — Add tsvector column to knowledge_chunks, GIN index. PostgreSQL full-text search RPC function. Supports AND/OR/phrase queries.
  - depends: P1-13
  - touches: migrations/008_fulltext_search.sql (new), services/supabase.py, tests/test_fulltext_search.py (new)
  - acceptance: tsvector column auto-populated via trigger. GIN index created. RPC: search "machine learning" returns chunks containing both words. Phrase search works.

- [ ] `P1-18` **hybrid-search-rpc** (heavy) — RRF (Reciprocal Rank Fusion) function combining vector similarity + full-text relevance. Single RPC call returns fused results. Configurable weights.
  - depends: P1-17
  - touches: migrations/009_hybrid_search.sql (new), services/supabase.py, tests/test_hybrid_search.py (new)
  - acceptance: Hybrid search returns better results than vector-only or keyword-only for test queries. RRF weights configurable. Single RPC call, not two separate calls merged in Python.

- [ ] `P1-19` **trigram-fuzzy-entity-search** (standard) — pg_trgm extension + GIN trigram index on entity names. Fuzzy search handles typos: "Jonh Smth" finds "John Smith".
  - depends: P1-13
  - touches: migrations/010_trigram_search.sql (new), services/supabase.py, tests/test_trigram_search.py (new)
  - acceptance: pg_trgm enabled. "Jonh" finds "John" with similarity > 0.3. "Acme Crp" finds "Acme Corp". Index used (EXPLAIN shows GIN scan).

- [ ] `P1-20` **graph-traversal-cte** (standard) — Recursive CTE for graph traversal: given entity, find all connected entities within N hops. Returns path + relationship types.
  - depends: P1-13
  - touches: migrations/011_graph_traversal.sql (new), services/supabase.py, tests/test_graph_traversal.py (new)
  - acceptance: Entity "John Smith" with 2-hop traversal returns connected entities through relationships. Path includes relationship types. Max depth configurable (default 2).

- [ ] `P1-21` **temporal-query-functions** (standard) — SQL functions for time-bounded queries: chunks created/modified since date, entities first/last seen, relationship timeline.
  - depends: P1-13
  - touches: migrations/012_temporal_queries.sql (new), services/supabase.py, tests/test_temporal_queries.py (new)
  - acceptance: "knowledge since 2026-02-20" returns only chunks created after that date. Entity first_seen/last_seen computed correctly. Timeline query returns chronologically ordered results.

- [ ] `P1-22` **database-views** (light) — Create views: v_active_chunks (only active status), v_entity_summary (entity + relationship count + chunk count), v_source_stats (chunks per source).
  - depends: P1-15, P1-17
  - touches: migrations/013_views.sql (new), tests/test_views.py (new)
  - acceptance: v_active_chunks excludes non-active. v_entity_summary shows correct counts. v_source_stats matches actual chunk distribution.

- [ ] `P1-23` **materialized-views** (standard) — Materialized views for expensive queries: mv_entity_graph (pre-computed 2-hop graph), mv_search_stats (query performance). Refresh strategy documented.
  - depends: P1-22
  - touches: migrations/014_materialized_views.sql (new), services/supabase.py (refresh functions), tests/test_materialized_views.py (new)
  - acceptance: mv_entity_graph returns pre-computed graph data. REFRESH MATERIALIZED VIEW works. Refresh strategy: after batch ingestion or on schedule.

- [ ] `P1-24` **statistics-functions** (light) — SQL functions: total_chunks(), chunks_by_type(), chunks_by_source(), avg_chunk_size(), entity_count(), relationship_count(). Used by health dashboard.
  - depends: P1-22
  - touches: migrations/015_statistics.sql (new), tests/test_statistics.py (new)
  - acceptance: All functions return correct counts matching actual data. Zero data = zero counts (not errors).

### E. Indexing & Query Optimization (5 specs)

- [ ] `P1-25` **hnsw-tuning** (standard) — Tune HNSW parameters: m=24, ef_construction=128. Benchmark at 1K, 10K, 100K vectors. Document recall@10 and latency at each scale.
  - depends: P1-13
  - touches: migrations/016_hnsw_tuning.sql (new), scripts/benchmark_hnsw.py (new), docs/hnsw_benchmarks.md (generated)
  - acceptance: HNSW index rebuilt with m=24, ef_construction=128. Benchmark script generates report with recall@10 and p50/p95 latency at 1K/10K/100K.

- [ ] `P1-26` **partial-hnsw-indexes** (standard) — Create per-knowledge_type partial HNSW indexes. Queries filtering by type use partial index (faster than full scan + filter).
  - depends: P1-25
  - touches: migrations/017_partial_indexes.sql (new), tests/test_partial_indexes.py (new)
  - acceptance: Partial indexes created for each knowledge_type. EXPLAIN ANALYZE shows partial index used for type-filtered queries. Query time < full index query time for filtered queries.

- [ ] `P1-27` **halfvec-migration** (standard) — Migrate embedding column from vector(1024) to halfvec(1024). 50% storage reduction with <1% accuracy loss. Benchmark before/after.
  - depends: P1-25
  - touches: migrations/018_halfvec.sql (new), scripts/benchmark_halfvec.py (new), docs/halfvec_benchmarks.md (generated)
  - acceptance: Column type is halfvec(1024). Storage reduced ~50%. Recall@10 difference < 1% vs full vector. All existing queries work unchanged.

- [ ] `P1-28` **composite-covering-indexes** (standard) — Add composite indexes for common query patterns: (source_origin, created_at), (knowledge_type, status), (content_hash). Covering indexes where beneficial.
  - depends: P1-13
  - touches: migrations/019_composite_indexes.sql (new), tests/test_index_usage.py (new)
  - acceptance: EXPLAIN ANALYZE shows new indexes used for filtered queries. No sequential scans on indexed columns for common queries.

- [ ] `P1-29` **query-performance-baselines** (standard) — Establish p50/p95 baselines for 10+ core queries using EXPLAIN ANALYZE. Store as test fixtures. Regression test: query time must stay within 2x baseline.
  - depends: P1-28
  - touches: scripts/query_baselines.py (new), tests/test_query_performance.py (new), docs/query_baselines.md (generated)
  - acceptance: 10+ queries baselined with p50/p95. Regression test fails if any query exceeds 2x baseline. Results documented.

### F. Knowledge Graph Infrastructure (4 specs)

- [ ] `P1-30` **entity-contract-hardening** (standard) — Validate KnowledgeEntity and KnowledgeRelationship contracts ready for extraction. Add missing fields (confidence, extraction_model, first_seen, last_seen). Supabase write helpers.
  - depends: P1-05
  - touches: contracts/knowledge.py, services/supabase.py, migrations/020_entity_fields.sql (new), tests/test_entity_contracts.py (new)
  - acceptance: KnowledgeEntity has confidence, extraction_model, first_seen, last_seen fields. Round-trip through Supabase insert/read. Entity with source_chunk_ids validates.

- [ ] `P1-31` **entity-alias-table** (standard) — Create knowledge_entity_aliases table: alias_text, canonical_entity_id, alias_type (exact/abbreviation/nickname/typo), confidence. Trigram index on alias_text.
  - depends: P1-30, P1-19
  - touches: migrations/021_entity_aliases.sql (new), contracts/knowledge.py, tests/test_entity_aliases.py (new)
  - acceptance: Alias table created with FK to knowledge_entities. Trigram index on alias_text. "J. Smith" alias resolves to "John Smith" entity. Alias types enforced.

- [ ] `P1-32` **entity-name-embedding** (standard) — Add name_embedding halfvec(1024) column to knowledge_entities. Semantic entity search: find entities by meaning, not just text match.
  - depends: P1-30, P1-27
  - touches: migrations/022_entity_embedding.sql (new), services/supabase.py, tests/test_entity_embedding.py (new)
  - acceptance: Entity name_embedding populated. Semantic search: "machine learning researcher" finds entity "Dr. AI Smith, ML Lab". HNSW index on name_embedding.

- [ ] `P1-33` **temporal-relationship-indexing** (standard) — Index relationships by time: valid_from, valid_to columns. Query: "Who did X work with in 2025?" Temporal relationships support open-ended (valid_to=NULL).
  - depends: P1-30
  - touches: migrations/023_temporal_relationships.sql (new), tests/test_temporal_relationships.py (new)
  - acceptance: Relationships have valid_from/valid_to. Time-bounded query returns only relationships active in range. NULL valid_to = still active.

### G. Embedding Infrastructure (4 specs)

- [ ] `P1-34` **embedding-model-registry** (standard) — Table tracking embedding models: model_name, dimension, provider, version, is_active. Each chunk links to model that produced its embedding.
  - depends: P1-13
  - touches: migrations/024_embedding_registry.sql (new), contracts/knowledge.py, services/voyage.py, tests/test_embedding_registry.py (new)
  - acceptance: embedding_models table populated with voyage-4-large entry. knowledge_chunks.embedding_model_id FK enforced. Model version tracked per chunk.

- [ ] `P1-35` **embedding-cache** (standard) — Cache table: content_hash -> embedding vector. Re-ingestion of same content skips Voyage API call. TTL-based expiry.
  - depends: P1-14, P1-34
  - touches: migrations/025_embedding_cache.sql (new), services/voyage.py, tests/test_embedding_cache.py (new)
  - acceptance: First embed = API call + cache write. Second embed of same content = cache hit, no API call. Expired cache entries cleaned up. Cache hit rate metric available.

- [ ] `P1-36` **batch-re-embedding-pipeline** (standard) — Re-embed all chunks when model changes. Batch processing with progress tracking, rate limiting, resume-on-failure.
  - depends: P1-34, P1-35
  - touches: services/embedding_pipeline.py (new), tests/test_embedding_pipeline.py (new)
  - acceptance: Pipeline re-embeds N chunks with new model. Progress reported. Rate limited (no 429s). Failure at chunk 50/100 = resume from 50. Old embeddings preserved until new ones verified.

- [ ] `P1-37` **embedding-pipeline-validation** (light) — Validate embedding pipeline: dimension check, null detection, model version consistency. Alert on anomalies.
  - depends: P1-36
  - touches: services/embedding_pipeline.py, tests/test_embedding_validation.py (new)
  - acceptance: Dimension mismatch detected and rejected. NULL embedding flagged. Model version inconsistency (chunk says model A, registry says model B) alerted.

### H. Data Quality (4 specs)

- [ ] `P1-38` **input-validation-layer** (standard) — Validate all incoming data before storage: content length limits, encoding check (UTF-8), metadata schema validation, source_origin validation.
  - depends: P1-04, P1-05
  - touches: services/validation.py (new), tests/test_validation.py (new)
  - acceptance: Empty content rejected. Content > 50KB rejected with error. Non-UTF-8 rejected. Invalid source_origin rejected. All with structured error messages.

- [ ] `P1-39` **chunk-quality-scoring** (standard) — Score chunks on quality: content length, information density (unique words / total words), language detection, formatting quality. Low-quality chunks flagged.
  - depends: P1-38
  - touches: services/quality.py (new), contracts/knowledge.py (add quality_score field), tests/test_quality.py (new)
  - acceptance: quality_score 0.0-1.0 computed for each chunk. Very short chunks (<20 words) score low. Repetitive content scores low. Threshold configurable. Flagged chunks queryable.

- [ ] `P1-40` **metadata-enrichment** (standard) — Auto-extract metadata on ingestion: word_count, language (langdetect), estimated_topic (from content), reading_time. Store in metadata JSONB.
  - depends: P1-38
  - touches: services/enrichment.py (new), tests/test_enrichment.py (new)
  - acceptance: Ingested chunk has word_count, language, estimated_topic, reading_time in metadata. Language detection correct for English/Spanish test content. Word count matches actual.

- [ ] `P1-41` **data-lineage-tracking** (standard) — Track provenance: source_chain field records full transformation history (original_file -> chunked -> embedded -> enriched). Queryable lineage.
  - depends: P1-38
  - touches: contracts/knowledge.py, services/supabase.py, migrations/026_lineage.sql (new), tests/test_lineage.py (new)
  - acceptance: Chunk source_chain shows: [original_file, chunk_step, embed_step, enrich_step]. Query "all chunks from file X" returns correct set. Lineage preserved through re-ingestion.

### I. Pipeline Resilience (4 specs)

- [ ] `P1-42` **ingestion-job-tracking** (standard) — Table tracking ingestion jobs: job_id, status (pending/running/completed/failed), source_file, chunk_count, idempotency_key. Prevents double-ingestion.
  - depends: P1-11
  - touches: migrations/027_ingestion_jobs.sql (new), services/ingestion_tracker.py (new), tests/test_ingestion_tracker.py (new)
  - acceptance: Job created on ingestion start. Same idempotency_key = skip (not duplicate). Job status tracks progress. Failed job can be retried. Completed job has chunk_count.

- [ ] `P1-43` **dead-letter-queue** (standard) — Failed chunks go to dead_letter_chunks table instead of crashing pipeline. Includes error message, retry_count, original payload. Manual or auto-retry.
  - depends: P1-42
  - touches: migrations/028_dead_letter.sql (new), services/dead_letter.py (new), tests/test_dead_letter.py (new)
  - acceptance: Chunk that fails embedding goes to DLQ, pipeline continues. DLQ entry has error details. Retry moves chunk back to processing. Max retries enforced.

- [ ] `P1-44` **provider-rate-limiter** (standard) — Token bucket rate limiter for Voyage, Ollama, Supabase API calls. Configurable per-provider limits. Prevents 429 errors during batch operations.
  - depends: P1-02
  - touches: services/rate_limiter.py (new), services/voyage.py, services/llm.py, tests/test_rate_limiter.py (new)
  - acceptance: Rate limiter enforces max requests/second per provider. Burst of 100 embed requests: no 429s, requests throttled. Rate configurable via Settings.

- [ ] `P1-45` **provider-health-monitor** (standard) — Unified health check for all providers (Supabase, Voyage, Ollama, Mem0). Check on startup. Periodic re-check. Status exposed via health endpoint.
  - depends: P1-10, P1-44
  - touches: services/health.py (new), tests/test_health.py (new)
  - acceptance: Health check returns status per provider. Unhealthy provider logged with structured error. Health endpoint returns JSON with all provider statuses. Startup fails gracefully if critical provider down.

### J. Data Operations (5 specs)

- [ ] `P1-46` **backup-restore** (standard) — Full JSON backup of all tables. Restore to fresh DB produces identical results. Backup includes schema version for compatibility.
  - depends: P1-06
  - touches: services/backup.py (new), tests/test_backup.py (new)
  - acceptance: Backup produces JSON with all tables + schema version. Restore to empty DB + verify: chunk counts match, content identical, entity relationships intact. Round-trip test passes.

- [ ] `P1-47` **embedding-free-backup** (standard) — Export all data WITHOUT embedding vectors. Smaller file, vendor-independent. Re-embeddable after restore using batch pipeline.
  - depends: P1-46, P1-36
  - touches: services/backup.py, tests/test_backup.py
  - acceptance: Embedding-free backup is significantly smaller than full backup. Restore + re-embed produces working system. Content hashes match original.

- [ ] `P1-48` **bulk-operations** (standard) — Bulk re-embed, re-index, re-score operations. Progress tracking, resume-on-failure, dry-run mode.
  - depends: P1-36, P1-39
  - touches: services/bulk_ops.py (new), tests/test_bulk_ops.py (new)
  - acceptance: Bulk re-embed 100 chunks with progress callback. Bulk re-score updates quality scores. Dry-run shows what would change without changing. Resume after failure at correct position.

- [ ] `P1-49` **data-cleanup-tools** (standard) — Tools: purge soft-deleted chunks older than N days, remove orphaned entities (no linked chunks), compact superseded chunks, vacuum analyze.
  - depends: P1-15
  - touches: services/cleanup.py (new), tests/test_cleanup.py (new)
  - acceptance: Purge removes soft-deleted chunks older than 30 days. Orphan entity cleanup removes entities with 0 source_chunk_ids. Compact removes superseded chunks. Vacuum runs without error.

- [ ] `P1-50` **ttl-staleness-scoring** (standard) — Score chunks by freshness: recently accessed = fresh, old + unaccessed = stale. TTL configurable per source_origin. Stale chunks deprioritized in search.
  - depends: P1-15
  - touches: contracts/knowledge.py (add last_accessed, staleness_score), services/supabase.py, migrations/029_staleness.sql (new), tests/test_staleness.py (new)
  - acceptance: last_accessed updated on retrieval. Staleness score computed based on age + access pattern. Stale chunks ranked lower in search. TTL configurable per source_origin.

### K. Audit, Compliance & Recovery (5 specs)

- [ ] `P1-51` **audit-log-triggers** (standard) — Trigger-based audit log: every INSERT, UPDATE, DELETE on knowledge_chunks, knowledge_entities, knowledge_relationships captured with old/new data, timestamp, operation type.
  - depends: P1-13
  - touches: migrations/030_audit_log.sql (new), tests/test_audit_log.py (new)
  - acceptance: Insert chunk -> audit log entry with operation=INSERT, new_data. Update chunk -> entry with old_data + new_data. Delete -> entry with old_data. Audit log queryable by table, operation, time range.

- [ ] `P1-52` **data-export-gdpr** (standard) — Full data export for a given user/source: all chunks, entities, relationships, audit log entries. JSON format. Supports "right to be forgotten" deletion.
  - depends: P1-51
  - touches: services/export.py (new), tests/test_export.py (new)
  - acceptance: Export for source_id returns all related data as JSON. Deletion removes all traces (chunks, entities, relationships, audit entries). Post-deletion query returns nothing.

- [ ] `P1-53` **source-priority-system** (light) — Sources have priority: primary, secondary, tertiary. Conflicting information from higher-priority source wins. Priority queryable.
  - depends: P1-05
  - touches: contracts/knowledge.py, migrations/031_source_priority.sql (new), tests/test_source_priority.py (new)
  - acceptance: Sources have priority field. Two chunks with same content_hash from different sources: higher priority source's metadata used. Priority queryable via v_source_stats.

- [ ] `P1-54` **conflict-detection-view** (standard) — View that surfaces conflicting information: same entity with different attributes from different sources, chunks with similar content but different claims.
  - depends: P1-14, P1-30
  - touches: migrations/032_conflict_detection.sql (new), tests/test_conflict_detection.py (new)
  - acceptance: Two sources claiming different roles for same entity -> conflict surfaced. Similar chunks (high cosine similarity) with contradicting metadata -> flagged. View queryable.

- [ ] `P1-55` **disaster-recovery-prep** (standard) — Document and configure: PITR (point-in-time recovery) for Supabase, nightly pg_dump backup, restore procedure tested, RTO/RPO targets defined.
  - depends: P1-46
  - touches: docs/disaster_recovery.md (new), scripts/nightly_backup.sh (new), tests/test_disaster_recovery.py (new)
  - acceptance: Nightly backup script works. Restore procedure documented and tested. PITR enabled or documented (Supabase Pro feature). RTO/RPO targets documented.

### L. Multi-Modal & Future-Proofing (3 specs)

- [ ] `P1-56` **content-type-column** (light) — Add content_type column to knowledge_chunks: text, code, image_description, audio_transcript, structured_data. Default "text" for existing rows. Queries can filter by content_type.
  - depends: P1-13
  - touches: contracts/knowledge.py, migrations/033_content_type.sql (new), tests/test_content_type.py (new)
  - acceptance: Column added with default "text". Existing rows migrated. New chunks can specify content_type. Search filters by content_type work.

- [ ] `P1-57` **multi-vector-readiness** (light) — Add secondary_embedding column (nullable halfvec). Supports future multi-modal embeddings (text + image from same chunk). Index ready but empty.
  - depends: P1-27
  - touches: migrations/034_multi_vector.sql (new), contracts/knowledge.py, tests/test_multi_vector.py (new)
  - acceptance: secondary_embedding column exists (nullable halfvec). Existing data unaffected. Column accepts embeddings. Index created but no data required.

- [ ] `P1-58` **metadata-conventions-doc** (light) — Document metadata field conventions: required fields per source_origin, optional enrichment fields, naming conventions. Living document updated as new sources added.
  - depends: P1-40
  - touches: docs/metadata_conventions.md (new)
  - acceptance: Document lists metadata fields per source_origin. Required vs optional clearly marked. Examples for each source type.

### Integration Proof & Tests (6 specs)

- [ ] `P1-59` **storage-metrics-dashboard** (standard) — Python function returning storage metrics: total chunks, chunks by type/source/status, avg embedding size, index sizes, cache hit rate, dead letter count.
  - depends: P1-24, P1-35, P1-43
  - touches: services/metrics.py (new), tests/test_metrics.py (new)
  - acceptance: Metrics function returns dict with all stats. Zero data = zero values (not errors). Stats match actual DB state.

- [ ] `P1-60` **e2e-fortress-test** (heavy) — End-to-end test: ingest -> deduplicate -> embed -> store -> hybrid search -> entity search -> graph traverse -> temporal query -> backup -> restore -> concurrent ingestion -> soft delete -> restore -> audit log — ALL PASS in one test.
  - depends: all P1 specs
  - touches: tests/test_e2e_fortress.py (new)
  - acceptance: Single test exercises entire Pillar 1 infrastructure. All operations succeed. Audit log captures everything. This is the integration proof.

- [ ] `P1-61` **test-fixtures-seed-data** (standard) — Create 12+ test fixtures across 4 formats (markdown, text, JSON, Zoom-like). Include edge cases: empty content, huge content, unicode, nested metadata.
  - depends: P1-05
  - touches: tests/fixtures/ (new directory), tests/conftest.py, tests/test_fixtures.py (new)
  - acceptance: 12+ fixture files created. Edge cases covered. Fixtures loadable via pytest conftest. Used by other test specs.

- [ ] `P1-62` **real-provider-test-harness** (standard) — Test harness that runs against real Supabase + Voyage + Ollama (not mocks). Skipped in CI, run manually. Validates real provider integration.
  - depends: P1-10, P1-34
  - touches: tests/test_real_providers.py (new)
  - acceptance: Tests connect to real Supabase, embed with real Voyage, query real Ollama. All pass. Skipped when env vars not set. Clear setup docs.

- [ ] `P1-63` **rls-policies-prep** (light) — Write RLS policies for all tables (user_id-based row isolation). Policies DISABLED but present. Add user_id column to all tables (nullable, for future multi-user).
  - depends: P1-13
  - touches: migrations/035_rls_prep.sql (new), tests/test_rls_prep.py (new)
  - acceptance: user_id column on all tables (nullable). RLS policies written but DISABLED. Enabling policies doesn't break anything. Future-ready for multi-user.

- [ ] `P1-64` **ollama-cloud-auth** (standard) — Add optional API key auth to OllamaLLMService. When OLLAMA_API_KEY set, send Authorization: Bearer header. Local Ollama (no key) works unchanged. Model availability check.
  - depends: P1-02
  - touches: services/llm.py, deps.py, tests/test_llm_service.py
  - acceptance: OllamaLLMService works with no key (local) and with API key (cloud mock). Health check + model list works for both modes.

- [ ] `P1-GATE` **pillar-1-gate** — Run ALL Pillar 1 gate criteria from PILLARS.md (42 criteria)
  - depends: P1-01 through P1-64
  - acceptance: Every gate criterion in PILLARS.md Pillar 1 section passes. Full test suite green. ruff + mypy --strict + pytest all pass. E2E fortress test passes.

## Pillar 2: Entity Extraction Pipeline (4 specs)

- [ ] `P2-01` **entity-extraction-service** (heavy) — LLM-based NER service using Ollama. Extract people, companies, projects, topics from text chunks. Return structured KnowledgeEntity list with confidence scores.
  - depends: P1-GATE
  - touches: services/entity_extraction.py (new), tests/test_entity_extraction.py (new)
  - acceptance: Given chunk about "John Smith from Acme Corp discussing Project Alpha", extracts [{name: "John Smith", type: "person", confidence: 0.95}, {name: "Acme Corp", type: "org"}, {name: "Project Alpha", type: "project"}]. Uses Ollama LLM.

- [ ] `P2-02` **relationship-inference** (standard) — Infer relationships between extracted entities using LLM. Determine types (works_at, discussed, related_to, manages, member_of). Write to KnowledgeRelationship with confidence.
  - depends: P2-01
  - touches: services/entity_extraction.py, tests/test_relationship_inference.py (new)
  - acceptance: Entities "John Smith" (person) + "Acme Corp" (org) from same chunk -> "works_at" relationship with correct source/target IDs and confidence score.

- [ ] `P2-03` **entity-deduplication** (standard) — Deduplicate entities across chunks leveraging Pillar 1's alias table + entity name embeddings. "John", "John Smith", "J. Smith" -> one canonical entity with aliases.
  - depends: P2-01, P1-31, P1-32
  - touches: services/entity_extraction.py, services/voyage.py, tests/test_entity_dedup.py (new)
  - acceptance: Three chunks mentioning "John", "John Smith", "J. Smith" produce one entity with three aliases. Dedup uses both trigram similarity and embedding similarity.

- [ ] `P2-04` **entity-ingestion-hook** (standard) — Wire entity extraction as post-ingestion step. After chunks stored, extraction runs automatically. Writes entities, relationships, and aliases to Supabase.
  - depends: P2-01, P2-02, P2-03
  - touches: ingestion/markdown.py, services/entity_extraction.py, deps.py, tests/test_entity_ingestion.py (new)
  - acceptance: Ingest 5 markdown files -> entities in knowledge_entities -> relationships in knowledge_relationships -> aliases in knowledge_entity_aliases. Automatic, no manual trigger.

- [ ] `P2-GATE` **pillar-2-gate** — Run all Pillar 2 gate criteria from PILLARS.md
  - depends: P2-01 through P2-04
  - acceptance: All Pillar 2 gate criteria pass. Entity extraction produces entities. Relationships populated. Dedup merges variants via alias table. Entity name embeddings populated. ruff + mypy --strict + pytest all pass.

## Pillar 3: Multi-Format Ingestion (4 specs)

- [ ] `P3-01` **file-type-detector** (light) — Auto-detection router: identifies markdown, plain text, JSON, Zoom transcript. Routes to correct parser. Unknown formats = "unsupported" gracefully.
  - depends: P1-GATE
  - touches: ingestion/detector.py (new), tests/test_detector.py (new)
  - acceptance: Correctly identifies .md, .txt, .json, Zoom transcript format. Unknown -> "unsupported" error. Unit tests cover all variants.

- [ ] `P3-02` **text-json-parsers** (standard) — Plain text parser (paragraph-based chunking) + JSON parser (extract content fields, handle nesting). Both produce valid KnowledgeChunks.
  - depends: P3-01, P1-05
  - touches: ingestion/text_parser.py (new), ingestion/json_parser.py (new), tests/test_parsers.py (new)
  - acceptance: Text chunked by paragraphs with correct chunk_index. JSON nested fields extracted. Both produce KnowledgeChunks with correct source_origin.

- [ ] `P3-03` **zoom-transcript-parser** (heavy) — Parse Zoom transcripts: speaker attribution, timestamps, segment-aware chunking. Preserve who said what and when. Handle real-world messy transcripts.
  - depends: P3-01, P1-05
  - touches: ingestion/zoom_parser.py (new), tests/test_zoom_parser.py (new)
  - acceptance: 3-speaker transcript parsed into chunks with speaker metadata + timestamps. Temporal ordering preserved. source_origin="zoom". Handles edge cases (empty segments, overlapping timestamps).

- [ ] `P3-04` **batch-ingestion-pipeline** (standard) — Unified pipeline: ingest N files from directory with auto-detection, progress reporting, per-file error handling, DLQ integration, entity extraction hook.
  - depends: P3-01, P3-02, P3-03, P2-04, P1-42, P1-43
  - touches: ingestion/pipeline.py (new), mcp_server.py, tests/test_batch_ingestion.py (new)
  - acceptance: Mixed-format directory (5 md, 3 txt, 2 JSON, 2 Zoom) -> all stored -> entities extracted -> progress dict with per-file status. Failed files go to DLQ.

- [ ] `P3-GATE` **pillar-3-gate** — Run all Pillar 3 gate criteria from PILLARS.md
  - depends: P3-01 through P3-04
  - acceptance: All Pillar 3 gate criteria pass. Auto-detection works for 4 formats. Zoom preserves speakers. Batch ingestion of 20+ files completes. Entity extraction auto-runs. ruff + mypy --strict + pytest all pass.

## Pillar 4: Retrieval Engine + Accuracy Harness (5 specs)

- [ ] `P4-01` **entity-retrieval** (standard) — Graph/entity retrieval: "What do I know about person X?" queries knowledge_entities + relationships via Pillar 1's graph traversal, returns connected chunks.
  - depends: P2-GATE, P1-20
  - touches: services/entity_search.py (new), agents/recall.py, orchestration/retrieval_router.py, tests/test_entity_retrieval.py (new)
  - acceptance: "What do I know about John Smith?" returns entity + connected chunks via graph traversal. Results include relationship context.

- [ ] `P4-02` **hybrid-retrieval-wiring** (standard) — Wire Pillar 1's hybrid search RPC into Python retrieval pipeline. Replace vector-only with RRF hybrid. Configurable weights.
  - depends: P1-18
  - touches: agents/recall.py, orchestration/retrieval_router.py, tests/test_hybrid_retrieval.py (new)
  - acceptance: Retrieval uses hybrid search (vector + keyword + RRF). Better results than vector-only for test queries. Weights configurable via Settings.

- [ ] `P4-03` **multi-provider-parallel** (standard) — Query Supabase pgvector + Mem0 in parallel, merge + deduplicate results by content similarity. Trace shows parallel execution.
  - depends: P1-GATE
  - touches: agents/recall.py, orchestration/retrieval_router.py, services/memory.py, tests/test_parallel_retrieval.py (new)
  - acceptance: Trace shows parallel queries. Merged results deduplicated. Latency < sum of individual latencies.

- [ ] `P4-04` **eval-corpus-harness** (heavy) — 50-query evaluation corpus with ground truth. Precision@5 and Recall@10 measurement. Reranking A/B comparison. Structured accuracy report.
  - depends: P4-01, P4-02, P4-03, P3-GATE
  - touches: validation/eval_corpus.py (new), validation/eval_data/ (new), validation/accuracy_harness.py (new), tests/test_eval_harness.py (new)
  - acceptance: 50 queries with ground truth. Precision@5 >= 80%, Recall@10 >= 80%. Rerank vs no-rerank A/B documented with numbers.

- [ ] `P4-05` **confidence-calibration** (light) — Tune retrieval thresholds based on eval results. Adjust confidence threshold and reranking cutoff. Re-run harness to verify no regression.
  - depends: P4-04
  - touches: deps.py, orchestration/fallbacks.py, tests/test_confidence.py (new)
  - acceptance: Updated thresholds improve or maintain accuracy. Re-run shows no regression. Threshold values documented.

- [ ] `P4-GATE` **pillar-4-gate** — Run all Pillar 4 gate criteria from PILLARS.md
  - depends: P4-01 through P4-05
  - acceptance: All Pillar 4 gate criteria pass. Entity retrieval works. Hybrid search wired. Parallel retrieval traced. P@5 >= 80%, R@10 >= 80%. Reranking A/B documented. ruff + mypy --strict + pytest all pass.

## Pillar 5: Pydantic AI Orchestrator + Docker Deployment (6 specs)

- [ ] `P5-01` **pydantic-ai-recall-agent** (heavy) — Migrate RecallOrchestrator to Pydantic AI Agent. Tool registration, RunContext, type-safe dependencies. Preserve all existing behavior and test compatibility.
  - depends: P4-GATE
  - touches: agents/recall.py, orchestration/planner.py, deps.py, pyproject.toml, tests/test_pydantic_ai_agent.py (new)
  - acceptance: RecallOrchestrator is Pydantic AI Agent with @agent.tool decorators. All 293+ existing tests pass. Equivalent results.

- [ ] `P5-02` **multi-agent-routing** (standard) — Orchestrator routes by intent: entity queries -> entity agent, recall -> recall agent, synthesis -> synthesis agent. Routing logged in trace.
  - depends: P5-01
  - touches: orchestration/planner.py, agents/ (new agent files), tests/test_agent_routing.py (new)
  - acceptance: "What do I know about X?" -> entity agent. "Summarize notes on Y" -> recall agent. Decision logged in trace.

- [ ] `P5-03` **agent-collaboration** (standard) — Multi-step queries: research agent feeds context to synthesis agent. Agent handoff pattern.
  - depends: P5-01, P5-02
  - touches: orchestration/planner.py, agents/, tests/test_agent_collaboration.py (new)
  - acceptance: Complex query triggers 2 agents in sequence. Final response grounded in both agents' context. Trace shows handoff.

- [ ] `P5-04` **mcp-server-upgrade** (standard) — Rewire MCP server to Pydantic AI backend. Add tools: entity_query, trace_inspect, provider_health. Update existing tools.
  - depends: P5-01, P5-02
  - touches: mcp_server.py, tests/test_mcp_server.py
  - acceptance: All 6 MCP tools respond correctly. Existing tool contracts preserved. New tools return structured data.

- [ ] `P5-05` **docker-compose** (standard) — Docker Compose: Postgres + backend. Health checks, auto-migration, .env.example. Works on local + VPS.
  - depends: P5-04
  - touches: docker-compose.yml (new), Dockerfile (new), .env.example (new)
  - acceptance: `docker compose up` starts system. Migration auto-runs. MCP server accessible. Documented for VPS deployment.

- [ ] `P5-06` **e2e-integration-test** (heavy) — Full pipeline test: ingest 10 docs -> extract entities -> query -> chat -> verify grounded response. The ultimate validation.
  - depends: P5-01 through P5-05
  - touches: tests/test_e2e_integration.py (new)
  - acceptance: Full pipeline: ingest -> entities -> recall -> chat -> grounded response. Entity query returns correct people/orgs. All previous tests maintained.

- [ ] `P5-GATE` **pillar-5-gate** — Run all Pillar 5 gate criteria from PILLARS.md
  - depends: P5-01 through P5-06
  - acceptance: All Pillar 5 gate criteria pass. Pydantic AI agents functional. Multi-agent routing works. Docker Compose runs. E2E passes. 293+ tests maintained. ruff + mypy --strict + pytest all pass.

## Spec Summary

| Pillar | Specs | Gate | Light | Standard | Heavy |
|--------|-------|------|-------|----------|-------|
| 1: Data Infrastructure (PLUS ULTRA) | 64 | P1-GATE | 10 | 51 | 3 |
| 2: Entity Extraction | 4 | P2-GATE | 0 | 3 | 1 |
| 3: Multi-Format Ingestion | 4 | P3-GATE | 1 | 2 | 1 |
| 4: Retrieval + Accuracy | 5 | P4-GATE | 1 | 3 | 1 |
| 5: Pydantic AI + Docker | 6 | P5-GATE | 0 | 4 | 2 |
| **Total** | **83** | **5** | **12** | **63** | **8** |

## Dependency Graph (Pillar Level)

```
Pillar 1 (Data Infrastructure) ──── P1-GATE
                                       │
                    ┌──────────────────┤
                    │                  │
              Pillar 2 (Entity)  Pillar 3 (Ingestion)
              P2-GATE ─────────── P3-GATE
                    │                  │
                    └────────┬─────────┘
                             │
                    Pillar 4 (Retrieval)
                         P4-GATE
                             │
                    Pillar 5 (Pydantic AI + Docker)
                         P5-GATE
```

## Parallelism Notes

### Within Pillar 1 (major parallel tracks):
- **Track A** (Type Safety): P1-01 -> P1-02 -> P1-03, P1-04 (parallel after P1-02)
- **Track B** (Schema): P1-05 -> P1-06 -> P1-07 -> P1-08, P1-09 (parallel after P1-07)
- **Track C** (DB Core): P1-10 -> P1-11 -> P1-12 (sequential) | P1-13 -> P1-14 -> P1-15 -> P1-16 (sequential)
- **Track D** (Search): P1-17 -> P1-18 | P1-19, P1-20, P1-21 (parallel after P1-13) | P1-22 -> P1-23 -> P1-24
- **Track E** (Indexing): P1-25 -> P1-26, P1-27 (parallel) -> P1-28 -> P1-29
- **Track F** (Graph): P1-30 -> P1-31, P1-32, P1-33 (parallel after P1-30)
- **Track G** (Embedding): P1-34 -> P1-35 -> P1-36 -> P1-37
- **Track H** (Quality): P1-38 -> P1-39, P1-40, P1-41 (parallel after P1-38)
- **Track I** (Resilience): P1-42 -> P1-43 (sequential) | P1-44, P1-45 (parallel)
- **Track J** (Operations): P1-46 -> P1-47 | P1-48, P1-49, P1-50 (parallel)
- **Track K** (Audit): P1-51 -> P1-52 | P1-53, P1-54, P1-55 (parallel)
- **Track L** (Future): P1-56, P1-57, P1-58 (independent after dependencies met)
- **Integration**: P1-59 -> P1-60 (fortress depends on all) | P1-61, P1-62, P1-63, P1-64 (parallel)

### Cross-Pillar:
- Pillars 2 and 3 can begin in parallel after P1-GATE
- Pillar 4 requires both P2-GATE and P3-GATE
- Pillar 5 requires P4-GATE
