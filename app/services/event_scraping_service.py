# from app.scrapers.eventbrite_scraper import scrape_eventbrite

# def get_eventbrite_events(city: str, state: str, seen_links=None) -> list[dict]:
#     return scrape_eventbrite(city, state, seen_links=seen_links)

from app.scrapers.eventbrite_scraper_async import scrape_eventbrite_async

async def get_eventbrite_events(city: str, state: str, seen_links=None) -> list[dict]:
    return await scrape_eventbrite_async(city, state, seen_links=seen_links)

# from playwright.sync_api import sync_playwright
# import json
# import time
# from urllib.parse import urljoin
# from datetime import datetime, timezone
# from uuid import uuid4

# def fetch_event_details(context, event_url):
    
#     page = context.new_page()
#     try:
#         page.goto(event_url, timeout=30000, wait_until="networkidle")
#     except Exception as e:
#         print(f"Failed to load {event_url}: {e}")
#         page.close()
#         return {}
#     page.wait_for_timeout(3000)

#     try:
#         server_data = page.evaluate("window.__SERVER_DATA__")
#     except Exception as e:
#         print(f"Failed to evaluate window.__SERVER_DATA__: {e}")
#         page.close()
#         return {}

#     event = server_data.get("event", {})
#     components = server_data.get("components", {})

#     result = build_event_object(event, components, server_data)

#     page.close()
#     return result

# def build_event_object(event, components, server_data):

#     try:
#         city = components.get("eventDetails", {}).get("location", {}).get("venueMultilineAddress", [None, "Unknown, XX"])[1].split(",")[0].strip()
#         print(f"City extracted: {city}")
#     except Exception:
#         city = "Unknown"
#     state = server_data.get("event", {}).get("venue", {}).get("region", "XX")
#     print(f"State extracted: {state}")

#     image_url = server_data.get("event_listing_response", {}).get("schemaInfo", {}).get("schemaImageUrl", None)
#     organizer_data = components.get("organizer", {})
#     organizer_name = organizer_data.get("name", "Eventbrite Organizer")

#     event_map = components.get("eventMap", {})
#     location = {
#         "name": event_map.get("venueName", "Unknown Venue"),
#         "city": city,
#         "state": state,
#         "country": "United States",
#         "latitude": float(event_map.get("location", {}).get("latitude", 0.0)),
#         "longitude": float(event_map.get("location", {}).get("longitude", 0.0)),
#         "formattedAddress": event_map.get("venueAddress", "N/A")
#     }

#     raw_tags = components.get("tags", [])
#     tags = [tag.get("text") for tag in raw_tags if isinstance(tag, dict) and "text" in tag]

#     description = components.get("eventDescription", {}).get("summary", "")

#     join_link = components.get("eventDetails", {}).get("onlineEvent", {}).get("url", "")

#     ticket_classes = server_data.get("event_listing_response", {}).get("tickets", {}).get("ticketClasses", [])
#     ticket_info = {}
#     if ticket_classes:
#         first_ticket = ticket_classes[0]
#         total_cost = first_ticket.get("totalCost", {})
#         ticket_info = {
#             "name": first_ticket.get("name", "General Admission"),
#             "price": float(total_cost.get("majorValue", "0.0")),
#             "currency": total_cost.get("currency", "USD"),
#             "remaining": first_ticket.get("quantityRemaining", -1)
#         }
#         price_text = f"{ticket_info['price']} {ticket_info['currency']}"
#     else:
#         ticket_info = {
#             "name": "General Admission",
#             "price": 0.0,
#             "currency": "USD",
#             "remaining": -1
#         }
#         price_text = "Free"

#     is_online = event.get("isOnlineEvent", False)

#     categories = list(filter(None, [
#         event["format"]["name"] if isinstance(event.get("format"), dict) else event.get("format"),
#         event["category"]["name"] if isinstance(event.get("category"), dict) else event.get("category"),
#         event["subcategory"]["name"] if isinstance(event.get("subcategory"), dict) else event.get("subcategory")
#     ]))

#     result = {
#         "eventId": event.get("id") or str(uuid4()),
#         "eventName": event.get("name", "Untitled Event").strip(),
#         "location": location,
#         "startTime": event.get("start", {}).get("utc"),
#         "duration": (
#             int(
#                 (
#                     datetime.fromisoformat(event.get("end", {}).get("utc", datetime.now(timezone.utc).isoformat()))
#                     - datetime.fromisoformat(event.get("start", {}).get("utc", datetime.now(timezone.utc).isoformat()))
#                 ).total_seconds() // 60
#             )
#             if event.get("start", {}).get("utc") and event.get("end", {}).get("utc")
#             else 120
#         ),
#         "categories": categories,
#         "isOnline": is_online,
#         "joinLink": join_link,
#         "imageUrl": image_url,
#         "createdBy": organizer_name,
#         "createdByEmail": "scraper@eventbrite.com",
#         "createdAt": datetime.now(timezone.utc).isoformat(),
#         "description": description or "No description available",
#         "rsvpList": [],
#         "origin": "external",
#         "source": "eventbrite",
#         "originalId": event.get("id"),
#         "price": price_text,
#         "ticket": ticket_info,
#         "format": event["format"]["name"] if isinstance(event.get("format"), dict) else event.get("format", "Event"),
#         "category": event["category"]["name"] if isinstance(event.get("category"), dict) else event.get("category", "General"),
#         "subCategory": event["subcategory"]["name"] if isinstance(event.get("subcategory"), dict) else event.get("subcategory", ""),
#         "tags": tags
#     }
#     return result

# def scrape_eventbrite(city="Tempe", state="AZ", max_scrolls=10, seen_links=None):
#     if seen_links is None:
#         seen_links = set()
        

#     results = []

#     def extract_event_links(page):
#         links = page.query_selector_all("a[href*='/e/']")
#         hrefs = set()
#         for link in links:
#             href = link.get_attribute("href")
#             if href:
#                 full_url = urljoin("https://www.eventbrite.com", href)
#                 hrefs.add(full_url)
#         return list(hrefs)

#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True, slow_mo=100)
#         context = browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
#         page = context.new_page()

#         url = f"https://www.eventbrite.com/d/{state.lower()}--{city.lower()}/all-events/"
#         print(f"🔍 Navigating to {url}")
#         page.goto(url, timeout=60000)

#         for _ in range(max_scrolls):
#             page.mouse.wheel(0, 6000)
#             time.sleep(1.5)
#         time.sleep(3)

#         scraped_urls = []
#         failed_urls = []

#         hrefs = extract_event_links(page)

#         for href in hrefs:
#             if href in seen_links:
#                 print(f"🔗 Skipping already seen link: {href}")
#                 continue
#             try:
#                 details = fetch_event_details(context, href)
#                 if not details:
#                     print(f"❌ Skipping event due to missing details: {href}")
#                     continue
#                 seen_links.add(href)
#                 results.append(details)
#                 scraped_urls.append(href)
#             except Exception as e:
#                 print(f"⚠️ Error fetching details for {href}: {e}")
#                 failed_urls.append(href)

#         browser.close()

#     with open("scraped_urls.log", "a") as f:
#         f.write("\n".join(scraped_urls))
#     with open("failed_urls.log", "a") as f:
#         f.write("\n".join(failed_urls))

#     # with open("eventbrite_events.json", "a", encoding="utf-8") as f:
#     #     json.dump(results, f, indent=2)
#     print(f"✅ Scraped {len(results)} unique events.")
#     return results

# if __name__ == "__main__":
#     scrape_eventbrite("Tempe", "AZ")

