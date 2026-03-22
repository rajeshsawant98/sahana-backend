"""
Backfill embeddings for all users that have bio/interests/profession but no embedding yet.

Usage:
    python scripts/backfill_user_embeddings.py          # dry run (shows what would be processed)
    python scripts/backfill_user_embeddings.py --apply  # actually generates and stores embeddings
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
from app.services.embedding_service import generate_and_store_user_embedding


async def _get_users_without_embeddings():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT email, name, profession, bio, interests, vibe_description
            FROM users
            WHERE embedding IS NULL
            ORDER BY email
        """))
        return [dict(row._mapping) for row in result.fetchall()]


async def main(apply: bool):
    users = await _get_users_without_embeddings()
    print(f"Found {len(users)} users without embeddings.")

    if not apply:
        print("Dry run — pass --apply to generate embeddings.")
        for u in users[:10]:
            print(f"  {u['email']} | bio={bool(u.get('bio'))} interests={bool(u.get('interests'))}")
        if len(users) > 10:
            print(f"  ... and {len(users) - 10} more")
        return

    success = 0
    failed = 0
    for u in users:
        ok = await generate_and_store_user_embedding(u)
        if ok:
            success += 1
            print(f"  [OK] {u['email']}")
        else:
            failed += 1
            print(f"  [SKIP] {u['email']} (no content or OpenAI unavailable)")

    print(f"\nDone. {success} embedded, {failed} skipped.")


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    asyncio.run(main(apply))
