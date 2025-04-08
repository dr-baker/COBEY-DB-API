-- Migration: 001_create_users_table
-- Description: Create initial users table
-- Rollback: DROP TABLE IF EXISTS users CASCADE;

BEGIN;

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    firebase_data JSONB NOT NULL DEFAULT '{}',
    body_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add an index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS users_created_at_idx ON users(created_at);

COMMIT; 