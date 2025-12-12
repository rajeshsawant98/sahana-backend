"""
Script to test event pagination and print all non-archived events using EventRepositoryManager.
"""
import asyncio
from app.repositories.events.event_repository_manager import EventRepositoryManager
from app.models.pagination import CursorPaginationParams, EventFilters


async def main():
    repo = EventRepositoryManager()
    all_events = []
    cursor = None
    page_size = 12  # Adjust as needed
    page = 1
    while True:
        params = CursorPaginationParams(cursor=cursor, page_size=page_size, direction="next")
        events, next_cursor, prev_cursor, has_next, has_previous = await repo.get_all_events_paginated(params, EventFilters())
        print(f"Page {page}: {len(events)} events, has_next={has_next}, next_cursor={next_cursor}")
        for e in events:
            print(f"  - eventId: {e.get('eventId')} | startTime: {e.get('startTime')}")
        all_events.extend(events)
        if not has_next or not next_cursor:
            break
        cursor = next_cursor
        page += 1
    print(f"Total non-archived events paginated: {len(all_events)}")
    print("All paginated eventId/startTime pairs:")
    for e in all_events:
        print(f"eventId: {e.get('eventId')} | startTime: {e.get('startTime')}")


if __name__ == "__main__":
    asyncio.run(main())
