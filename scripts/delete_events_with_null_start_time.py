"""
Script to find and delete all non-archived events with startTime == None (null) for data sanitization.
"""
from app.repositories.events.event_repository_manager import EventRepositoryManager

if __name__ == "__main__":
    repo = EventRepositoryManager()
    all_events = repo.get_all_events()
    to_delete = [e for e in all_events if e.get('startTime') is None]
    print(f"Found {len(to_delete)} non-archived events with startTime=None.")
    for e in to_delete:
        event_id = e.get('eventId')
        if event_id is not None:
            print(f"Deleting eventId: {event_id} | title: {e.get('title')}")
            repo.delete_event(event_id)
        else:
            print(f"Skipping event with missing eventId | title: {e.get('title')}")
    print("Done deleting events with null startTime.")
