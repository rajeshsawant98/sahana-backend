from app.services.events_retrival_service import fetch_ticketmaster_events , get_unique_user_locations, ingest_events_for_all_cities
import json

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
        
    result = ingest_events_for_all_cities()

    print(f"\n✅ Ingestion Summary")
    print(f"Total Events Saved   : {result['total_events']}")
    print(f"Total Cities Processed: {result['processed_cities']}")
    print("\nDetails:")
    for detail in result["details"]:
        print(f"• {detail}")
