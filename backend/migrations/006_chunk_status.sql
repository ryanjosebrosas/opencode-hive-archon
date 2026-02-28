-- Migration 006: Chunk status lifecycle documentation
-- The status column was added in migration 005.
-- This migration documents the valid transitions and adds a comment.

COMMENT ON COLUMN knowledge_chunks.status IS
  'Lifecycle state: active (searchable), superseded (replaced by newer content), archived (manually excluded), deleted (soft-deleted, restorable)';