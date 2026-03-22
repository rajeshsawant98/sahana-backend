-- Migration: 004_trigram_user_search
-- Enables trigram indexes so ILIKE '%term%' on users.name and users.email
-- uses an index instead of a full table scan.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_users_name_trgm
ON users USING GIN (name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_users_email_trgm
ON users USING GIN (email gin_trgm_ops);
