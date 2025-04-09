-- Migration: 003_create_algos_table
-- Description: Create algos table for algorithm metadata
-- Rollback: DROP TABLE IF EXISTS algos CASCADE;

BEGIN;

CREATE TABLE IF NOT EXISTS algos (
    algo_id TEXT PRIMARY KEY,
    recording_type TEXT NOT NULL,
    location TEXT NOT NULL,
    version TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add index for recording type queries
CREATE INDEX IF NOT EXISTS algos_recording_type_idx ON algos(recording_type);
CREATE INDEX IF NOT EXISTS algos_version_idx ON algos(version);
CREATE INDEX IF NOT EXISTS algos_created_at_idx ON algos(created_at);

COMMIT; 