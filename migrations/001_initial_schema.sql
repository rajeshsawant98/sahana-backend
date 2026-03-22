-- Sahana PostgreSQL Schema
-- Migration: 001_initial_schema
-- Replaces: Firestore collections (users, events, friend_requests)

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector for future AI recommendations

-- ─────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    email               TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    password_hash       TEXT,
    google_uid          TEXT,
    role                TEXT NOT NULL DEFAULT 'user',   -- 'user' | 'admin'

    -- Profile
    bio                 TEXT,
    profession          TEXT,
    phone_number        TEXT,
    birthdate           DATE,
    profile_picture     TEXT,
    interests           TEXT[]  NOT NULL DEFAULT '{}',

    -- Location (flattened from nested object)
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    city                TEXT,
    state               TEXT,
    country             TEXT,
    formatted_address   TEXT,
    location_name       TEXT,

    -- AI (future)
    embedding           vector(1536),

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_city_state ON users (city, state);
CREATE INDEX IF NOT EXISTS idx_users_google_uid ON users (google_uid) WHERE google_uid IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_interests  ON users USING GIN (interests);
-- Full-text search (replaces full-table scan for user search)
CREATE INDEX IF NOT EXISTS idx_users_search ON users
    USING GIN (to_tsvector('english', coalesce(name, '') || ' ' || coalesce(email, '')));


-- ─────────────────────────────────────────
-- EVENTS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    event_id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    event_name          TEXT NOT NULL,
    description         TEXT,

    -- Location (flattened from nested object)
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    city                TEXT,
    state               TEXT,
    country             TEXT,
    formatted_address   TEXT,
    location_name       TEXT,

    -- Timing
    start_time          TIMESTAMPTZ,
    duration            INTEGER,        -- seconds

    -- Classification
    -- 'categories' is the canonical multi-value list used for filtering
    -- 'category' / 'format' / 'sub_category' are Eventbrite/Ticketmaster metadata
    categories          TEXT[]  NOT NULL DEFAULT '{}',
    tags                TEXT[]  NOT NULL DEFAULT '{}',
    category            TEXT,           -- primary category string (e.g. "Food & Drink")
    format              TEXT,           -- event format (e.g. "Festival", "Conference")
    sub_category        TEXT,           -- sub-category (e.g. "Spirits", "Christianity")

    -- Pricing (stored as-is from source, e.g. "83.49 USD")
    price               TEXT,
    -- Ticket details (flattened from nested ticket object)
    ticket_name         TEXT,
    ticket_remaining    INTEGER,
    ticket_currency     TEXT,
    ticket_price        NUMERIC(10, 2),

    -- Flags
    is_online           BOOLEAN NOT NULL DEFAULT FALSE,
    join_link           TEXT,
    image_url           TEXT,

    -- Ingestion metadata
    origin              TEXT NOT NULL DEFAULT 'community',  -- 'community' | 'external' | 'manual'
    source              TEXT NOT NULL DEFAULT 'user',       -- 'user' | 'eventbrite' | 'ticketmaster'
    original_id         TEXT UNIQUE,    -- dedup key for ingested events

    -- Ownership
    created_by          TEXT,           -- display name (e.g. "Eventbrite Organizer")
    created_by_email    TEXT REFERENCES users (email) ON DELETE SET NULL,

    -- Soft delete / archive
    is_archived         BOOLEAN NOT NULL DEFAULT FALSE,
    archived_at         TIMESTAMPTZ,
    archived_by         TEXT,
    archive_reason      TEXT,

    -- AI (future)
    embedding           vector(1536),

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes mirroring Firestore composite indexes + new ones
CREATE INDEX IF NOT EXISTS idx_events_start_time  ON events (start_time)              WHERE is_archived = FALSE;
CREATE INDEX IF NOT EXISTS idx_events_city        ON events (city, state, start_time) WHERE is_archived = FALSE;
CREATE INDEX IF NOT EXISTS idx_events_created_by  ON events (created_by_email, start_time) WHERE is_archived = FALSE;
CREATE INDEX IF NOT EXISTS idx_events_categories  ON events USING GIN (categories);
CREATE INDEX IF NOT EXISTS idx_events_tags        ON events USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_events_is_online   ON events (is_online, start_time)   WHERE is_archived = FALSE;
CREATE INDEX IF NOT EXISTS idx_events_original_id ON events (original_id)             WHERE original_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_archived    ON events (is_archived, archived_at);
CREATE INDEX IF NOT EXISTS idx_events_source      ON events (source, start_time)      WHERE is_archived = FALSE;


-- ─────────────────────────────────────────
-- EVENT ORGANIZERS  (was array field in Firestore)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS event_organizers (
    event_id    TEXT REFERENCES events (event_id) ON DELETE CASCADE,
    user_email  TEXT REFERENCES users  (email)    ON DELETE CASCADE,
    PRIMARY KEY (event_id, user_email)
);

-- ─────────────────────────────────────────
-- EVENT MODERATORS  (was array field in Firestore)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS event_moderators (
    event_id    TEXT REFERENCES events (event_id) ON DELETE CASCADE,
    user_email  TEXT REFERENCES users  (email)    ON DELETE CASCADE,
    PRIMARY KEY (event_id, user_email)
);


-- ─────────────────────────────────────────
-- RSVPs  (was nested array inside event doc — read-modify-write bottleneck)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rsvps (
    id          BIGSERIAL PRIMARY KEY,
    event_id    TEXT REFERENCES events (event_id) ON DELETE CASCADE,
    user_email  TEXT REFERENCES users  (email)    ON DELETE CASCADE,
    status      TEXT NOT NULL,  -- 'interested' | 'joined' | 'attended' | 'no_show'
    rating      SMALLINT CHECK (rating BETWEEN 1 AND 5),
    review      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (event_id, user_email)
);

CREATE INDEX IF NOT EXISTS idx_rsvps_user  ON rsvps (user_email, status);
CREATE INDEX IF NOT EXISTS idx_rsvps_event ON rsvps (event_id,   status);


-- ─────────────────────────────────────────
-- FRIEND REQUESTS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS friend_requests (
    id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    sender_id   TEXT NOT NULL REFERENCES users (email) ON DELETE CASCADE,
    receiver_id TEXT NOT NULL REFERENCES users (email) ON DELETE CASCADE,
    status      TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'accepted' | 'rejected'
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (sender_id, receiver_id)
);

CREATE INDEX IF NOT EXISTS idx_friend_requests_receiver ON friend_requests (receiver_id, status);
CREATE INDEX IF NOT EXISTS idx_friend_requests_sender   ON friend_requests (sender_id,   status);


-- ─────────────────────────────────────────
-- updated_at auto-trigger
-- ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

CREATE OR REPLACE TRIGGER events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

CREATE OR REPLACE TRIGGER rsvps_updated_at
    BEFORE UPDATE ON rsvps
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

CREATE OR REPLACE TRIGGER friend_requests_updated_at
    BEFORE UPDATE ON friend_requests
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
