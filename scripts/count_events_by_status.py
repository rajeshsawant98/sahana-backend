"""
Script to count all events, non-archived events, and archived events directly from the database.
"""
import asyncio
from app.repositories.events.event_repository_manager import EventRepositoryManager


async def main():
    repo = EventRepositoryManager()
    all_events = await repo.get_all_events()  # Should return all non-archived events
    print(f"Non-archived events (get_all_events): {len(all_events)}")

    # Try to count archived events if method exists
    archived_events = None
    try:
        archived_events = await repo.get_archived_events()
        print(f"Archived events: {len(archived_events)}")
    except Exception as e:
        print(f"Could not fetch archived events: {e}")

    # Try to count all events (archived + non-archived) if possible
    # If you have a method to fetch ALL events regardless of archive status, use it here
    # Otherwise, sum the above
    total = len(all_events)
    if archived_events is not None:
        total += len(archived_events)
    print(f"Total events (archived + non-archived): {total}")


if __name__ == "__main__":
    asyncio.run(main())
