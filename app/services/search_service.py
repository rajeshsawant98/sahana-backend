"""
Natural language event search.

Phase 1: GPT-4o-mini parses the query into structured filters, which are
fed into the existing SQL pipeline.

Phase 2: pgvector ANN search using event embeddings, with hard filters
(city, state, date) from the LLM parser still applied as WHERE clauses.
Falls back to Phase 1 SQL path if query embedding is unavailable.
"""
import base64
import json
import os
from datetime import date, timedelta
from typing import Optional, Tuple

from openai import AsyncOpenAI

from app.models.pagination import CursorPaginationParams, EventCursorPaginatedResponse, EventFilters
from app.models.search import ParsedSearchQuery
from app.repositories.events.event_query_repository import EventQueryRepository
from app.services.embedding_service import generate_query_embedding
from app.services.event_service import get_all_events_paginated
from app.utils.cache_keys import embedding_cache_key, search_cache_key, TTL_EMBEDDING, TTL_EVENT_QUERY
from app.utils.logger import get_service_logger
from app.utils.redis_client import get_redis_client

_event_query_repo = EventQueryRepository()

logger = get_service_logger(__name__)


def _encode_semantic_cursor(offset: int) -> str:
    """Encode an offset as a base64 semantic cursor (distinct from keyset cursors)."""
    return base64.b64encode(json.dumps({"type": "semantic", "offset": offset}).encode()).decode()


def _decode_semantic_cursor(cursor: str) -> Optional[int]:
    """Decode a semantic cursor, returning the offset. Returns None if not a semantic cursor."""
    try:
        data = json.loads(base64.b64decode(cursor.encode()).decode())
        if data.get("type") == "semantic":
            return data["offset"]
    except Exception:
        pass
    return None

_openai_client: Optional[AsyncOpenAI] = None


def _get_openai_client() -> Optional[AsyncOpenAI]:
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set — natural language search unavailable")
            return None
        _openai_client = AsyncOpenAI(api_key=api_key)
    return _openai_client


_SYSTEM_PROMPT = """\
You are a search intent parser for an event discovery app.
Extract structured filters from the user's natural language query.

Return ONLY valid JSON matching this schema (use null for missing fields):
{{
  "city": string | null,
  "state": string | null,
  "category": string | null,
  "keywords": string | null,
  "is_online": boolean | null,
  "start_date": "YYYY-MM-DD" | null,
  "end_date": "YYYY-MM-DD" | null
}}

Rules:
- category must be one of: Music, Food & Drink, Sports, Arts, Nightlife, Community, Education, Tech, Health, Other — or null if unclear.
- keywords: descriptor words NOT already captured by category (e.g. "rock", "vegan", "5k run"). Do NOT include city/state names in keywords.
- city: extract any city name mentioned, even without "in" (e.g. "baseball tempe" → city="Tempe"). Null if only a state is mentioned.
- state: always return the 2-letter US abbreviation. Infer from city when obvious (Brooklyn→NY, Tempe→AZ, Austin→TX). Convert full state names (arizona→AZ, texas→TX, california→CA).
- Dates: "this weekend" = upcoming Saturday–Sunday. "tonight" = today. Today is {today}.

Examples:
- "rock concerts in tempe" → {{"city":"Tempe","state":"AZ","category":"Music","keywords":"rock"}}
- "baseball games tempe" → {{"city":"Tempe","state":"AZ","category":"Sports","keywords":"baseball"}}
- "food and drinks brooklyn" → {{"city":"Brooklyn","state":"NY","category":"Food & Drink","keywords":null}}
- "online yoga this weekend" → {{"is_online":true,"category":"Health","keywords":"yoga","start_date":"{saturday}","end_date":"{sunday}"}}
- "food festivals in arizona" → {{"city":null,"state":"AZ","category":"Food & Drink","keywords":"festivals"}}
- "concerts in new york" → {{"city":"New York","state":"NY","category":"Music","keywords":null}}
"""


async def _parse_query(query: str) -> ParsedSearchQuery:
    """Call GPT-4o-mini to extract structured intent. Returns empty filters on failure."""
    client = _get_openai_client()
    if client is None:
        return ParsedSearchQuery()

    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7 or 7
    saturday = today + timedelta(days=days_until_saturday)
    sunday = saturday + timedelta(days=1)
    system = _SYSTEM_PROMPT.format(
        today=today.isoformat(),
        saturday=saturday.isoformat(),
        sunday=sunday.isoformat(),
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": query},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=200,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return ParsedSearchQuery(**{k: v for k, v in data.items() if k in ParsedSearchQuery.model_fields})
    except Exception as e:
        logger.warning(f"[SearchService] LLM parse failed for '{query}': {e}")
        return ParsedSearchQuery()


def _strip_location_words(keywords: Optional[str], city: Optional[str], state: Optional[str]) -> Optional[str]:
    """Remove city/state tokens from keywords so location never leaks into the tsvector search."""
    if not keywords:
        return keywords
    stop: set[str] = set()
    if city:
        stop.update(city.lower().split())
    if state:
        stop.add(state.lower())
    filtered = [w for w in keywords.split() if w.lower() not in stop]
    return " ".join(filtered) if filtered else None


async def search_events(
    query: str,
    cursor_params: CursorPaginationParams,
) -> EventCursorPaginatedResponse:
    """
    Natural language event search.

    1. Check Redis for a cached response for this exact query string.
    2. Call GPT-4o-mini to parse the query into EventFilters.
    3. Run the existing paginated SQL pipeline.
    4. Cache and return the response.
    """
    redis = get_redis_client()
    cache_key = search_cache_key(query)

    # Cache check (only for first page — cursored pages vary)
    if redis is not None and cursor_params.cursor is None:
        try:
            cached = await redis.get(cache_key)
            if cached:
                logger.debug(f"[SearchCache] hit {cache_key}")
                return EventCursorPaginatedResponse(**json.loads(cached))
        except Exception:
            pass

    parsed = await _parse_query(query)
    logger.info(
        f"[SearchService] query='{query}' → "
        f"city={parsed.city} state={parsed.state} category={parsed.category} "
        f"keywords={parsed.keywords} is_online={parsed.is_online} "
        f"start={parsed.start_date} end={parsed.end_date}"
    )

    # ── Phase 2: pgvector semantic search ────────────────────────────────────
    # Uses offset-based pagination (semantic ranking has no stable keyset).
    # Cursor encodes {"type": "semantic", "offset": N} — distinct from keyset cursors.
    semantic_offset = _decode_semantic_cursor(cursor_params.cursor) if cursor_params.cursor else 0
    is_semantic_cursor = semantic_offset is not None

    if cursor_params.cursor is None or is_semantic_cursor:
        offset = semantic_offset or 0
        parts = []
        if parsed.category:
            parts.append(f"{parsed.category} events.")
        if parsed.keywords:
            parts.append(parsed.keywords + ".")
        if parsed.city:
            parts.append(f"Location: {parsed.city}" + (f", {parsed.state}." if parsed.state else "."))
        enriched_query = " ".join(parts) if parts else query

        # Cache embedding per enriched query — paginated requests reuse it without calling OpenAI
        emb_key = embedding_cache_key(enriched_query)
        query_embedding = None
        if redis is not None:
            try:
                cached_emb = await redis.get(emb_key)
                if cached_emb:
                    query_embedding = json.loads(cached_emb)
            except Exception:
                pass
        if query_embedding is None:
            query_embedding = await generate_query_embedding(enriched_query)
            if query_embedding is not None and redis is not None:
                try:
                    await redis.set(emb_key, json.dumps(query_embedding), ex=TTL_EMBEDDING)
                except Exception:
                    pass
        if query_embedding is not None:
            page_size = cursor_params.page_size
            rows = await _event_query_repo.search_events_by_embedding(
                query_embedding, parsed, limit=page_size, offset=offset
            )
            has_next = len(rows) > page_size
            page = rows[:page_size]
            next_cursor = _encode_semantic_cursor(offset + page_size) if has_next else None
            prev_cursor = _encode_semantic_cursor(offset - page_size) if offset > 0 else None
            response = EventCursorPaginatedResponse.create(
                items=page,
                next_cursor=next_cursor,
                prev_cursor=prev_cursor,
                has_next=has_next,
                has_previous=offset > 0,
                page_size=page_size,
            )
            logger.info(
                f"[SearchService] semantic path: enriched='{enriched_query}' "
                f"offset={offset} returning={len(page)} has_next={has_next}"
            )
            if page:
                if redis is not None and offset == 0:
                    try:
                        await redis.set(cache_key, response.model_dump_json(), ex=TTL_EVENT_QUERY)
                    except Exception:
                        pass
                return response
            logger.info("[SearchService] semantic returned 0 — falling back to Phase 1 SQL")

    # ── Phase 1 fallback: structured SQL filters ─────────────────────────────
    # Used when embedding is unavailable, or for subsequent cursor pages.
    clean_keywords = _strip_location_words(parsed.keywords, parsed.city, parsed.state)
    kw_parts = [p for p in [clean_keywords, parsed.category] if p]
    combined_keywords = " ".join(kw_parts) if kw_parts else None

    filters = EventFilters(
        city=parsed.city,
        state=parsed.state,
        keywords=combined_keywords,
        is_online=parsed.is_online,
        start_date=parsed.start_date,
        end_date=parsed.end_date,
    )

    response = await get_all_events_paginated(cursor_params, filters)

    # Cache first-page results
    if redis is not None and cursor_params.cursor is None:
        try:
            await redis.set(cache_key, response.model_dump_json(), ex=TTL_EVENT_QUERY)
        except Exception:
            pass

    return response
