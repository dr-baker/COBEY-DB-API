-- Migration: 005_create_event_log_table
-- Description: Create event_log table for tracking events
-- Rollback: DROP TABLE IF EXISTS event_log CASCADE;

BEGIN;

CREATE TABLE IF NOT EXISTS event_log (
    event_id SERIAL PRIMARY KEY,
    ts TIMESTAMP WITH TIME ZONE NOT NULL,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    event_source TEXT NOT NULL,
    log_level TEXT NOT NULL,
    app_version TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add foreign key constraints if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'event_log_user_id_fkey'
    ) THEN
        ALTER TABLE event_log
        ADD CONSTRAINT event_log_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(user_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'event_log_session_id_fkey'
    ) THEN
        ALTER TABLE event_log
        ADD CONSTRAINT event_log_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES sessions(session_id);
    END IF;
END$$;

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS event_log_ts_idx ON event_log(ts);
CREATE INDEX IF NOT EXISTS event_log_user_id_idx ON event_log(user_id);
CREATE INDEX IF NOT EXISTS event_log_session_id_idx ON event_log(session_id);
CREATE INDEX IF NOT EXISTS event_log_event_type_idx ON event_log(event_type);
CREATE INDEX IF NOT EXISTS event_log_event_source_idx ON event_log(event_source);
CREATE INDEX IF NOT EXISTS event_log_created_at_idx ON event_log(created_at); -- Index for created_at

COMMIT; 