-- Migration 005: Content-addressable deduplication
-- Adds content_hash (SHA-256) and status columns to knowledge_chunks.

-- Add content_hash column (nullable initially, will be backfilled)
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS
  content_hash text;

-- Add status column with CHECK constraint
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS
  status text NOT NULL DEFAULT 'active'
  CHECK (status IN ('active', 'superseded', 'archived', 'deleted'));

-- Add UNIQUE constraint on content_hash (once populated)
-- Note: partial index excludes NULLs automatically in PostgreSQL
CREATE UNIQUE INDEX IF NOT EXISTS knowledge_chunks_content_hash_unique_idx
  ON knowledge_chunks (content_hash)
  WHERE content_hash IS NOT NULL;

-- Index for status filtering (search excludes non-active by default)
CREATE INDEX IF NOT EXISTS knowledge_chunks_status_idx
  ON knowledge_chunks (status);