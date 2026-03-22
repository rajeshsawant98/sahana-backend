-- Migration: 003_query_optimizations
-- Performance indexes identified during PostgreSQL migration audit.

-- 1. tsvector column + trigger + GIN index for full-text event search.
--    Generated columns don't accept to_tsvector (not considered immutable by PG).
--    Standard solution: regular column populated by a BEFORE INSERT OR UPDATE trigger.

ALTER TABLE events ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE OR REPLACE FUNCTION events_search_vector_update() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector(
        'english',
        COALESCE(NEW.event_name, '') || ' '
        || COALESCE(NEW.description, '') || ' '
        || regexp_replace(COALESCE(NEW.categories::text, ''), '[{}"]', ' ', 'g') || ' '
        || COALESCE(NEW.city, '') || ' '
        || COALESCE(NEW.state, '') || ' '
        || COALESCE(NEW.formatted_address, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS events_search_vector_trigger ON events;
CREATE TRIGGER events_search_vector_trigger
BEFORE INSERT OR UPDATE ON events
FOR EACH ROW EXECUTE FUNCTION events_search_vector_update();

-- Backfill existing rows
UPDATE events SET search_vector = to_tsvector(
    'english',
    COALESCE(event_name, '') || ' '
    || COALESCE(description, '') || ' '
    || regexp_replace(COALESCE(categories::text, ''), '[{}"]', ' ', 'g') || ' '
    || COALESCE(city, '') || ' '
    || COALESCE(state, '') || ' '
    || COALESCE(formatted_address, '')
);

CREATE INDEX IF NOT EXISTS idx_events_search ON events USING GIN (search_vector);

-- 2. Composite index for the most common event list query:
--    WHERE is_archived = FALSE ORDER BY start_time ASC
--    Covers get_all_events_paginated, get_external_events_paginated.
CREATE INDEX IF NOT EXISTS idx_events_active_start_time
ON events (start_time ASC NULLS LAST)
WHERE is_archived = FALSE;

-- 3. Composite index for city+state filtering on active events.
--    Covers get_nearby_events_paginated and filtered event queries.
CREATE INDEX IF NOT EXISTS idx_events_active_city_state
ON events (LOWER(city), LOWER(state))
WHERE is_archived = FALSE;

-- 4. Index for creator email filter (case-insensitive).
CREATE INDEX IF NOT EXISTS idx_events_created_by_email_lower
ON events (LOWER(created_by_email))
WHERE is_archived = FALSE;

-- 5. Index for archived events ordered by archived_at (admin archive view).
CREATE INDEX IF NOT EXISTS idx_events_archived_at
ON events (archived_at DESC NULLS LAST)
WHERE is_archived = TRUE;

-- 6. Covering index for RSVP lookups joining to events on start_time ordering.
CREATE INDEX IF NOT EXISTS idx_rsvps_user_event
ON rsvps (user_email, status)
INCLUDE (event_id);

-- 7. Index for friend request lookups in both directions.
--    Covers get_requests_for_user(direction="all").
CREATE INDEX IF NOT EXISTS idx_friend_requests_either_party
ON friend_requests (sender_id, receiver_id, status);
