import json
import asyncio
from app.services.event_ingestion_service import (
    fetch_ticketmaster_events,
    get_unique_user_locations,
    ingest_events_for_all_cities
)
from app.services.event_service import (
    delete_old_events
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




if __name__ == "__main__":
    # Uncomment the task you want to test

    #show_sample_ticketmaster_events("Tempe", "AZ")
    #show_all_user_locations()
    #run_ingestion_for_all_cities()
    # backfill_user_events_metadata()
    # migrate_ticketmaster_events()
    delete_old_events()  # This will delete events older than 1 year
    pass