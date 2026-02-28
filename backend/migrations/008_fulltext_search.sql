-- Migration 008: Full-text search infrastructure
-- Adds tsvector column, auto-populate trigger, GIN index, and search RPC.

-- Add tsvector column for full-text search
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS
  content_tsv tsvector;

-- Trigger function to auto-update tsvector on insert/update
CREATE OR REPLACE FUNCTION knowledge_chunks_tsvector_update()
RETURNS trigger AS $$
BEGIN
  NEW.content_tsv := to_tsvector('english', coalesce(NEW.content, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger
DROP TRIGGER IF EXISTS knowledge_chunks_tsv_trigger ON knowledge_chunks;
CREATE TRIGGER knowledge_chunks_tsv_trigger
  BEFORE INSERT OR UPDATE OF content ON knowledge_chunks
  FOR EACH ROW EXECUTE FUNCTION knowledge_chunks_tsvector_update();

-- Populate existing rows (backfill after trigger is in place to cover any concurrent inserts)
UPDATE knowledge_chunks
SET content_tsv = to_tsvector('english', coalesce(content, ''))
WHERE content_tsv IS NULL;

-- GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS knowledge_chunks_content_tsv_idx
  ON knowledge_chunks USING GIN (content_tsv);

-- RPC: search_knowledge_chunks_fulltext
CREATE OR REPLACE FUNCTION search_knowledge_chunks_fulltext(
  query_text        text,
  search_mode       text    DEFAULT 'websearch',
  filter_type       text    DEFAULT NULL,
  match_count       int     DEFAULT 10
)
RETURNS TABLE (
  id             uuid,
  content        text,
  knowledge_type text,
  document_id    uuid,
  chunk_index    integer,
  source_origin  text,
  metadata       jsonb,
  rank           float
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
  tsquery_val tsquery;
BEGIN
  IF search_mode = 'phrase' THEN
    tsquery_val := phraseto_tsquery('english', query_text);
  ELSIF search_mode = 'simple' THEN
    tsquery_val := plainto_tsquery('english', query_text);
  ELSE
    tsquery_val := websearch_to_tsquery('english', query_text);
  END IF;

  RETURN QUERY
  SELECT
    kc.id,
    kc.content,
    kc.knowledge_type,
    kc.document_id,
    kc.chunk_index,
    kc.source_origin,
    kc.metadata,
    ts_rank_cd(kc.content_tsv, tsquery_val)::float AS rank
  FROM knowledge_chunks kc
  WHERE
    kc.content_tsv @@ tsquery_val
    AND (filter_type IS NULL OR kc.knowledge_type = filter_type)
    AND kc.status = 'active'
  ORDER BY rank DESC
  LIMIT match_count;
END;
$$;

REVOKE ALL ON FUNCTION search_knowledge_chunks_fulltext(text, text, text, int) FROM public;
GRANT EXECUTE ON FUNCTION search_knowledge_chunks_fulltext(text, text, text, int)
  TO service_role;