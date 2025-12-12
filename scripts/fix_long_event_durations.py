"""
Script to find and fix events with abnormally long durations (> 14 days / 20160 minutes).
Sets duration to 120 minutes if it is negative or > 20160.
"""
import asyncio
from app.repositories.events.event_repository_manager import EventRepositoryManager

MAX_DURATION = 20160  # 14 days in minutes
DEFAULT_DURATION = 120


async def main():
    repo = EventRepositoryManager()
    all_events = await repo.get_all_events()
    to_fix = [e for e in all_events if e.get('duration', 0) > MAX_DURATION or e.get('duration', 0) <= 0]
    print(f"Found {len(to_fix)} events with abnormal duration.")
    for e in to_fix:
        event_id = e.get('eventId')
        old_duration = e.get('duration')
        if event_id is not None:
            print(f"Fixing eventId: {event_id} | title: {e.get('title')} | old duration: {old_duration}")
            await repo.update_event(event_id, {"duration": DEFAULT_DURATION})
        else:
            print(f"Skipping event with missing eventId | title: {e.get('title')}")
    print("Done fixing event durations.")


if __name__ == "__main__":
    asyncio.run(main())
