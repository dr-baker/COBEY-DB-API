-- Migration: 004_create_sessions_table
-- Description: Create sessions table with user foreign key
-- Rollback: DROP TABLE IF EXISTS sessions CASCADE;

BEGIN;

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    ts_start TIMESTAMP WITH TIME ZONE NOT NULL,
    user_id TEXT NOT NULL,
    exercises_data JSONB NOT NULL DEFAULT '{}',
    device_type TEXT NOT NULL,
    device_os TEXT NOT NULL,
    region TEXT NOT NULL,
    ip TEXT NOT NULL,
    app_version TEXT NOT NULL
);

-- Add foreign key constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'sessions_user_id_fkey'
    ) THEN
        ALTER TABLE sessions
        ADD CONSTRAINT sessions_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(user_id);
    END IF;
END$$;

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions(user_id);
CREATE INDEX IF NOT EXISTS sessions_ts_start_idx ON sessions(ts_start);
CREATE INDEX IF NOT EXISTS sessions_region_idx ON sessions(region);

COMMIT; 