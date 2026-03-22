"""
Backfill missing event coordinates in Firestore using geocoding fallback.

Default behavior is dry-run (no writes). Use --apply to persist updates.

Examples:
  python scripts/backfill_missing_event_coordinates.py
  python scripts/backfill_missing_event_coordinates.py --apply
  python scripts/backfill_missing_event_coordinates.py --apply --source eventbrite --limit 200

Provider config (free by default):
  GEOCODING_PROVIDER=nominatim   # default, OpenStreetMap
  GEOCODING_PROVIDER=geoapify    # requires GEOAPIFY_API_KEY
  GEOCODING_PROVIDER=google      # requires GOOGLE_MAPS_API_KEY
"""

import argparse
import asyncio
import sys
from typing import Iterable
from pathlib import Path

from google.api_core.exceptions import DeadlineExceeded, ServiceUnavailable

# Allow running as: python scripts/backfill_missing_event_coordinates.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth.firebase_init import get_firestore_client
from app.utils.geocoding import apply_geocode_fallback, build_address_candidates, build_address_query, get_geocoding_stats, has_valid_coordinates


DEFAULT_SOURCES = ("eventbrite", "ticketmaster")


def _parse_sources(raw: str) -> set[str]:
    value = (raw or "").strip().lower()
    if value == "all":
        return set()
    return {s.strip().lower() for s in value.split(",") if s.strip()}


def _should_include_event(data: dict, sources: set[str]) -> bool:
    if not sources:
        return True
    return (data.get("source") or "").strip().lower() in sources


def _iter_preview(items: list[dict], limit: int = 10) -> Iterable[dict]:
    for item in items[:limit]:
        yield item


def _print_progress(prefix: str, scanned: int, geocode_attempted: int, geocode_succeeded: int, unresolved: int, updated: int, failed: int, unique_addresses: int) -> None:
    geocoding_stats = get_geocoding_stats()
    print(
        f"{prefix} scanned={scanned} geocode_attempted={geocode_attempted} "
        f"geocode_succeeded={geocode_succeeded} unresolved={unresolved} "
        f"updated={updated} failed={failed} unique_addresses={unique_addresses} "
        f"provider_requests={geocoding_stats['provider_requests']} "
        f"provider_successes={geocoding_stats['provider_successes']} "
        f"provider_failures={geocoding_stats['provider_failures']} "
        f"cache_hits={geocoding_stats['cache_hits']} "
        f"fallback_queries_tried={geocoding_stats['fallback_queries_tried']} "
        f"rate_limited_retries={geocoding_stats['rate_limited_retries']}"
    )


async def backfill_coordinates(
    apply: bool,
    sources: set[str],
    limit: int | None,
    batch_size: int,
    max_provider_requests: int | None,
) -> None:
    db = get_firestore_client()
    events_ref = db.collection("events")

    scanned = 0
    source_filtered_out = 0
    already_valid = 0
    geocode_attempted = 0
    geocode_succeeded = 0
    unresolved = 0
    updated = 0
    failed = 0
    previews: list[dict] = []
    processed_doc_ids: set[str] = set()
    unique_addresses_seen: set[str] = set()
    resolution_counts = {"street": 0, "zip": 0, "city": 0, "unknown": 0}

    last_doc = None
    batch_number = 0
    stopped_for_budget = False
    while True:
        docs = await _read_batch_with_retry(events_ref, last_doc, batch_size=batch_size)
        if not docs:
            break
        batch_number += 1
        print(f"[BATCH {batch_number}] loaded {len(docs)} documents")

        for doc in docs:
            if doc.id in processed_doc_ids:
                continue
            processed_doc_ids.add(doc.id)

            data = doc.to_dict() or {}
            scanned += 1

            if not _should_include_event(data, sources):
                source_filtered_out += 1
                continue

            location = data.get("location")
            if has_valid_coordinates(location):
                already_valid += 1
                continue

            current_stats = get_geocoding_stats()
            if max_provider_requests is not None and current_stats["provider_requests"] >= max_provider_requests:
                stopped_for_budget = True
                print(
                    f"[STOP] provider_requests={current_stats['provider_requests']} reached "
                    f"max_provider_requests={max_provider_requests}"
                )
                break

            geocode_attempted += 1
            event_name = data.get("eventName") or "Untitled Event"
            source = data.get("source") or "unknown"
            city = (location or {}).get("city") if isinstance(location, dict) else None
            state = (location or {}).get("state") if isinstance(location, dict) else None
            address_query = build_address_query(location if isinstance(location, dict) else {})
            address_candidates = build_address_candidates(location if isinstance(location, dict) else {})
            if address_query:
                unique_addresses_seen.add(address_query)
            for candidate in address_candidates:
                unique_addresses_seen.add(candidate)
            print(
                f"[GEOCODE] #{geocode_attempted} doc={doc.id} source={source} "
                f"city={city or '-'} state={state or '-'} address={address_query or '-'} "
                f"event={event_name}"
            )
            if len(address_candidates) > 1:
                print(f"[GEOCODE][CANDIDATES] doc={doc.id} candidates={address_candidates}")
            new_location = await apply_geocode_fallback(location if isinstance(location, dict) else {})
            if not has_valid_coordinates(new_location):
                unresolved += 1
                print(f"[GEOCODE][MISS] doc={doc.id}")
                continue

            geocode_succeeded += 1
            resolution = new_location.get("geocodeResolution") or "unknown"
            resolution_counts[resolution] = resolution_counts.get(resolution, 0) + 1
            update_payload = {"location": new_location}
            previews.append(
                {
                    "docId": doc.id,
                    "eventName": data.get("eventName"),
                    "source": data.get("source"),
                    "oldLat": (location or {}).get("latitude") if isinstance(location, dict) else None,
                    "oldLng": (location or {}).get("longitude") if isinstance(location, dict) else None,
                    "newLat": new_location.get("latitude"),
                    "newLng": new_location.get("longitude"),
                    "resolution": resolution,
                }
            )
            print(
                f"[GEOCODE][HIT] doc={doc.id} lat={new_location.get('latitude')} "
                f"lng={new_location.get('longitude')} resolution={resolution}"
            )

            if apply:
                try:
                    await events_ref.document(doc.id).update(update_payload)
                    updated += 1
                    print(f"[WRITE] updated doc={doc.id} count={updated}")
                except Exception as e:
                    failed += 1
                    print(f"[ERROR] Failed to update {doc.id}: {e}")
                    continue
            else:
                updated += 1
                print(f"[DRY-RUN] would update doc={doc.id} count={updated}")

            if limit is not None and updated >= limit:
                break

        _print_progress(
            prefix=f"[BATCH {batch_number}][SUMMARY]",
            scanned=scanned,
            geocode_attempted=geocode_attempted,
            geocode_succeeded=geocode_succeeded,
            unresolved=unresolved,
            updated=updated,
            failed=failed,
            unique_addresses=len(unique_addresses_seen),
        )

        if stopped_for_budget:
            break
        if limit is not None and updated >= limit:
            break
        last_doc = docs[-1]

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"\n=== Backfill Missing Event Coordinates ({mode}) ===")
    print(f"Scanned total events             : {scanned}")
    print(f"Filtered out by source           : {source_filtered_out}")
    print(f"Already had valid coordinates    : {already_valid}")
    print(f"Geocode attempts                 : {geocode_attempted}")
    print(f"Geocode successes                : {geocode_succeeded}")
    geocoding_stats = get_geocoding_stats()
    print(f"Unique address queries           : {len(unique_addresses_seen)}")
    print(f"Provider requests               : {geocoding_stats['provider_requests']}")
    print(f"Provider successes              : {geocoding_stats['provider_successes']}")
    print(f"Provider failures               : {geocoding_stats['provider_failures']}")
    print(f"Geocoder cache hits             : {geocoding_stats['cache_hits']}")
    print(f"Fallback queries tried          : {geocoding_stats['fallback_queries_tried']}")
    print(f"Rate-limited retries            : {geocoding_stats['rate_limited_retries']}")
    print(f"Missing coords but not geocoded  : {unresolved}")
    print(f"{'Updated' if apply else 'Would update'} events      : {updated}")
    print(f"Street resolution hits          : {resolution_counts.get('street', 0)}")
    print(f"ZIP resolution hits             : {resolution_counts.get('zip', 0)}")
    print(f"City resolution hits            : {resolution_counts.get('city', 0)}")
    print(f"Unknown resolution hits         : {resolution_counts.get('unknown', 0)}")
    print(f"Stopped for request budget      : {stopped_for_budget}")
    if apply:
        print(f"Failed updates                   : {failed}")

    if previews:
        print("\nSample updates:")
        for item in _iter_preview(previews, limit=10):
            print(
                f"- {item['docId']} | {item['source']} | {item['eventName']} | "
                f"({item['oldLat']}, {item['oldLng']}) -> ({item['newLat']}, {item['newLng']}) "
                f"[{item['resolution']}]"
            )


async def _read_batch_with_retry(events_ref, last_doc, batch_size: int, retries: int = 4):
    """
    Read one batch with pagination and retry on transient Firestore stream timeouts.
    """
    attempt = 0
    while True:
        try:
            query = events_ref.order_by("__name__").limit(batch_size)
            if last_doc is not None:
                query = query.start_after(last_doc)

            docs = []
            async for doc in query.stream(timeout=120):
                docs.append(doc)
            return docs
        except (DeadlineExceeded, ServiceUnavailable) as e:
            attempt += 1
            if attempt > retries:
                raise
            wait_seconds = min(2 ** attempt, 15)
            print(f"[WARN] Firestore batch read timeout ({e.__class__.__name__}), retrying in {wait_seconds}s...")
            await asyncio.sleep(wait_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill missing event coordinates in Firestore.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist updates to Firestore. If omitted, runs as dry-run.",
    )
    parser.add_argument(
        "--source",
        default=",".join(DEFAULT_SOURCES),
        help="Comma-separated source filter (e.g. 'eventbrite,ticketmaster') or 'all'.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of events to update (or would update in dry-run).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="Firestore page size per read batch. Reduce this if you see stream timeouts.",
    )
    parser.add_argument(
        "--max-provider-requests",
        type=int,
        default=2500,
        help="Stop before exceeding this many provider requests in one run. Use 0 to disable.",
    )
    args = parser.parse_args()

    sources = _parse_sources(args.source)
    asyncio.run(
        backfill_coordinates(
            apply=args.apply,
            sources=sources,
            limit=args.limit,
            batch_size=max(1, args.batch_size),
            max_provider_requests=(None if args.max_provider_requests == 0 else max(1, args.max_provider_requests)),
        )
    )


if __name__ == "__main__":
    main()
