-- Migration 001: Knowledge schema foundation
-- Establishes canonical tables for Ultima Second Brain storage layer.
-- Run in Supabase SQL editor or via supabase db push.

-- Enable pgvector extension
create extension if not exists vector with schema extensions;

-- Enable UUID generation used by table defaults
create extension if not exists pgcrypto;

-- -------------------------------------------------------------------------
-- knowledge_sources: integration origin registry
-- -------------------------------------------------------------------------
create table if not exists knowledge_sources (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  origin      text not null check (origin in (
                'notion','obsidian','email','manual','youtube','web','other'
              )),
  config      jsonb not null default '{}',
  created_at  timestamptz not null default now()
);

alter table knowledge_sources enable row level security;

-- -------------------------------------------------------------------------
-- knowledge_documents: parent containers for chunks
-- -------------------------------------------------------------------------
create table if not exists knowledge_documents (
  id             uuid primary key default gen_random_uuid(),
  title          text not null,
  knowledge_type text not null default 'document' check (knowledge_type in (
                   'note','document','decision','conversation',
                   'task','signal','playbook','case_study','transcript'
                 )),
  source_id      uuid references knowledge_sources(id) on delete set null,
  source_url     text,
  source_origin  text not null default 'manual' check (source_origin in (
                   'notion','obsidian','email','manual','youtube','web','other'
                 )),
  author         text,
  raw_content    text,
  metadata       jsonb not null default '{}',
  ingested_at    timestamptz not null default now(),
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

alter table knowledge_documents enable row level security;

create index if not exists knowledge_documents_knowledge_type_idx
  on knowledge_documents (knowledge_type);

create index if not exists knowledge_documents_source_origin_idx
  on knowledge_documents (source_origin);

-- -------------------------------------------------------------------------
-- knowledge_chunks: base retrieval unit (semantic search target)
-- embedding dimension 1024 aligned to voyage-4-large
-- -------------------------------------------------------------------------
create table if not exists knowledge_chunks (
  id             uuid primary key default gen_random_uuid(),
  document_id    uuid references knowledge_documents(id) on delete cascade,
  content        text not null,
  embedding      extensions.vector(1024) not null,
  knowledge_type text not null default 'document' check (knowledge_type in (
                   'note','document','decision','conversation',
                   'task','signal','playbook','case_study','transcript'
                 )),
  chunk_index    integer not null default 0 check (chunk_index >= 0),
  source_origin  text not null default 'manual' check (source_origin in (
                   'notion','obsidian','email','manual','youtube','web','other'
                 )),
  metadata       jsonb not null default '{}',
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

alter table knowledge_chunks enable row level security;

-- HNSW index for cosine similarity (recommended for normalized voyage embeddings)
create index if not exists knowledge_chunks_embedding_idx
  on knowledge_chunks using hnsw (embedding extensions.vector_cosine_ops);

create index if not exists knowledge_chunks_document_id_idx
  on knowledge_chunks (document_id);

create index if not exists knowledge_chunks_knowledge_type_idx
  on knowledge_chunks (knowledge_type);

-- -------------------------------------------------------------------------
-- knowledge_entities: graph nodes (named concepts, people, tools)
-- -------------------------------------------------------------------------
create table if not exists knowledge_entities (
  id               uuid primary key default gen_random_uuid(),
  name             text not null,
  entity_type      text not null,
  description      text,
  source_chunk_ids uuid[] not null default '{}',
  metadata         jsonb not null default '{}',
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

alter table knowledge_entities enable row level security;

create index if not exists knowledge_entities_name_idx
  on knowledge_entities (name);

create index if not exists knowledge_entities_entity_type_idx
  on knowledge_entities (entity_type);

-- -------------------------------------------------------------------------
-- knowledge_relationships: typed edges between nodes (semantic graph)
-- valid_from / valid_to support bi-temporal Graphiti-style tracking
-- -------------------------------------------------------------------------
create table if not exists knowledge_relationships (
  id                uuid primary key default gen_random_uuid(),
  source_node_id    uuid not null,
  target_node_id    uuid not null,
  relationship_type text not null check (relationship_type in (
                      'topic_link','provenance','temporal',
                      'entity_mention','supports','contradicts'
                    )),
  weight            float not null default 1.0 check (weight >= 0.0 and weight <= 1.0),
  valid_from        timestamptz,
  valid_to          timestamptz,
  metadata          jsonb not null default '{}',
  created_at        timestamptz not null default now()
);

alter table knowledge_relationships enable row level security;

create index if not exists knowledge_relationships_source_idx
  on knowledge_relationships (source_node_id);

create index if not exists knowledge_relationships_target_idx
  on knowledge_relationships (target_node_id);

create index if not exists knowledge_relationships_type_idx
  on knowledge_relationships (relationship_type);

-- -------------------------------------------------------------------------
-- match_knowledge_chunks: RPC for semantic similarity search
-- Replaces the old match_vectors stub function.
-- Returns top-k chunks by cosine similarity above threshold.
-- -------------------------------------------------------------------------
create or replace function match_knowledge_chunks(
  query_embedding   extensions.vector(1024),
  match_count       int             default 5,
  match_threshold   float           default 0.6,
  filter_type       text            default null
)
returns table (
  id             uuid,
  content        text,
  similarity     float,
  knowledge_type text,
  document_id    uuid,
  chunk_index    integer,
  source_origin  text,
  metadata       jsonb
)
language sql
stable
security definer
set search_path = public, extensions
as $$
  select
    kc.id,
    kc.content,
    1 - (kc.embedding <=> query_embedding) as similarity,
    kc.knowledge_type,
    kc.document_id,
    kc.chunk_index,
    kc.source_origin,
    kc.metadata
  from knowledge_chunks kc
  where
    1 - (kc.embedding <=> query_embedding) >= match_threshold
    and (filter_type is null or kc.knowledge_type = filter_type)
  order by kc.embedding <=> query_embedding
  limit match_count;
$$;

revoke all on function match_knowledge_chunks(extensions.vector(1024), int, float, text) from public;
grant execute on function match_knowledge_chunks(extensions.vector(1024), int, float, text)
  to service_role;
