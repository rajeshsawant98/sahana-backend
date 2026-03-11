"""
Diagnostic script: inspect what data Eventbrite actually serves on event pages.
Run: python3 -m app.test.eventbrite_page_inspector
"""
import asyncio
import json
from urllib.parse import urljoin
from playwright.async_api import async_playwright

LISTING_URL = "https://www.eventbrite.com/d/az--tempe/all-events/"
MAX_DETAIL_PAGES = 2   # only inspect this many event pages


def _try_parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _summarize(obj, depth=0, max_depth=3) -> str:
    """Recursively summarize a JSON object to show its shape."""
    indent = "  " * depth
    if depth >= max_depth:
        return f"<truncated: {type(obj).__name__}>"
    if isinstance(obj, dict):
        lines = ["{"]
        for k, v in list(obj.items())[:20]:
            lines.append(f"{indent}  {k!r}: {_summarize(v, depth+1, max_depth)},")
        if len(obj) > 20:
            lines.append(f"{indent}  ... ({len(obj) - 20} more keys)")
        lines.append(f"{indent}}}")
        return "\n".join(lines)
    if isinstance(obj, list):
        if not obj:
            return "[]"
        preview = f"[{len(obj)} items, first: {_summarize(obj[0], depth+1, max_depth)}]"
        return preview
    if isinstance(obj, str) and len(obj) > 120:
        return repr(obj[:120] + "...")
    return repr(obj)


async def inspect_page(page, url: str, label: str):
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"  {url}")
    print(f"{'='*70}")

    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(2)

    # 1. Check all window.__ variables
    print("\n── JS window variables ──────────────────────────────────────────")
    candidates = [
        "__SERVER_DATA__", "__NEXT_DATA__", "__REDUX_STATE__",
        "__eb_sdk_data__", "__APP_STATE__", "__INITIAL_STATE__",
        "EB", "EventbriteData", "__eventbrite__"
    ]
    found_vars = {}
    for var in candidates:
        try:
            val = await page.evaluate(f"window['{var}']")
            if val:
                found_vars[var] = val
                print(f"  ✅ window.{var} found (type={type(val).__name__})")
                if isinstance(val, dict):
                    print(f"     top-level keys: {list(val.keys())[:15]}")
                elif isinstance(val, str) and len(val) < 200:
                    print(f"     value: {val!r}")
            else:
                print(f"  ✗  window.{var} = null/undefined")
        except Exception as e:
            print(f"  ✗  window.{var} error: {e}")

    # 2. Dump found JS variable structures
    for var_name, val in found_vars.items():
        print(f"\n── {var_name} structure ──────────────────────────────────────────")
        if isinstance(val, str):
            parsed = _try_parse_json(val)
            val = parsed if parsed else val
        print(_summarize(val, max_depth=4))

    # 3. All <script> tags — size and first 300 chars
    print("\n── <script> tags (non-src) ──────────────────────────────────────")
    scripts = await page.eval_on_selector_all(
        "script:not([src])",
        "els => els.map(el => ({id: el.id, type: el.type, text: el.textContent}))"
    )
    for i, s in enumerate(scripts):
        text = s.get("text", "")
        tag_id = s.get("id", "")
        tag_type = s.get("type", "")
        print(f"\n  Script #{i+1}  id={tag_id!r}  type={tag_type!r}  len={len(text)}")
        if text.strip().startswith("{") or text.strip().startswith("["):
            parsed = _try_parse_json(text)
            if parsed:
                print(f"  → valid JSON, keys: {list(parsed.keys())[:10] if isinstance(parsed, dict) else f'list of {len(parsed)}'}")
                print(f"  → structure: {_summarize(parsed, max_depth=3)}")
            else:
                print(f"  → first 300 chars: {text[:300]!r}")
        else:
            print(f"  → first 300 chars: {text[:300]!r}")

    # 4. JSON-LD scripts
    print("\n── JSON-LD (<script type=application/ld+json>) ──────────────────")
    jsonld_texts = await page.eval_on_selector_all(
        'script[type="application/ld+json"]',
        "els => els.map(el => el.textContent)"
    )
    if not jsonld_texts:
        print("  (none found)")
    for i, text in enumerate(jsonld_texts):
        print(f"\n  LD+JSON #{i+1}:")
        parsed = _try_parse_json(text)
        if parsed:
            print(_summarize(parsed, max_depth=5))
        else:
            print(f"  (parse failed) raw: {text[:300]!r}")

    # 5. Key DOM elements
    print("\n── DOM: event card structure ────────────────────────────────────")
    dom_info = await page.evaluate("""() => {
        const selectors = [
            '[data-event-id]',
            '[data-testid="event-card"]',
            '.eds-event-card',
            'article',
            '[class*="EventCard"]',
            '[class*="event-card"]',
            'h1', 'h2', 'h3',
            'time',
            '[datetime]',
        ];
        const result = {};
        for (const sel of selectors) {
            const els = document.querySelectorAll(sel);
            if (els.length > 0) {
                result[sel] = {
                    count: els.length,
                    first_attrs: Object.fromEntries(
                        [...els[0].attributes].map(a => [a.name, a.value.substring(0, 100)])
                    ),
                    first_text: els[0].textContent.trim().substring(0, 150)
                };
            }
        }
        return result;
    }""")
    for sel, info in dom_info.items():
        print(f"\n  {sel!r} → {info['count']} elements")
        print(f"    attrs: {info['first_attrs']}")
        print(f"    text:  {info['first_text']!r}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ))

        # ── Inspect listing page ─────────────────────────────────────────────
        page = await context.new_page()
        await inspect_page(page, LISTING_URL, "LISTING PAGE")

        # Collect a couple of event links
        elements = await page.query_selector_all("a[href*='/e/']")
        seen = set()
        links = []
        for el in elements:
            href = await el.get_attribute("href")
            if href:
                full = urljoin("https://www.eventbrite.com", href.split("?")[0])
                if full not in seen:
                    seen.add(full)
                    links.append(full)
            if len(links) >= MAX_DETAIL_PAGES:
                break

        await page.close()

        # ── Inspect detail pages ─────────────────────────────────────────────
        for i, href in enumerate(links, 1):
            detail_page = await context.new_page()
            await inspect_page(detail_page, href, f"EVENT DETAIL PAGE #{i}")
            await detail_page.close()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
