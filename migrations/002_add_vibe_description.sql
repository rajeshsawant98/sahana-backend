-- Migration: 002_add_vibe_description
-- Adds vibe_description column to users for AI-powered semantic matching.
-- users.embedding (vector(1536)) already exists from 001_initial_schema.

ALTER TABLE users ADD COLUMN IF NOT EXISTS vibe_description TEXT;

-- IVFFlat index for cosine ANN search on user embeddings.
-- Run AFTER backfilling embeddings (ivfflat requires data to build lists).
-- CREATE INDEX IF NOT EXISTS idx_users_embedding
-- ON users USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);
