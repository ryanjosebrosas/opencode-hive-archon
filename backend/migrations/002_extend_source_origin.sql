-- Second Brain Knowledge Schema - Extend Source Origin Values
-- Migration: 002_extend_source_origin.sql
-- Author: Second Brain Team
-- Date: 2024-01-01

-- Update constraints across all three tables to include new source origin values
-- knowledge_sources: column is "origin"
ALTER TABLE knowledge_sources DROP CONSTRAINT IF EXISTS knowledge_sources_origin_check;
ALTER TABLE knowledge_sources ADD CONSTRAINT knowledge_sources_origin_check
  CHECK (origin IN ('notion','obsidian','email','manual','youtube','web','other','zoom','json','text','leadworks'));

-- knowledge_documents: column is "source_origin"
ALTER TABLE knowledge_documents DROP CONSTRAINT IF EXISTS knowledge_documents_source_origin_check;
ALTER TABLE knowledge_documents ADD CONSTRAINT knowledge_documents_source_origin_check
  CHECK (source_origin IN ('notion','obsidian','email','manual','youtube','web','other','zoom','json','text','leadworks'));

-- knowledge_chunks: column is "source_origin"
ALTER TABLE knowledge_chunks DROP CONSTRAINT IF EXISTS knowledge_chunks_source_origin_check;
ALTER TABLE knowledge_chunks ADD CONSTRAINT knowledge_chunks_source_origin_check
  CHECK (source_origin IN ('notion','obsidian','email','manual','youtube','web','other','zoom','json','text','leadworks'));