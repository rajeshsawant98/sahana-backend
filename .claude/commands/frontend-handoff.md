You are generating a detailed frontend integration prompt for a frontend agent working on the Sahana app (React/TypeScript mobile or web client). The backend is a FastAPI + PostgreSQL + pgvector API deployed on Cloud Run.

The feature to document is: $ARGUMENTS

If no feature name is provided, infer it from recent git changes.

## Your task

1. Run `git diff HEAD~1 HEAD -- app/routes/ app/services/ app/models/ app/repositories/` to see what changed.
2. Read any new or modified route files to extract the exact endpoint signatures, query params, request bodies, and response shapes.
3. Read any new or modified model files (app/models/) for Pydantic schemas.
4. Read any relevant service files if they clarify behavior the frontend needs to know about.

Then produce a single, self-contained prompt the frontend agent can paste directly into their session. Structure it exactly like this:

---

## Frontend Integration: <Feature Name>

### What was built
<2–3 sentence plain-English summary of what the feature does and why it exists.>

### New / changed endpoints

For each endpoint, provide:

```
METHOD  /api/path
Auth:   Bearer token required (Firebase JWT)
```

**Query params** (if any):
| Param | Type | Required | Description |
|-------|------|----------|-------------|

**Request body** (if any):
```json
{
  "field": "type — description"
}
```

**Success response** `200`:
```json
{
  "field": "type — description"
}
```

**Error cases** the UI should handle:
- `400` — <when>
- `401` — unauthenticated
- `404` — <when, if applicable>
- `500` — server error (show generic retry message)

### Integration notes
- <Any ordering constraints, e.g. "call this before that">
- <Pagination: how cursors work if relevant>
- <Caching: are results cached? What triggers a stale result?>
- <UX hint: what should the loading/empty/error state look like based on the data shape>

### Fields to display
List every field in the response that the UI should render, with a short note on how to use it:
- `fieldName` (`type`) — <what to show, e.g. "display as a badge", "format as relative time", "show only if non-null">

### Types (TypeScript)
Provide ready-to-use TypeScript interfaces for the request and response shapes.

```typescript
// paste interfaces here
```

### Example fetch call
Provide a minimal, copy-paste-ready fetch/axios snippet showing exactly how to call the endpoint, including auth header and error handling pattern consistent with the existing codebase.

```typescript
// paste snippet here
```

---

Be precise. Include actual field names from the code, not placeholders. The frontend agent has no access to the backend repo.
