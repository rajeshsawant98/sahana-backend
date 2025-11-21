import json
import asyncio
import pytest
from app.services.event_ingestion_service import (
    fetch_ticketmaster_events,
    get_unique_user_locations,
    ingest_events_for_all_cities
)
from app.auth.firebase_init import get_firestore_client


def show_sample_ticketmaster_events(city="Tempe", state="AZ"):
    events = fetch_ticketmaster_events(city, state)
    print(f"\n🔍 Total Events Fetched: {len(events)}\n")

    for i, e in enumerate(events, 1):
        print(f"📌 Event #{i}")
        print(f"Name       : {e['eventName']}")
        print(f"Date/Time  : {e['startTime']}")
        print(f"Venue      : {e['location']['name']}")
        print(f"Address    : {e['location']['formattedAddress']}")
        print(f"City/State : {e['location']['city']}, {e['location']['country']}")
        print(f"Latitude   : {e['location']['latitude']}")
        print(f"Longitude  : {e['location']['longitude']}")
        print(f"Categories : {e['categories']}")
        print(f"Online?    : {e['isOnline']}")
        print(f"Join Link  : {e['joinLink']}")
        print(f"Image URL  : {e['imageUrl']}")
        print(f"Description: {e['description'][:100]}...")
        print("-" * 60)


def show_all_user_locations():
    locations = get_unique_user_locations()
    print(f"\n🔍 Total Unique Locations: {len(locations)}\n")

    for i, loc in enumerate(locations, 1):
        print(f"📌 Location #{i}")
        print(f"City : {loc[0]}")
        print(f"State: {loc[1]}")
        print("-" * 40)




def run_ingestion_for_all_cities():
    result = asyncio.run(ingest_events_for_all_cities())
    print(f"\n✅ Ingestion Summary")
    print(f"Total Events Saved    : {result['total_events']}")
    print(f"Total Cities Processed: {result['processed_cities']}")
    print("\nDetails:")
    for detail in result["summary"]:
        print(f"• {detail}")


def backfill_user_events_metadata():
    db = get_firestore_client()
    events_ref = db.collection("events")

    updated_count = 0
    for doc in events_ref.stream():
        data = doc.to_dict()

        if "origin" not in data or "source" not in data:
            updates = {
                "origin": data.get("origin", "community"),
                "source": data.get("source", "user")
            }
            events_ref.document(doc.id).update(updates)
            updated_count += 1

    print(f"✅ Backfilled {updated_count} user events with origin/source")


def migrate_ticketmaster_events():
    db = get_firestore_client()
    old_ref = db.collection("ticketmasterEvents")
    new_ref = db.collection("events")

    migrated = 0
    for doc in old_ref.stream():
        data = doc.to_dict()
        data["origin"] = "external"
        data["source"] = "ticketmaster"
        data["originalId"] = data.get("eventId")
        new_ref.document(data["eventId"]).set(data)
        migrated += 1

    print(f"✅ {migrated} Ticketmaster events migrated to unified 'events' collection.")
    return migrated


def test_archive_fields_in_parsed_events():
    """Test that parsed events include proper archive fields"""
    events = fetch_ticketmaster_events("Tempe", "AZ")
    if events:
        sample_event = events[0]
        print(f"\n🔍 Testing Archive Fields in Event: {sample_event['eventName']}")
        print(f"✅ isArchived: {sample_event.get('isArchived', 'MISSING')}")
        print(f"✅ archivedAt: {sample_event.get('archivedAt', 'MISSING')}")
        print(f"✅ archivedBy: {sample_event.get('archivedBy', 'MISSING')}")
        print(f"✅ archiveReason: {sample_event.get('archiveReason', 'MISSING')}")
        print(f"✅ origin: {sample_event.get('origin', 'MISSING')}")
        print(f"✅ source: {sample_event.get('source', 'MISSING')}")
        
        # Verify all required fields are present
        required_fields = ['isArchived', 'archivedAt', 'archivedBy', 'archiveReason']
        missing_fields = [field for field in required_fields if field not in sample_event]
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
        else:
            print("✅ All archive fields are present!")
            
        return sample_event
    else:
        print("❌ No events fetched for testing")
        return None


@pytest.mark.asyncio
async def test_eventbrite_archive_fields():
    """Test that Eventbrite events also include proper archive fields"""
    from app.services.event_scraping_service import get_eventbrite_events
    
    try:
        events = await get_eventbrite_events("Tempe", "AZ", seen_links=set())
        if events:
            sample_event = events[0]
            print(f"\n🔍 Testing Eventbrite Archive Fields in Event: {sample_event['eventName']}")
            print(f"✅ isArchived: {sample_event.get('isArchived', 'MISSING')}")
            print(f"✅ archivedAt: {sample_event.get('archivedAt', 'MISSING')}")
            print(f"✅ archivedBy: {sample_event.get('archivedBy', 'MISSING')}")
            print(f"✅ archiveReason: {sample_event.get('archiveReason', 'MISSING')}")
            print(f"✅ origin: {sample_event.get('origin', 'MISSING')}")
            print(f"✅ source: {sample_event.get('source', 'MISSING')}")
            
            # Verify all required fields are present
            required_fields = ['isArchived', 'archivedAt', 'archivedBy', 'archiveReason']
            missing_fields = [field for field in required_fields if field not in sample_event]
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
            else:
                print("✅ All Eventbrite archive fields are present!")
        else:
            print("❌ No Eventbrite events fetched for testing")
    except Exception as e:
        print(f"❌ Error testing Eventbrite events: {e}")


def backfill_archive_fields():
    """Backfill archive fields for existing events that don't have them"""
    db = get_firestore_client()
    events_ref = db.collection("events")
    
    updated_count = 0
    total_checked = 0
    
    for doc in events_ref.stream():
        total_checked += 1
        data = doc.to_dict()
        
        # Check if any archive fields are missing
        archive_fields = ["isArchived", "archivedAt", "archivedBy", "archiveReason"]
        missing_fields = [field for field in archive_fields if field not in data]
        
        if missing_fields:
            updates = {
                "isArchived": data.get("isArchived", False),
                "archivedAt": data.get("archivedAt", None),
                "archivedBy": data.get("archivedBy", None),
                "archiveReason": data.get("archiveReason", None)
            }
            events_ref.document(doc.id).update(updates)
            updated_count += 1
            print(f"✅ Updated event: {data.get('eventName', 'Unnamed Event')} (Missing: {missing_fields})")
    
    print(f"\n📊 Backfill Summary:")
    print(f"Total events checked: {total_checked}")
    print(f"Events updated: {updated_count}")
    print(f"Events already had archive fields: {total_checked - updated_count}")


if __name__ == "__main__":
    # Uncomment the task you want to test

    #show_sample_ticketmaster_events("Tempe", "AZ")
    #test_archive_fields_in_parsed_events()
    #asyncio.run(test_eventbrite_archive_fields())
    #show_all_user_locations()
    run_ingestion_for_all_cities()
    # backfill_user_events_metadata()
    # migrate_ticketmaster_events()
    #delete_old_events()  # This will delete events older than 1 year
    # backfill_archive_fields()
    pass