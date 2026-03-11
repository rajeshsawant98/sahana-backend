import asyncio
import json
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from app.utils.event_parser import parse_eventbrite_jsonld, parse_eventbrite_server_data, is_schema_event
from app.utils.logger import get_service_logger

logger = get_service_logger(__name__)

semaphore = asyncio.Semaphore(5)


def _canonical_url(href: str) -> str:
    """Strip tracking query params so the same event isn't visited twice."""
    parsed = urlparse(href)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def _collect_jsonld_events(jsonld_texts: list[str], url_hint: str = "", extra_categories: list[str] | None = None) -> list[dict]:
    """Parse all JSON-LD script tags and return Sahana-format events."""
    results = []
    for text in jsonld_texts:
        try:
            data = json.loads(text)
            candidates = []
            if isinstance(data, list):
                candidates = data
            elif isinstance(data, dict):
                if is_schema_event(data):
                    candidates = [data]
                elif "@graph" in data:
                    candidates = [c for c in data["@graph"] if isinstance(c, dict) and is_schema_event(c)]

            for item in candidates:
                href = item.get("url") or url_hint
                event = parse_eventbrite_jsonld(item, href, extra_categories=extra_categories)
                if event:
                    results.append(event)
        except Exception:
            continue
    return results


async def _try_js_var(page, var_name: str):
    """Safely evaluate a window variable, returning None on failure."""
    try:
        val = await page.evaluate(f"window['{var_name}']")
        if not val:
            return None
        for _ in range(2):
            if isinstance(val, str):
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, ValueError):
                    break
        return val if isinstance(val, dict) else None
    except Exception:
        return None


async def fetch_event_detail(context, href: str, seen_canonical: set, extra_categories: list[str] | None = None) -> dict | None:
    canonical = _canonical_url(href)
    async with semaphore:
        if canonical in seen_canonical:
            return None

        page = await context.new_page()
        try:
            await page.goto(href, timeout=30000, wait_until="domcontentloaded")

            # 1. Try window.__SERVER_DATA__ (still works on some pages)
            server_data = await _try_js_var(page, "__SERVER_DATA__")
            if server_data:
                event = parse_eventbrite_server_data(server_data, href)
                if event:
                    seen_canonical.add(canonical)
                    return event

            # 2. JSON-LD — covers Festival, SocialEvent, MusicEvent, etc.
            jsonld_texts = await page.eval_on_selector_all(
                'script[type="application/ld+json"]',
                "els => els.map(el => el.textContent)"
            )
            events = _collect_jsonld_events(jsonld_texts, href, extra_categories=extra_categories)
            if events:
                seen_canonical.add(canonical)
                return events[0]

            logger.warning(f"No event data found at {canonical}")

        except Exception as e:
            logger.error(f"Failed to scrape {canonical}: {e}")
        finally:
            await page.close()

        return None


async def scrape_eventbrite_async(city="Tempe", state="AZ", max_scrolls=10, seen_links=None):
    if seen_links is None:
        seen_links = set()

    seen_canonical: set[str] = {_canonical_url(u) for u in seen_links}
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ))

        # ── Listing page ─────────────────────────────────────────────────────
        page = await context.new_page()
        url = f"https://www.eventbrite.com/d/{state.lower()}--{city.lower()}/all-events/"
        logger.info(f"Navigating to {url}")
        await page.goto(url, timeout=60000)

        for _ in range(max_scrolls):
            await page.mouse.wheel(0, 6000)
            await asyncio.sleep(1.5)
        await asyncio.sleep(2)

        # Collect de-duplicated links + per-event categories from data-event-category
        link_categories: dict[str, list[str]] = {}  # canonical -> [category]
        elements = await page.query_selector_all("a[data-event-id]")
        for el in elements:
            raw = await el.get_attribute("href")
            cat = await el.get_attribute("data-event-category")
            if raw:
                full = urljoin("https://www.eventbrite.com", raw)
                c = _canonical_url(full)
                if c not in link_categories:
                    link_categories[c] = [cat] if cat else []

        await page.close()

        # ── Detail pages (for links not resolved from listing page) ──────────
        remaining = [(c, c) for c in link_categories if c not in seen_canonical]
        logger.info(f"Visiting {len(remaining)} detail pages (de-duped from {len(link_categories)} raw links)")

        tasks = [
            fetch_event_detail(context, href, seen_canonical, extra_categories=link_categories.get(c))
            for c, href in remaining
        ]
        detail_events = await asyncio.gather(*tasks)
        results.extend([e for e in detail_events if e])

        await browser.close()

    logger.info(f"Scraped {len(results)} events from Eventbrite.")
    return results
