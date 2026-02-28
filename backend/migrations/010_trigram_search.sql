-- Migration 010: Trigram fuzzy search for entity names
-- Enables pg_trgm extension and GIN trigram index for fuzzy entity search.
-- Handles typos: "Jonh Smth" finds "John Smith"

-- Enable pg_trgm extension in extensions schema
CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA extensions;

-- GIN trigram index on knowledge_entities.name for fast fuzzy search
-- Uses gin_trgm_ops operator class for trigram similarity
CREATE INDEX IF NOT EXISTS knowledge_entities_name_trgm_idx
  ON knowledge_entities USING GIN (name extensions.gin_trgm_ops);

-- RPC: search_knowledge_entities_fuzzy
-- Fuzzy search using trigram similarity
-- Parameters:
--   search_term: text to search for (e.g., "Jonh Smth")
--   similarity_threshold: minimum similarity score (default 0.3)
--   match_count: max results to return (default 10)
--   filter_type: optional entity_type filter (default NULL = all types)
-- Returns: id, name, entity_type, description, similarity
CREATE OR REPLACE FUNCTION search_knowledge_entities_fuzzy(
  search_term         text,
  similarity_threshold float   DEFAULT 0.3,
  match_count         int     DEFAULT 10,
  filter_type         text    DEFAULT NULL
)
RETURNS TABLE (
  id              uuid,
  name            text,
  entity_type     text,
  description     text,
  similarity      float
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
  -- Validate search_term is not empty
  IF search_term IS NULL OR length(trim(search_term)) = 0 THEN
    RETURN QUERY
    SELECT NULL::uuid, NULL::text, NULL::text, NULL::text, 0.0::float
    WHERE FALSE;  -- Return empty set
  END IF;

  -- Set threshold for % operator (index-friendly filtering)
  PERFORM set_config('pg_trgm.similarity_threshold', similarity_threshold::text, true);

  RETURN QUERY
  SELECT
    ke.id,
    ke.name,
    ke.entity_type,
    ke.description,
    extensions.similarity(ke.name, search_term)::float AS similarity
  FROM knowledge_entities ke
  WHERE
    ke.name % search_term
    AND (filter_type IS NULL OR ke.entity_type = filter_type)
  ORDER BY extensions.similarity(ke.name, search_term) DESC
  LIMIT match_count;
END;
$$;

-- Security: revoke from public, grant to service_role
REVOKE ALL ON FUNCTION search_knowledge_entities_fuzzy(text, float, int, text) FROM public;
GRANT EXECUTE ON FUNCTION search_knowledge_entities_fuzzy(text, float, int, text)
  TO service_role;
