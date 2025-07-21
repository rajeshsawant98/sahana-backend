import asyncio
from urllib.parse import urljoin
import json
from playwright.async_api import async_playwright
from app.utils.event_parser import parse_eventbrite_data

# Limit concurrency to avoid tab/memory overload
semaphore = asyncio.Semaphore(10)

async def fetch_event_detail(context, href, seen_links):
    async with semaphore:
        if href in seen_links:
            return None

        page = await context.new_page()
        try:
            await page.goto(href, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(1.5)  # Give time for window.__SERVER_DATA__ to be injected

            server_data = await page.evaluate("window.__SERVER_DATA__")

            if not server_data:
                print(f"[WARN] No window.__SERVER_DATA__ found at {href}")
                return None

            # Handle stringified JSON inside JS variable
            for _ in range(2):
                if isinstance(server_data, str):
                    try:
                        server_data = json.loads(server_data)
                    except json.JSONDecodeError:
                        break

            if isinstance(server_data, dict):
                event = parse_eventbrite_data(server_data)
                if event:
                    seen_links.add(href)
                    return event
                else:
                    print(f"[SKIP] Event at {href} was filtered out (missing start date or abnormal duration)")
                    return None

            print(f"[ERROR] Invalid server_data at {href} — type={type(server_data)}")

        except Exception as e:
            print(f"[ERROR] Failed to scrape {href}: {e}")
        finally:
            await page.close()

        return None


async def scrape_eventbrite_async(city="Tempe", state="AZ", max_scrolls=10, seen_links=None):
    if seen_links is None:
        seen_links = set()

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ))

        page = await context.new_page()
        url = f"https://www.eventbrite.com/d/{state.lower()}--{city.lower()}/all-events/"
        print(f"🔍 Navigating to {url}")
        await page.goto(url, timeout=60000)

        for _ in range(max_scrolls):
            await page.mouse.wheel(0, 6000)
            await asyncio.sleep(1.5)
        await asyncio.sleep(2)

        elements = await page.query_selector_all("a[href*='/e/']")
        links = {
            urljoin("https://www.eventbrite.com", await el.get_attribute("href"))
            for el in elements
            if await el.get_attribute("href")
        }

        await page.close()

        # Concurrent fetch
        tasks = [fetch_event_detail(context, href, seen_links) for href in links]
        events = await asyncio.gather(*tasks)

        results.extend([e for e in events if e])

        await browser.close()

    print(f"✅ Scraped {len(results)} events from Eventbrite.")
    return results