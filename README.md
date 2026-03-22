# Sahana Backend

FastAPI backend for **Sahana** — a social meetup and event discovery platform. Handles authentication, event management, friend system, RSVP, and automated Ticketmaster event ingestion.

---

## Tech Stack

| Layer          | Technology                                            |
| -------------- | ----------------------------------------------------- |
| API            | FastAPI + Uvicorn                                     |
| Auth           | Firebase Authentication (email/password + Google SSO) |
| Database       | PostgreSQL (Neon serverless) + pgvector             |
| Cache          | Redis (Upstash)                                     |
| Ingestion      | Ticketmaster API                                    |
| Infrastructure | Docker, Cloud Run (us-west1), Cloud Scheduler       |
| CI/CD          | GitHub Actions                                      |

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
│   ├── models/             # Pydantic request/response models
│   ├── routes/             # API route handlers
│   ├── services/           # Business logic
│   ├── repositories/       # PostgreSQL data access (repository pattern)
│   │   ├── events/         # Specialized event repositories + facade
│   │   ├── friends/        # Friend system repositories
│   │   └── users/          # User repositories
│   ├── scrapers/           # Ticketmaster API client
│   ├── utils/              # redis_client, cache_utils, location_utils, etc.
│   ├── test/               # Tests
│   └── main.py             # App entrypoint + lifespan (Redis init)
├── .github/workflows/
│   └── deploy.yml          # Build → cleanup GCR → deploy to Cloud Run
├── cleanup_gcr.sh          # Manual GCR image cleanup script
├── Dockerfile
└── requirements.txt
```

---

## API Endpoints

### Auth

| Method | Path           | Description            |
| ------ | -------------- | ---------------------- |
| POST   | `/auth/login`  | Email/password login   |
| POST   | `/auth/google` | Google SSO login       |

### Events

| Method | Path                      | Description                   |
| ------ | ------------------------- | ----------------------------- |
| GET    | `/events/`                | All public events (cursor pagination) |
| POST   | `/events/new`             | Create event                  |
| GET    | `/events/{id}`            | Event detail                  |
| PATCH  | `/events/{id}/archive`    | Archive event                 |
| POST   | `/events/{id}/rsvp`       | RSVP                          |
| DELETE | `/events/{id}/rsvp`       | Cancel RSVP                   |
| GET    | `/events/me/created`      | My created events             |
| GET    | `/events/me/rsvped`       | My RSVP'd events              |
| GET    | `/events/location/nearby` | Events by city/state          |

### Friends

| Method | Path                      | Description             |
| ------ | ------------------------- | ----------------------- |
| POST   | `/friends/request`        | Send friend request     |
| GET    | `/friends/requests`       | Sent & received requests |
| POST   | `/friends/accept/{id}`    | Accept request          |
| POST   | `/friends/reject/{id}`    | Reject request          |
| DELETE | `/friends/request/{id}`   | Cancel sent request     |
| GET    | `/friends/list`           | Friends list            |
| GET    | `/friends/search`         | Search users            |
| GET    | `/friends/status/{user_id}` | Friendship status     |

### Ingestion (admin)

| Method | Path                        | Description                          |
| ------ | --------------------------- | ------------------------------------ |
| POST   | `/api/ingest/ticketmaster`  | Ingest TM events for all user cities |

---

## Event Ingestion

Cloud Scheduler runs `POST /api/ingest/ticketmaster` daily at **06:00 UTC**.

The ingestion pipeline:

1. Acquires a Redis mutex to prevent duplicate concurrent runs
2. Fetches Ticketmaster events per unique user city (Redis-cached 8 hrs)
3. Deduplicates via Redis SET (fast path) then `original_id` UNIQUE index in
   Postgres (fallback)
4. Saves new events to Postgres and invalidates the event query cache

Redis degrades gracefully — if unavailable, Postgres dedup still prevents duplicates.

---

## Redis Cache Keys

| Key                        | Type        | TTL     | Purpose                        |
| -------------------------- | ----------- | ------- | ------------------------------ |
| `sahana:ingestion:lock`    | STRING      | 1 hr    | Mutex for ingestion runs       |
| `sahana:tm:{city}:{state}` | STRING/JSON | 8 hrs   | TM API response cache          |
| `sahana:ingested_ids`      | SET         | 30 days | Event dedup by originalId      |
| `sahana:url_cache`         | SET         | 30 days | Scraped URL dedup              |
| `sahana:user_locations`    | STRING/JSON | 30 min  | Unique user city/state pairs   |
| `sahana:events:q:{hash}`   | STRING/JSON | 10 min  | Paginated event query cache    |

---

## Deployment

```bash
# Manual GCR cleanup (keep only latest image)
./cleanup_gcr.sh
```

CI/CD via GitHub Actions on push to `main`:

1. Build Docker image for `linux/amd64`
2. Push to `gcr.io/sahana-deaf0/sahana-backend`
3. Delete old GCR images (keep latest)
4. Deploy to Cloud Run (`us-west1`)

### Database Schema

See [`migrations/001_initial_schema.sql`](migrations/001_initial_schema.sql) for
the full PostgreSQL schema including indexes and triggers.

---

## Testing

```bash
pytest app/test/
```

---

## License

MIT
