from app.repositories.event_repository import EventRepository

event_repo = EventRepository()

def create_event(data: dict):
    try:
        return event_repo.create_event(data)
    except Exception as e:
        print(f"Error in create_event: {e}")
        return None

def get_event_by_id(event_id: str):
    try:
        return event_repo.get_event_by_id(event_id)
    except Exception as e:
        print(f"Error in get_event_by_id: {e}")
        return None

def get_all_events():
    try:
        return event_repo.get_all_events()
    except Exception as e:
        print(f"Error in get_all_events: {e}")
        return []

def update_event(event_id: str, update_data: dict):
    try:
        return event_repo.update_event(event_id, update_data)
    except Exception as e:
        print(f"Error in update_event: {e}")
        return False

def delete_event(event_id: str):
    try:
        return event_repo.delete_event(event_id)
    except Exception as e:
        print(f"Error in delete_event: {e}")
        return False

def get_my_events(email: str):
    try:
        return event_repo.get_events_by_creator(email)
    except Exception as e:
        print(f"Error in get_my_events: {e}")
        return []

def rsvp_to_event(event_id: str, email: str):
    try:
        return event_repo.rsvp_to_event(event_id, email)
    except Exception as e:
        print(f"Error in rsvp_to_event: {e}")
        return False

def cancel_user_rsvp(event_id: str, email: str):
    try:
        return event_repo.cancel_rsvp(event_id, email)
    except Exception as e:
        raise Exception(f"Error cancelling RSVP: {e}")

def get_user_rsvps(email: str):
    try:
        return event_repo.get_user_rsvps(email)
    except Exception as e:
        print(f"Error in get_user_rsvps: {e}")
        return []

def get_rsvp_list(event_id: str):
    try:
        return event_repo.get_rsvp_list(event_id)
    except Exception as e:
        print(f"Error in get_rsvp_list: {e}")
        return []

def get_nearby_events(city: str, state: str):
    try:
        return event_repo.get_nearby_events(city, state)
    except Exception as e:
        print(f"Error in get_nearby_events: {e}")
        return []

def get_external_events(city: str, state: str) -> list[dict]:
    try:
        return event_repo.get_external_events(city, state)
    except Exception as e:
        print(f"Error in get_external_events: {e}")
        return []