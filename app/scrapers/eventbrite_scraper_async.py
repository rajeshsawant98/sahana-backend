import asyncio
import json
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from app.utils.event_parser import parse_eventbrite_jsonld, parse_eventbrite_server_data, is_schema_event
from app.utils.logger import get_service_logger

logger = get_service_logger(__name__)

# Max concurrent detail-page fetches within a single city scrape
_detail_semaphore = asyncio.Semaphore(5)


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
    async with _detail_semaphore:
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


async def _collect_listing_page(page, base_url: str, max_pages: int, seen_canonical: set) -> dict[str, list[str]]:
    """
    Paginate through Eventbrite listing pages and collect canonical event URLs
    with their categories.  Stops early when a page yields no new links.
    Returns: {canonical_url: [category, ...]}
    """
    link_categories: dict[str, list[str]] = {}

    for page_num in range(1, max_pages + 1):
        url = base_url if page_num == 1 else f"{base_url}?page={page_num}"
        logger.info(f"Listing page {page_num}: {url}")

        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(2)  # let lazy-loaded cards settle
        except Exception as e:
            logger.warning(f"Failed to load listing page {page_num}: {e}")
            break

        elements = await page.query_selector_all("a[data-event-id]")
        new_this_page = 0
        for el in elements:
            raw = await el.get_attribute("href")
            cat = await el.get_attribute("data-event-category")
            if not raw:
                continue
            full = urljoin("https://www.eventbrite.com", raw)
            c = _canonical_url(full)
            if c not in link_categories and c not in seen_canonical:
                link_categories[c] = [cat] if cat else []
                new_this_page += 1

        logger.info(f"  → {new_this_page} new links (total so far: {len(link_categories)})")
        if new_this_page == 0:
            break  # no new events, stop paginating

    return link_categories


# Category slugs to scrape per city. Order matters — all-events first gives the
# broadest set; categories after it fill in gaps with genre-specific events.
_CATEGORY_SLUGS = [
    "all-events",
    "music-events",
    "food-and-drink",
    "arts",
    "nightlife",
    "sports-and-fitness",
    "science-and-tech",
    "family-and-education",
    "health",
    "charity-and-causes",
    "community",
]


async def scrape_eventbrite_async(city="Tempe", state="AZ", max_pages=3, seen_links=None):
    if seen_links is None:
        seen_links = set()

    seen_canonical: set[str] = {_canonical_url(u) for u in seen_links}
    location = f"{state.lower()}--{city.lower()}"
    link_categories: dict[str, list[str]] = {}  # canonical -> [category]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ))

        # ── Paginated listing across all category slugs ───────────────────────
        listing_page = await context.new_page()
        for slug in _CATEGORY_SLUGS:
            base_url = f"https://www.eventbrite.com/d/{location}/{slug}/"
            new_links = await _collect_listing_page(listing_page, base_url, max_pages, seen_canonical | set(link_categories))
            link_categories.update(new_links)
            logger.info(f"[{city}] {slug}: +{len(new_links)} new links (total: {len(link_categories)})")
        await listing_page.close()

        # ── Concurrent detail page fetches ────────────────────────────────────
        remaining = list(link_categories.keys())
        logger.info(f"[{city}] Fetching {len(remaining)} unique detail pages")

        tasks = [
            fetch_event_detail(context, href, seen_canonical, extra_categories=link_categories[href])
            for href in remaining
        ]
        results = [e for e in await asyncio.gather(*tasks) if e]

        await browser.close()

    logger.info(f"[{city}] Scraped {len(results)} Eventbrite events.")
    return results
