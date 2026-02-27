-- Migration 003: Schema version tracking table
CREATE TABLE IF NOT EXISTS schema_versions (
    id              serial PRIMARY KEY,
    version_number  integer NOT NULL UNIQUE,
    filename        text NOT NULL UNIQUE,
    checksum        char(64) NOT NULL,
    applied_at      timestamptz NOT NULL DEFAULT now(),
    applied_by      text NOT NULL DEFAULT 'system',
    execution_time_ms integer
);
ALTER TABLE schema_versions ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS schema_versions_version_idx ON schema_versions (version_number);