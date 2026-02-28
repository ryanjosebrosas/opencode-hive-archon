-- Add data integrity constraints to all tables
-- Enforce at DB level what contracts enforce at Python level

-- 1. Add entity_type CHECK constraint to knowledge_entities table
ALTER TABLE knowledge_entities DROP CONSTRAINT IF EXISTS knowledge_entities_entity_type_check;
ALTER TABLE knowledge_entities ADD CONSTRAINT knowledge_entities_entity_type_check
  CHECK (entity_type IN ('person','organization','concept','tool','event','location','other'));

-- 2. Add FK constraints to knowledge_relationships table
ALTER TABLE knowledge_relationships DROP CONSTRAINT IF EXISTS knowledge_relationships_source_node_id_fkey;
ALTER TABLE knowledge_relationships ADD CONSTRAINT knowledge_relationships_source_node_id_fkey
  FOREIGN KEY (source_node_id) REFERENCES knowledge_entities(id) ON DELETE RESTRICT;

ALTER TABLE knowledge_relationships DROP CONSTRAINT IF EXISTS knowledge_relationships_target_node_id_fkey;
ALTER TABLE knowledge_relationships ADD CONSTRAINT knowledge_relationships_target_node_id_fkey
  FOREIGN KEY (target_node_id) REFERENCES knowledge_entities(id) ON DELETE RESTRICT;

-- 3. Add UNIQUE constraint on knowledge_entities name per entity_type
ALTER TABLE knowledge_entities DROP CONSTRAINT IF EXISTS knowledge_entities_name_entity_type_unique;
ALTER TABLE knowledge_entities ADD CONSTRAINT knowledge_entities_name_entity_type_unique
  UNIQUE (name, entity_type);

-- 4. Add non-empty CHECK constraint to knowledge_documents title
ALTER TABLE knowledge_documents DROP CONSTRAINT IF EXISTS knowledge_documents_title_nonempty;
ALTER TABLE knowledge_documents ADD CONSTRAINT knowledge_documents_title_nonempty
  CHECK (length(trim(title)) > 0);

-- 5. Add non-empty CHECK constraint to knowledge_chunks content
ALTER TABLE knowledge_chunks DROP CONSTRAINT IF EXISTS knowledge_chunks_content_nonempty;
ALTER TABLE knowledge_chunks ADD CONSTRAINT knowledge_chunks_content_nonempty
  CHECK (length(trim(content)) > 0);

-- 6. Add non-empty CHECK constraint to knowledge_entities name
ALTER TABLE knowledge_entities DROP CONSTRAINT IF EXISTS knowledge_entities_name_nonempty;
ALTER TABLE knowledge_entities ADD CONSTRAINT knowledge_entities_name_nonempty
  CHECK (length(trim(name)) > 0);

-- 7. Add non-empty CHECK constraint to knowledge_sources name
ALTER TABLE knowledge_sources DROP CONSTRAINT IF EXISTS knowledge_sources_name_nonempty;
ALTER TABLE knowledge_sources ADD CONSTRAINT knowledge_sources_name_nonempty
  CHECK (length(trim(name)) > 0);