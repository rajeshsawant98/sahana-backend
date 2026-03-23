"""
Backfill embeddings for all active events that don't have one yet.
Only processes is_archived = FALSE events.

Usage:
    python scripts/backfill_event_embeddings.py          # dry run
    python scripts/backfill_event_embeddings.py --apply  # generates and stores embeddings
"""
import asyncio
import sys
import os

# Allow running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.services.embedding_service import generate_and_store_event_embedding


async def _get_events_without_embeddings():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT event_id, event_name, description, categories, city, state
            FROM events
            WHERE embedding IS NULL
              AND is_archived = FALSE
            ORDER BY event_id
        """))
        return [dict(row._mapping) for row in result.fetchall()]


async def main(apply: bool):
    events = await _get_events_without_embeddings()
    print(f"Found {len(events)} active events without embeddings.")

    if not apply:
        print("Dry run — pass --apply to generate embeddings.")
        for e in events[:10]:
            print(f"  {e['event_id']} | {e.get('event_name', '')[:60]}")
        if len(events) > 10:
            print(f"  ... and {len(events) - 10} more")
        return

    success = 0
    failed = 0
    for e in events:
        ok = await generate_and_store_event_embedding(e)
        if ok:
            success += 1
            print(f"  [OK] {e['event_id']} — {e.get('event_name', '')[:60]}")
        else:
            failed += 1
            print(f"  [SKIP] {e['event_id']} (no content or OpenAI unavailable)")

    print(f"\nDone. {success} embedded, {failed} skipped.")


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    asyncio.run(main(apply))
