-- Migration: 003_create_algos_table
-- Description: Create algos table for algorithm metadata
-- Rollback: DROP TABLE IF EXISTS algos CASCADE;

BEGIN;

CREATE TABLE IF NOT EXISTS algos (
    algo_id TEXT PRIMARY KEY,
    recording_type TEXT NOT NULL,
    location TEXT NOT NULL,
    version TEXT NOT NULL
);

-- Add index for recording type queries
CREATE INDEX IF NOT EXISTS algos_recording_type_idx ON algos(recording_type);
CREATE INDEX IF NOT EXISTS algos_version_idx ON algos(version);

COMMIT; 