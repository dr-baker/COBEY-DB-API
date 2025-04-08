-- Migration: 002_create_recordings_table
-- Description: Create recordings table with user foreign key
-- Rollback: DROP TABLE IF EXISTS recordings CASCADE;

BEGIN;

CREATE TABLE IF NOT EXISTS recordings (
    recording_id TEXT PRIMARY KEY,
    recording_link TEXT NOT NULL,
    recording_type TEXT NOT NULL,
    user_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_session_id TEXT NOT NULL
);

-- Add foreign key constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'recordings_user_id_fkey'
    ) THEN
        ALTER TABLE recordings
        ADD CONSTRAINT recordings_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(user_id);
    END IF;
END$$;

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS recordings_user_id_idx ON recordings(user_id);
CREATE INDEX IF NOT EXISTS recordings_created_at_idx ON recordings(created_at);
CREATE INDEX IF NOT EXISTS recordings_type_idx ON recordings(recording_type);

COMMIT; 