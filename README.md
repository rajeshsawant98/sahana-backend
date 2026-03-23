# Sahana Backend

FastAPI backend for **Sahana** — a social event discovery and people-matching platform. Handles authentication, event management, friend system, RSVP, AI-powered semantic search, friend recommendations, and automated event ingestion.

---

## Tech Stack

| Layer          | Technology                                            |
| -------------- | ----------------------------------------------------- |
| API            | FastAPI + Uvicorn                                     |
| Auth           | Firebase Authentication (email/password + Google SSO) |
| Database       | PostgreSQL (Neon serverless) + pgvector               |
| AI             | OpenAI `text-embedding-3-small` (1536-dim embeddings) |
| Cache          | Redis (Upstash)                                       |
| Ingestion      | Ticketmaster API                                      |
| Infrastructure | Docker, Cloud Run (us-west1), Cloud Scheduler         |
| CI/CD          | GitHub Actions                                        |

---

## Local Setup

```bash
# 1. Clone and create virtualenv
git clone https://github.com/your-username/sahana-backend.git
cd sahana-backend
python -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env  # then fill in values

# 4. Run
uvicorn app.main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### `.env` variables

```env
JWT_SECRET_KEY=
JWT_REFRESH_SECRET_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_MAPS_API_KEY=
TICKETMASTER_API_KEY=
OPENAI_API_KEY=
REDIS_URL=rediss://default:<token>@<host>.upstash.io:6379
DATABASE_URL=postgresql://neondb_owner:<password>@<host>.neon.tech/neondb?sslmode=require

# Firebase Auth (JWT verification only)
GOOGLE_APPLICATION_CREDENTIALS=firebase_cred.json

# Cloud Run Firebase (via Secret Manager)
FIREBASE_CRED_SECRET=firebase_cred
FIREBASE_CRED_PATH=/tmp/firebase_cred.json
```

> Never commit `.env` or Firebase credentials.

---

## Project Structure

```text
sahana-backend/
├── app/
│   ├── auth/               # JWT + Firebase auth middleware
│   ├── db/                 # SQLAlchemy async session factory
│   ├── models/             # Pydantic request/response models
│   ├── routes/             # API route handlers
│   ├── services/           # Business logic + AI services
│   │   ├── embedding_service.py      # OpenAI embedding generation (users + events + queries)
│   │   ├── search_service.py         # NL event search (LLM parse + pgvector)
│   │   ├── friend_recommendation_service.py  # Semantic people matching
│   │   └── ...
│   ├── repositories/       # PostgreSQL data access (repository pattern)
│   │   ├── events/         # Specialized event repositories + facade
│   │   ├── friends/        # Friend system repositories
│   │   └── users/          # User repositories
│   ├── scrapers/           # Ticketmaster API client
│   ├── utils/              # redis_client, cache_utils, location_utils, etc.
│   └── main.py             # App entrypoint + lifespan (Redis init)
├── migrations/
│   ├── 001_initial_schema.sql        # Full PostgreSQL schema
│   ├── 002_add_vibe_description.sql  # users.vibe_description
│   ├── 003_query_optimizations.sql   # GIN indexes, search_vector trigger
│   └── 004_trigram_user_search.sql   # pg_trgm indexes for user search
├── scripts/
│   ├── backfill_user_embeddings.py   # One-time user embedding backfill
│   └── backfill_event_embeddings.py  # One-time event embedding backfill
├── .github/workflows/
│   └── deploy.yml          # Build → cleanup GCR → deploy to Cloud Run
├── Dockerfile
└── requirements.txt
```

---

## API Endpoints

### Auth

| Method | Path                  | Description              |
| ------ | --------------------- | ------------------------ |
| POST   | `/api/auth/login`     | Email/password login     |
| POST   | `/api/auth/google`    | Google SSO login         |
| POST   | `/api/auth/register`  | Register new user        |
| POST   | `/api/auth/refresh`   | Refresh access token     |
| GET    | `/api/auth/me`        | Get own profile          |
| PUT    | `/api/auth/me`        | Update profile           |

### Events

| Method | Path                              | Description                                    |
| ------ | --------------------------------- | ---------------------------------------------- |
| GET    | `/api/events`                     | All public events (cursor pagination)          |
| GET    | `/api/events/search?q=`           | Natural language search (pgvector + LLM)       |
| GET    | `/api/events/nearby`              | Events by city/state (cursor pagination)       |
| POST   | `/api/events/new`                 | Create event                                   |
| GET    | `/api/events/{id}`                | Event detail                                   |
| PUT    | `/api/events/{id}`                | Update event                                   |
| DELETE | `/api/events/{id}`                | Delete event                                   |
| PATCH  | `/api/events/{id}/archive`        | Archive event                                  |
| PATCH  | `/api/events/{id}/unarchive`      | Unarchive event                                |
| POST   | `/api/events/{id}/rsvp`           | RSVP to event                                  |
| DELETE | `/api/events/{id}/rsvp`           | Cancel RSVP                                    |
| PATCH  | `/api/events/{id}/rsvp`           | Update RSVP status                             |
| GET    | `/api/events/{id}/rsvps`          | Event RSVP list                                |
| GET    | `/api/events/me/created`          | My created events                              |
| GET    | `/api/events/me/rsvped`           | My RSVP'd events                               |
| GET    | `/api/events/me/organized`        | Events I'm organizing                          |
| GET    | `/api/events/me/moderated`        | Events I'm moderating                          |
| GET    | `/api/events/me/interested`       | Events I'm interested in                       |

### Friends

| Method | Path                        | Description                          |
| ------ | --------------------------- | ------------------------------------ |
| POST   | `/api/friends/request`      | Send friend request                  |
| GET    | `/api/friends/requests`     | Sent & received requests             |
| POST   | `/api/friends/accept/{id}`  | Accept request                       |
| POST   | `/api/friends/reject/{id}`  | Reject request                       |
| DELETE | `/api/friends/request/{id}` | Cancel sent request                  |
| GET    | `/api/friends/list`         | Friends list                         |
| GET    | `/api/friends/search`       | Search users                         |
| GET    | `/api/friends/recommendations` | AI-powered people recommendations |
| GET    | `/api/friends/status/{id}`  | Friendship status                    |

### Admin

| Method | Path                | Description                                  |
| ------ | ------------------- | -------------------------------------------- |
| GET    | `/api/admin/stats`  | Platform stats (users, events, active/archived) |
| GET    | `/api/admin/users`  | All users (paginated)                        |

### Ingestion

| Method | Path                    | Description                          |
| ------ | ----------------------- | ------------------------------------ |
| POST   | `/api/ingest/ticketmaster` | Ingest TM events for all user cities |

---

## AI Features

### Natural Language Event Search

`GET /api/events/search?q=rock+concerts+in+tempe`

Two-phase pipeline:

1. **LLM parsing** — GPT-4o-mini extracts structured intent: `{city, state, category, keywords, is_online, start_date, end_date}`
2. **Semantic search** — enriched query embedded via `text-embedding-3-small`, compared against event embeddings using pgvector cosine similarity. Hard filters (city, state, date) applied as SQL WHERE clauses. Results ordered by relevance.

Falls back to Phase 1 tsvector SQL search if embeddings unavailable. Supports offset-based cursor pagination (semantic cursors are distinct from regular keyset cursors). Embeddings cached in Redis (1 hr) so paginated requests skip the OpenAI call.

### People Recommendations

`GET /api/friends/recommendations`

Uses pgvector ANN search on `users.embedding` (1536-dim). User embeddings are built from name + profession + bio + interests + `vibe_description`. Falls back to rule-based scoring (shared interests + city + event overlap) when no embedding exists.

Profile field: `vibe_description` — users describe the kind of people they want to meet. Included in the embedding to drive semantic matching.

---

## Event Ingestion

Cloud Scheduler triggers `POST /api/ingest/ticketmaster` daily at **06:00 UTC**.

Pipeline:
1. Acquires a Redis mutex to prevent duplicate concurrent runs
2. Fetches Ticketmaster events per unique user city (Redis-cached 8 hrs)
3. Deduplicates via `original_id` UNIQUE index (batch insert with per-row fallback)
4. New events get embeddings generated as a background task

---

## Redis Cache Keys

| Key                          | TTL     | Purpose                              |
| ---------------------------- | ------- | ------------------------------------ |
| `sahana:ingestion:lock`      | 1 hr    | Mutex for ingestion runs             |
| `sahana:tm:{city}:{state}`   | 8 hrs   | Ticketmaster API response cache      |
| `sahana:ingested_ids`        | 30 days | Event dedup by originalId            |
| `sahana:url_cache`           | 30 days | Scraped URL dedup                    |
| `sahana:user_locations`      | 30 min  | Unique user city/state pairs         |
| `sahana:events:q:{hash}`     | 10 min  | Paginated event query cache          |
| `sahana:search:{hash}`       | 10 min  | NL search result cache (first page)  |
| `sahana:emb:{hash}`          | 1 hr    | Query embedding cache                |

---

## Database

PostgreSQL on Neon (serverless). pgvector enabled for embedding storage and ANN search.

Key schema features:
- `users.embedding vector(1536)` — semantic people matching
- `events.embedding vector(1536)` — semantic event search
- `events.search_vector tsvector` — full-text search via trigger
- GIN indexes on `categories[]`, `search_vector`, and trigram indexes on `users.name`/`email`
- Cursor pagination on `(start_time ASC, event_id ASC)`

See [`migrations/`](migrations/) for full schema and indexes.

---

## Deployment

CI/CD via GitHub Actions on push to `main`:

1. Build Docker image for `linux/amd64`
2. Push to `gcr.io/sahana-deaf0/sahana-backend`
3. Delete old GCR images (keep latest)
4. Deploy to Cloud Run (`us-west1`)

---

## Testing

```bash
pytest app/test/
```

---

## License

MIT
