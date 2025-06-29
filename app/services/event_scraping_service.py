from app.scrapers.eventbrite_scraper_async import scrape_eventbrite_async

async def get_eventbrite_events(city: str, state: str, seen_links=None) -> list[dict]:
    return await scrape_eventbrite_async(city, state, seen_links=seen_links)
