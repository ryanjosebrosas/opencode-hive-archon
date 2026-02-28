# Database Schema Documentation

*Generated on 2026-02-28 08:22:56 from migration files*

---

## Table: `knowledge_sources`

*Row Level Security enabled*

### Columns:

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid primary` | key default gen_random_uuid() |
| `name` | `text not` | null |
| `origin` | `text not` | null check (origin in ( notion,obsidian,email,manual,youtube,web,other )) |
| `config` | `jsonb not` | null default {} |
| `created_at` | `timestamptz not` | null default now() |

---

## Table: `knowledge_documents`

*Row Level Security enabled*

### Columns:

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid primary` | key default gen_random_uuid() |
| `title` | `text not` | null |
| `knowledge_type` | `text not` | null default document check (knowledge_type in ( note,document,decision,conversation, task,signal,playbook,case_study,transcript )) |
| `source_id` | `uuid references` | knowledge_sources(id) on delete set null |
| `source_url` | `text` |  |
| `source_origin` | `text not` | null default manual check (source_origin in ( notion,obsidian,email,manual,youtube,web,other )) |
| `author` | `text` |  |
| `raw_content` | `text` |  |
| `metadata` | `jsonb not` | null default {} |
| `ingested_at` | `timestamptz not` | null default now() |
| `created_at` | `timestamptz not` | null default now() |
| `updated_at` | `timestamptz not` | null default now() |

### Indexes:

- `knowledge_documents_knowledge_type_idx`: create index if not exists knowledge_documents_knowledge_type_idx on knowledge_documents (knowledge_...
- `knowledge_documents_source_origin_idx`: create index if not exists knowledge_documents_source_origin_idx on knowledge_documents (source_orig...

---

## Table: `knowledge_chunks`

*Row Level Security enabled*

### Columns:

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid primary` | key default gen_random_uuid() |
| `document_id` | `uuid references` | knowledge_documents(id) on delete cascade |
| `content` | `text not` | null |
| `embedding` | `extensions.vector(1024) not` | null |
| `knowledge_type` | `text not` | null default document check (knowledge_type in ( note,document,decision,conversation, task,signal,playbook,case_study,transcript )) |
| `chunk_index` | `integer not` | null default 0 check (chunk_index >= 0) |
| `source_origin` | `text not` | null default manual check (source_origin in ( notion,obsidian,email,manual,youtube,web,other )) |
| `metadata` | `jsonb not` | null default {} |
| `created_at` | `timestamptz not` | null default now() |
| `updated_at` | `timestamptz not` | null default now() |

### Indexes:

- `knowledge_chunks_embedding_idx`: create index if not exists knowledge_chunks_embedding_idx on knowledge_chunks using hnsw (embedding ...
- `knowledge_chunks_document_id_idx`: create index if not exists knowledge_chunks_document_id_idx on knowledge_chunks (document_id);
- `knowledge_chunks_knowledge_type_idx`: create index if not exists knowledge_chunks_knowledge_type_idx on knowledge_chunks (knowledge_type);

---

## Table: `knowledge_entities`

*Row Level Security enabled*

### Columns:

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid primary` | key default gen_random_uuid() |
| `name` | `text not` | null |
| `entity_type` | `text not` | null |
| `description` | `text` |  |
| `source_chunk_ids` | `uuid[] not` | null default {} |
| `metadata` | `jsonb not` | null default {} |
| `created_at` | `timestamptz not` | null default now() |
| `updated_at` | `timestamptz not` | null default now() |

### Indexes:

- `knowledge_entities_name_idx`: create index if not exists knowledge_entities_name_idx on knowledge_entities (name);
- `knowledge_entities_entity_type_idx`: create index if not exists knowledge_entities_entity_type_idx on knowledge_entities (entity_type);

---

## Table: `knowledge_relationships`

*Row Level Security enabled*

### Columns:

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid primary` | key default gen_random_uuid() |
| `source_node_id` | `uuid not` | null |
| `target_node_id` | `uuid not` | null |
| `relationship_type` | `text not` | null check (relationship_type in ( topic_link,provenance,temporal, entity_mention,supports,contradicts )) |
| `weight` | `float not` | null default 1.0 check (weight >= 0.0 and weight <= 1.0) |
| `valid_from` | `timestamptz` |  |
| `valid_to` | `timestamptz` |  |
| `metadata` | `jsonb not` | null default {} |
| `created_at` | `timestamptz not` | null default now() |

### Indexes:

- `knowledge_relationships_source_idx`: create index if not exists knowledge_relationships_source_idx on knowledge_relationships (source_nod...
- `knowledge_relationships_target_idx`: create index if not exists knowledge_relationships_target_idx on knowledge_relationships (target_nod...
- `knowledge_relationships_type_idx`: create index if not exists knowledge_relationships_type_idx on knowledge_relationships (relationship...

---

## Table: `schema_versions`

*Row Level Security enabled*

### Columns:

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `serial PRIMARY` | KEY |
| `version_number` | `integer NOT` | NULL UNIQUE |
| `filename` | `text NOT` | NULL UNIQUE |
| `applied_at` | `timestamptz NOT` | NULL DEFAULT now() |
| `applied_by` | `text NOT` | NULL DEFAULT system |
| `execution_time_ms` | `integer` |  |

### Indexes:

- `schema_versions_version_idx`: CREATE INDEX IF NOT EXISTS schema_versions_version_idx ON schema_versions (version_number);

---

## Functions

### `match_knowledge_chunks`

**Signature**: ```sql
create or replace function match_knowledge_chunks( query_embedding   extensions.vector(1024), match_count       int             default 5, match_threshold   float           default 0.6, filter_type       text            default null )
```

**Returns**: `table ( id             uuid, content        text, similarity     float, knowledge_type text, document_id    uuid, chunk_index    integer, source_origin  text, metadata       jsonb )`

**Definition**: ```sql
create or replace function match_knowledge_chunks( query_embedding   extensions.vector(1024), match_count       int             default 5, match_threshold   float           default 0.6, filter_type       text            default null ) returns table ( id             uuid, content        text, similarity     float, knowledge_type text, document_id    uuid, chunk_index    integer, source_origin  text, metadata       jsonb ) language sql stable security definer set search_path = public, extensions as $$ select kc.id, kc.content, 1 - (kc.embedding <=> query_embedding) as similarity, kc.knowledge_type, kc.document_id, kc.chunk_index, kc.source_origin, kc.metadata from knowledge_chunks kc where 1 - (kc.embedding <=> query_embedding) >= match_threshold and (filter_type is null or kc.knowledge_type = filter_type) order by kc.embedding <=> query_embedding limit match_count;
```

