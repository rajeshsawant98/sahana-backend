# Backend Analysis Report

## 1. Critical Performance Issues: Blocking I/O in Async Routes

**Severity: High**

The application mixes `async def` route handlers with synchronous service and repository calls. In FastAPI, `async def` endpoints run on the main event loop. If you call a synchronous blocking function (like a network call to Firestore) directly within an `async def` function, it blocks the entire event loop, preventing the server from handling other requests concurrently.

**Evidence:**

- `app/routes/event_routes.py`: Endpoints are defined as `async def`.
- `app/services/event_service.py`: Methods are defined as `def` (synchronous).
- `app/repositories/base_repository.py`: Uses the synchronous `google.cloud.firestore` client.

**Impact:**
The server will effectively process requests serially. Under load, this will lead to high latency and timeouts.

**Recommendation:**

- **Option A (Preferred):** Migrate to the asynchronous Firestore client (`google.cloud.firestore_v1.async_client`) and make all service/repository methods `async`.
- **Option B (Quick Fix):** Remove `async` from the route handlers (change `async def` to `def`). FastAPI will then run these endpoints in a thread pool, preventing the blocking of the main loop.

## 2. Database Scalability & Cost (Firestore)

**Severity: High**

### 2.1 Inefficient Counting

**Issue:** `BaseRepository._get_total_count` uses `len(list(query.stream()))`.
**Impact:** This fetches *every single document* matching the query just to count them.

- **Cost:** You are billed for N reads (where N is the total number of documents).
- **Performance:** Extremely slow for large collections.
**Recommendation:** Use Firestore's `count()` aggregation query: `query.count().get()[0][0].value`.

### 2.2 Dangerous Query Limits

**Issue:** `BaseRepository._apply_base_filters` sets a default limit of `1,000,000`.
**Impact:** This is effectively "no limit" but with a dangerous upper bound that could crash the application memory if hit.
**Recommendation:** Always enforce reasonable pagination limits (e.g., 50-100 items).

### 2.3 Document Size Limits (RSVP List)

**Issue:** RSVPs are stored in an array `rsvpList` within the Event document.
**Impact:** Firestore documents have a 1MB limit. If an event has thousands of attendees, the document will exceed this limit and writes will fail.
**Recommendation:** Move RSVPs to a subcollection `events/{eventId}/rsvps`. Keep only a summary (count, preview images) on the main document.

## 3. Error Handling & Reliability

**Severity: Medium**

**Issue:** Service layer methods swallow exceptions.

```python
def create_event(data: dict):
    try:
        return event_repo.create_event(data)
    except Exception as e:
        logger.error(...)
        return None
```

**Impact:**

- The API layer cannot distinguish between different error types (e.g., "Database unavailable" vs "Invalid data").
- It often returns generic 500 errors or 400 errors inappropriately.
**Recommendation:**
- Remove generic `try/except` blocks in services.
- Allow exceptions to propagate to the router.
- Use a global exception handler or specific `HTTPException` mapping in the router.

## 4. Security & Configuration

**Severity: Medium**

### 4.1 Secret Management

**Issue:** `app/config.py` writes secrets from Google Secret Manager to a local file `firebase_cred.json` at runtime.
**Impact:** Potential security risk if the container file system is compromised or if the file is not cleaned up.
**Recommendation:** Initialize the Firebase Admin SDK directly with the dictionary object retrieved from Secret Manager, avoiding the intermediate file write.

### 4.2 CORS Configuration

**Issue:** Origins are hardcoded in `app/main.py`.
**Recommendation:** Load allowed origins from environment variables.

## 5. Code Quality

**Severity: Low**

- **Type Hinting:** Inconsistent use of type hints.
- **Model Validation:** `EventCreateRequest` uses `str` for `startTime`. Using `datetime` would allow Pydantic to validate the format automatically.

## Summary of Action Plan

1. **Fix Blocking I/O:** Change route handlers to `def` (synchronous) as a temporary fix, or migrate to async Firestore.
2. **Optimize Firestore Counts:** Replace `len(list(query.stream()))` with `count()` queries.
3. **Refactor Error Handling:** Remove catch-all try/except blocks in services.
4. **Refactor RSVP Storage:** Plan migration to subcollections for RSVPs.
