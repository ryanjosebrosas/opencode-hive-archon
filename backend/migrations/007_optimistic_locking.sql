-- Migration 007: Optimistic locking via version column
-- Adds version column to knowledge_chunks for concurrent update safety.

ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS
  version integer NOT NULL DEFAULT 1 CHECK (version >= 1);

-- Index for version-based update queries
CREATE INDEX IF NOT EXISTS knowledge_chunks_version_idx
  ON knowledge_chunks (id, version);