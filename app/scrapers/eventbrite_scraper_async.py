import asyncio
from urllib.parse import urljoin
import time
import json
from playwright.async_api import async_playwright
from app.utils.event_parser import parse_eventbrite_data

async def scrape_eventbrite_async(city="Tempe", state="AZ", max_scrolls=10, seen_links=None):
    if seen_links is None:
        seen_links = set()

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=100)
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
        await asyncio.sleep(3)

        elements = await page.query_selector_all("a[href*='/e/']")
        links = {
            urljoin("https://www.eventbrite.com", await el.get_attribute("href"))
            for el in elements
            if await el.get_attribute("href")
        }

        for href in links:
            if href in seen_links:
                continue

            detail_page = await context.new_page()
            try:
                await detail_page.goto(href, timeout=30000, wait_until="networkidle")
                await detail_page.wait_for_timeout(3000)
                server_data = await detail_page.evaluate("window.__SERVER_DATA__")

                # Handle stringified server_data
                attempts = 0
                while isinstance(server_data, str) and attempts < 2:
                    try:
                        server_data = json.loads(server_data)
                        attempts += 1
                    except json.JSONDecodeError:
                        print(f"[ERROR] Failed to decode server_data at {href}")
                        server_data = None
                        break

                if isinstance(server_data, dict):
                    parsed = parse_eventbrite_data(server_data)
                    results.append(parsed)
                    seen_links.add(href)
                else:
                    print(f"[ERROR] Invalid server_data at {href} ({type(server_data)})")

            except Exception as e:
                print(f"[ERROR] Skipping {href}: {e}")
            finally:
                await detail_page.close()

        await browser.close()

    print(f"✅ Scraped {len(results)} events.")
    return results