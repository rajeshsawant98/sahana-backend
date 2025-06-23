from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import time
from app.utils.event_parser import parse_eventbrite_data

def scrape_eventbrite(city="Tempe", state="AZ", max_scrolls=10, seen_links=None):
    if seen_links is None:
        seen_links = set()

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        url = f"https://www.eventbrite.com/d/{state.lower()}--{city.lower()}/all-events/"
        print(f"🔍 Navigating to {url}")
        page.goto(url, timeout=60000)

        for _ in range(max_scrolls):
            page.mouse.wheel(0, 6000)
            time.sleep(1.5)
        time.sleep(3)

        links = {
            urljoin("https://www.eventbrite.com", a.get_attribute("href"))
            for a in page.query_selector_all("a[href*='/e/']")
            if a.get_attribute("href")
        }

        for href in links:
            if href in seen_links:
                continue

            detail_page = context.new_page()
            try:
                detail_page.goto(href, timeout=30000, wait_until="networkidle")
                detail_page.wait_for_timeout(3000)
                server_data = detail_page.evaluate("window.__SERVER_DATA__")

                if server_data:
                    parsed = parse_eventbrite_data(server_data)
                    results.append(parsed)
                    seen_links.add(href)

            except Exception as e:
                print(f"[ERROR] Skipping {href}: {e}")
            finally:
                detail_page.close()

        browser.close()

    print(f"✅ Scraped {len(results)} events.")
    return results