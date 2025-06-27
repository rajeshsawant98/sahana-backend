from app.repositories.event_repository import EventRepository
from app.services.user_service import validate_user_emails

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

def get_events_organized_by_user(email: str):
    try:
        return event_repo.get_events_organized_by_user(email)
    except Exception as e:
        print(f"Error in get_events_organized_by_user: {e}")
        return []

def get_events_moderated_by_user(email: str):
    try:
        return event_repo.get_events_moderated_by_user(email)
    except Exception as e:
        print(f"Error in get_events_moderated_by_user: {e}")
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
    
#Role assignment with email validation
def set_organizers(event_id: str, emails: list[str], creator_email: str) -> dict:
    result = validate_user_emails(emails)
    valid_emails = result["valid"]
    invalid_emails = result["invalid"]

    # Ensure creator is always an organizer
    if creator_email not in valid_emails:
        valid_emails.append(creator_email)

    success = event_repo.update_event_roles(event_id, "organizers", valid_emails)
    return {
        "success": success,
        "organizers": valid_emails,
        "skipped": invalid_emails
    }

def set_moderators(event_id: str, emails: list[str]) -> dict:
    result = validate_user_emails(emails)
    valid_emails = result["valid"]
    invalid_emails = result["invalid"]

    success = event_repo.update_event_roles(event_id, "moderators", valid_emails)
    return {
        "success": success,
        "moderators": valid_emails,
        "skipped": invalid_emails
    }
    

def delete_old_events() -> int:
    return event_repo.delete_events_before_today()