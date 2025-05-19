

from app.services.events_retrival_service import fetch_ticketmaster_events , get_unique_user_locations, ingest_events_for_all_cities
import json
from app.auth.firebase_init import get_firestore_client

if __name__ == "__main__":
    # events = fetch_ticketmaster_events("Tempe", "AZ")
    # print(f"\n🔍 Total Events Fetched: {len(events)}\n")

    # for i, e in enumerate(events, 1):
    #     print(f"📌 Event #{i}")
    #     print(f"Name       : {e['eventName']}")
    #     print(f"Date/Time  : {e['startTime']}")
    #     print(f"Venue      : {e['location']['name']}")
    #     print(f"Address    : {e['location']['formattedAddress']}")
    #     print(f"City/State : {e['location']['city']}, {e['location']['country']}")
    #     print(f"Latitude   : {e['location']['latitude']}")
    #     print(f"Longitude  : {e['location']['longitude']}")
    #     print(f"Categories : {e['categories']}")
    #     print(f"Online?    : {e['isOnline']}")
    #     print(f"Join Link  : {e['joinLink']}")
    #     print(f"Image URL  : {e['imageURL']}")
    #     print(f"Description: {e['description'][:100]}...")
    #     print("-" * 60)
    
    # locations = get_unique_user_locations()
    # print(f"\n🔍 Total Unique Locations: {len(locations)}\n")
    
    # for i, loc in enumerate(locations, 1):
    #     print(f"📌 Location #{i}")
    #     print(f"City: {loc[0]}")
    #     print(f"State: {loc[1]}")
    #     print("-" * 60)
        
    # result = ingest_events_for_all_cities()

    # print(f"\n✅ Ingestion Summary")
    # print(f"Total Events Saved   : {result['total_events']}")
    # print(f"Total Cities Processed: {result['processed_cities']}")
    # print("\nDetails:")
    # for detail in result["details"]:
    #     print(f"• {detail}")
    
    # def backfill_user_events_metadata():
    #     db = get_firestore_client()
    #     events_ref = db.collection("events")

    #     updated_count = 0
    #     for doc in events_ref.stream():
    #         data = doc.to_dict()

    #         # Only update if missing 'origin' or 'source'
    #         if "origin" not in data or "source" not in data:
    #             updates = {
    #                 "origin": data.get("origin", "community"),
    #                 "source": data.get("source", "user")
    #             }
    #             events_ref.document(doc.id).update(updates)
    #             updated_count += 1

    #     print(f"✅ Backfilled {updated_count} user events with origin/source")
    
    # backfill= backfill_user_events_metadata()



    def migrate_ticketmaster_events():
        db = get_firestore_client()
        old_ref = db.collection("ticketmasterEvents")
        new_ref = db.collection("events")

        for doc in old_ref.stream():
            data = doc.to_dict()
            data["origin"] = "external"
            data["source"] = "ticketmaster"
            data["originalId"] = data.get("eventId")
            new_ref.document(data["eventId"]).set(data)

        print("✅ Ticketmaster events migrated to unified 'events' collection.")
        
    migrate= migrate_ticketmaster_events()
    print(json.dumps(migrate, indent=2))
