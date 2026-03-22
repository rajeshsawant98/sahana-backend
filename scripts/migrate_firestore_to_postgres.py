"""
Migrate all Firestore data to Neon PostgreSQL.

Run from project root:
    python scripts/migrate_firestore_to_postgres.py

Safe to re-run — uses ON CONFLICT DO NOTHING throughout.
Order: users → events → rsvps → organizers → moderators → friend_requests
"""

import asyncio
import datetime
import logging
import os
import sys

import firebase_admin
from firebase_admin import credentials, firestore

# Load .env so DATABASE_URL is available
from dotenv import load_dotenv
load_dotenv()

import asyncpg

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BATCH = 500  # rows per insert batch

# ─── Firestore init ────────────────────────────────────────────────────────────

cred = credentials.Certificate("firebase_cred.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


# ─── Postgres connection ───────────────────────────────────────────────────────

def get_pg_dsn() -> str:
    url = os.environ["DATABASE_URL"]
    # asyncpg uses the plain postgresql:// scheme (not +asyncpg)
    return url.split("?")[0]  # strip query params; SSL handled via ssl="require"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def parse_dt(value) -> datetime.datetime | None:
    """Parse Firestore datetime values tolerantly."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value
    if isinstance(value, str):
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f",  # no tz — treat as UTC
            "%Y-%m-%dT%H:%M:%S",     # no tz — treat as UTC
            "%Y-%m-%dT%H:%M",        # e.g. "2025-07-02T12:32"
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S.%f",  # no tz — treat as UTC
        ):
            try:
                dt = datetime.datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                return dt
            except ValueError:
                continue
        log.warning("Could not parse datetime: %r", value)
    return None


def parse_date(value) -> datetime.date | None:
    if value is None:
        return None
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            pass
    return None


# ─── Step 1: Users ────────────────────────────────────────────────────────────

async def migrate_users(conn: asyncpg.Connection) -> set[str]:
    log.info("Fetching users from Firestore...")
    docs = list(db.collection("users").stream())
    log.info("  %d users found", len(docs))

    rows = []
    emails = set()
    for doc in docs:
        d = doc.to_dict()
        email = d.get("email") or doc.id.replace("_at_", "@").replace("_", ".")
        emails.add(email)
        loc = d.get("location") or {}
        rows.append((
            email,
            d.get("name") or "",
            d.get("password"),
            d.get("google_uid"),
            d.get("role", "user"),
            d.get("bio"),
            d.get("profession"),
            d.get("phoneNumber"),
            parse_date(d.get("birthdate")),
            d.get("profile_picture"),
            d.get("interests") or [],
            loc.get("latitude"),
            loc.get("longitude"),
            loc.get("city"),
            loc.get("state"),
            loc.get("country"),
            loc.get("formattedAddress"),
            loc.get("name"),
            parse_dt(d.get("created_at")),
            parse_dt(d.get("updated_at")),
        ))

    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        result = await conn.executemany("""
            INSERT INTO users (
                email, name, password_hash, google_uid, role,
                bio, profession, phone_number, birthdate, profile_picture,
                interests,
                latitude, longitude, city, state, country, formatted_address, location_name,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11,
                $12, $13, $14, $15, $16, $17, $18,
                COALESCE($19, NOW()), COALESCE($20, NOW())
            )
            ON CONFLICT (email) DO NOTHING
        """, batch)
        inserted += len(batch)
        log.info("  users: %d / %d", min(i + BATCH, len(rows)), len(rows))

    log.info("Users done. %d processed.", inserted)
    return emails


# ─── Step 2: Placeholder users for scraper emails ─────────────────────────────

async def ensure_placeholder_users(conn: asyncpg.Connection, emails: set[str], known_emails: set[str]):
    """Insert minimal placeholder rows for emails referenced in events/rsvps but not in users."""
    missing = emails - known_emails
    if not missing:
        return
    log.info("  Inserting %d placeholder users for scraper/system emails", len(missing))
    rows = [(e, e.split("@")[0], "system") for e in missing]
    await conn.executemany("""
        INSERT INTO users (email, name, role)
        VALUES ($1, $2, $3)
        ON CONFLICT (email) DO NOTHING
    """, rows)


# ─── Step 3: Events + RSVPs + Organizers + Moderators ─────────────────────────

async def migrate_events(conn: asyncpg.Connection, known_emails: set[str]):
    log.info("Fetching events from Firestore...")
    docs = list(db.collection("events").stream())
    log.info("  %d events found", len(docs))

    event_rows = []
    rsvp_rows = []
    organizer_rows = []
    moderator_rows = []

    # Collect all referenced emails for placeholder insertion
    ref_emails: set[str] = set()

    for doc in docs:
        d = doc.to_dict()
        event_id = d.get("eventId") or doc.id
        loc = d.get("location") or {}
        ticket = d.get("ticket") or {}

        created_by_email = d.get("createdByEmail")
        if created_by_email:
            ref_emails.add(created_by_email)

        # RSVPs
        for rsvp in d.get("rsvpList") or []:
            rsvp_email = rsvp.get("email")
            if rsvp_email:
                ref_emails.add(rsvp_email)
                rsvp_rows.append((event_id, rsvp_email, rsvp.get("status", "joined"),
                                  rsvp.get("rating"), rsvp.get("review")))

        # Organizers / Moderators
        for email in d.get("organizers") or []:
            ref_emails.add(email)
            organizer_rows.append((event_id, email))
        for email in d.get("moderators") or []:
            ref_emails.add(email)
            moderator_rows.append((event_id, email))

        event_rows.append((
            event_id,
            d.get("eventName") or "",
            d.get("description"),
            loc.get("latitude"),
            loc.get("longitude"),
            loc.get("city"),
            loc.get("state"),
            loc.get("country"),
            loc.get("formattedAddress"),
            loc.get("name"),
            parse_dt(d.get("startTime")),
            d.get("duration"),
            d.get("categories") or [],
            d.get("tags") or [],
            d.get("category"),
            d.get("format"),
            d.get("subCategory"),
            d.get("price"),
            ticket.get("name"),
            ticket.get("remaining"),
            ticket.get("currency"),
            ticket.get("price"),
            bool(d.get("isOnline", False)),
            d.get("joinLink"),
            d.get("imageUrl"),
            d.get("origin", "community"),
            d.get("source", "user"),
            d.get("originalId"),
            d.get("createdBy"),
            created_by_email,
            bool(d.get("isArchived", False)),
            parse_dt(d.get("archivedAt")),
            d.get("archivedBy"),
            d.get("archiveReason"),
            parse_dt(d.get("unarchivedAt")),
            parse_dt(d.get("createdAt")),
        ))

    # Insert placeholder users for any referenced emails not in users
    await ensure_placeholder_users(conn, ref_emails, known_emails)

    # Insert events
    log.info("  Inserting events...")
    for i in range(0, len(event_rows), BATCH):
        batch = event_rows[i:i + BATCH]
        await conn.executemany("""
            INSERT INTO events (
                event_id, event_name, description,
                latitude, longitude, city, state, country, formatted_address, location_name,
                start_time, duration,
                categories, tags, category, format, sub_category,
                price, ticket_name, ticket_remaining, ticket_currency, ticket_price,
                is_online, join_link, image_url,
                origin, source, original_id,
                created_by, created_by_email,
                is_archived, archived_at, archived_by, archive_reason, unarchived_at,
                created_at
            ) VALUES (
                $1, $2, $3,
                $4, $5, $6, $7, $8, $9, $10,
                $11, $12,
                $13, $14, $15, $16, $17,
                $18, $19, $20, $21, $22,
                $23, $24, $25,
                COALESCE($26, 'community'), COALESCE($27, 'user'), $28,
                $29, $30,
                $31, $32, $33, $34, $35,
                COALESCE($36, NOW())
            )
            ON CONFLICT (event_id) DO NOTHING
        """, batch)
        log.info("  events: %d / %d", min(i + BATCH, len(event_rows)), len(event_rows))

    # Insert RSVPs
    log.info("  Inserting RSVPs (%d rows)...", len(rsvp_rows))
    for i in range(0, len(rsvp_rows), BATCH):
        batch = rsvp_rows[i:i + BATCH]
        await conn.executemany("""
            INSERT INTO rsvps (event_id, user_email, status, rating, review)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (event_id, user_email) DO NOTHING
        """, batch)
        log.info("  rsvps: %d / %d", min(i + BATCH, len(rsvp_rows)), len(rsvp_rows))

    # Insert organizers
    log.info("  Inserting event_organizers (%d rows)...", len(organizer_rows))
    for i in range(0, len(organizer_rows), BATCH):
        batch = organizer_rows[i:i + BATCH]
        await conn.executemany("""
            INSERT INTO event_organizers (event_id, user_email)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """, batch)

    # Insert moderators
    log.info("  Inserting event_moderators (%d rows)...", len(moderator_rows))
    for i in range(0, len(moderator_rows), BATCH):
        batch = moderator_rows[i:i + BATCH]
        await conn.executemany("""
            INSERT INTO event_moderators (event_id, user_email)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """, batch)

    log.info("Events done.")


# ─── Step 4: Friend Requests ───────────────────────────────────────────────────

async def migrate_friend_requests(conn: asyncpg.Connection):
    log.info("Fetching friend_requests from Firestore...")
    docs = list(db.collection("friend_requests").stream())
    log.info("  %d friend_requests found", len(docs))

    rows = []
    for doc in docs:
        d = doc.to_dict()
        rows.append((
            d.get("id") or doc.id,
            d.get("sender_id"),
            d.get("receiver_id"),
            d.get("status", "pending"),
            parse_dt(d.get("created_at")),
            parse_dt(d.get("updated_at")),
        ))

    await conn.executemany("""
        INSERT INTO friend_requests (id, sender_id, receiver_id, status, created_at, updated_at)
        VALUES ($1, $2, $3, $4, COALESCE($5, NOW()), COALESCE($6, NOW()))
        ON CONFLICT (id) DO NOTHING
    """, rows)
    log.info("Friend requests done.")


# ─── Final counts ─────────────────────────────────────────────────────────────

async def print_counts(conn: asyncpg.Connection):
    for table in ("users", "events", "rsvps", "event_organizers", "event_moderators", "friend_requests"):
        count = await conn.fetchval(f"SELECT count(*) FROM {table}")
        log.info("  %-22s %d rows", table, count)


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    dsn = get_pg_dsn()
    log.info("Connecting to Postgres...")
    conn = await asyncpg.connect(dsn, ssl="require")
    log.info("Connected.")

    try:
        known_emails = await migrate_users(conn)
        await migrate_events(conn, known_emails)
        await migrate_friend_requests(conn)
        log.info("\n=== Final row counts ===")
        await print_counts(conn)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
