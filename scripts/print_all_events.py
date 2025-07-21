"""
Script to print all non-archived event IDs and titles using get_all_events (non-paginated).
"""
from app.repositories.events.event_repository_manager import EventRepositoryManager

if __name__ == "__main__":
    repo = EventRepositoryManager()
    all_events = repo.get_all_events()
    print(f"Total non-archived events (get_all_events): {len(all_events)}")
    count_with_start_time = 0
    for e in all_events:
        start_time = e.get('startTime')
        if start_time is not None:
            count_with_start_time += 1
        print(f"eventId: {e.get('eventId')} | title: {e.get('title')} | startTime: {start_time}")
    print(f"Events with non-null startTime: {count_with_start_time}")
