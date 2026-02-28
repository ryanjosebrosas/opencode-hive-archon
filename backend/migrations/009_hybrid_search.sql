-- Migration 009: Hybrid search via Reciprocal Rank Fusion (RRF)
-- Combines vector similarity (embedding <=> query) + full-text (tsvector @@ tsquery)
-- into a single RPC call. Uses RRF formula: score = Σ weight/(k + rank).

CREATE OR REPLACE FUNCTION hybrid_search_knowledge_chunks(
  query_embedding   extensions.vector(1024),
  query_text        text,
  match_count       int     DEFAULT 10,
  match_threshold   float   DEFAULT 0.0,
  vector_weight     float   DEFAULT 1.0,
  text_weight       float   DEFAULT 1.0,
  filter_type       text    DEFAULT NULL,
  search_mode       text    DEFAULT 'websearch',
  pool_size         int     DEFAULT 50
)
RETURNS TABLE (
  id             uuid,
  content        text,
  knowledge_type text,
  document_id    uuid,
  chunk_index    integer,
  source_origin  text,
  metadata       jsonb,
  rrf_score      float,
  vector_rank    bigint,
  text_rank      bigint
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
  WITH vector_results AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY dist) AS vrank
    FROM (
      SELECT kc.id, kc.embedding <=> query_embedding AS dist
      FROM knowledge_chunks kc
      WHERE 1 - (kc.embedding <=> query_embedding) >= match_threshold
        AND kc.status = 'active'
        AND (filter_type IS NULL OR kc.knowledge_type = filter_type)
      ORDER BY dist
      LIMIT pool_size
    ) v_sub
  ),
  text_results AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY trank_raw DESC) AS trank
    FROM (
      SELECT kc.id, ts_rank_cd(kc.content_tsv, tsquery_val) AS trank_raw
      FROM knowledge_chunks kc
      WHERE kc.content_tsv @@ tsquery_val
        AND kc.status = 'active'
        AND (filter_type IS NULL OR kc.knowledge_type = filter_type)
      ORDER BY trank_raw DESC
      LIMIT pool_size
    ) t_sub
  ),
  combined AS (
    SELECT
      COALESCE(v.id, t.id) AS chunk_id,
      v.vrank,
      t.trank
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.id = t.id
  ),
  scored AS (
    SELECT
      chunk_id,
      (
        COALESCE(vector_weight / (60.0 + vrank), 0.0)
      + COALESCE(text_weight   / (60.0 + trank), 0.0)
      ) AS rrf_score,
      vrank AS vector_rank,
      trank AS text_rank
    FROM combined
  )
  SELECT
    kc.id,
    kc.content,
    kc.knowledge_type,
    kc.document_id,
    kc.chunk_index,
    kc.source_origin,
    kc.metadata,
    s.rrf_score::float,
    s.vector_rank,
    s.text_rank
  FROM scored s
  JOIN knowledge_chunks kc ON kc.id = s.chunk_id
  ORDER BY s.rrf_score DESC, kc.id
  LIMIT match_count;
END;
$$;

REVOKE ALL ON FUNCTION hybrid_search_knowledge_chunks(
  extensions.vector(1024), text, int, float, float, float, text, text, int
) FROM public;
GRANT EXECUTE ON FUNCTION hybrid_search_knowledge_chunks(
  extensions.vector(1024), text, int, float, float, float, text, text, int
) TO service_role;
