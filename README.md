# Sahana Backend

The backend for **Sahana**, a comprehensive social meetup and event discovery platform. Built using **FastAPI**, connected to **Firebase** for authentication and Firestore as the primary database. This backend supports advanced features including event creation, social friend system, RSVP management, cursor-based pagination, automated event ingestion, user profiles, authentication, and location services.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **FastAPI**
- **Firebase Authentication** (Google SSO & email/password)
- **Firestore** (as NoSQL database)
- **Uvicorn** (ASGI server)
- **Docker** (containerized deployment)
- **GitHub Actions** (CI/CD)
- **Playwright** (web scraping for event ingestion)
- **External APIs** (Ticketmaster, Eventbrite)

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/sahana-backend.git
cd sahana-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Firebase

- Create a Firebase project
- Enable Firestore and Authentication (email/password + Google SSO)
- Download your Firebase admin SDK key and set it as an environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=path/to/firebase-adminsdk.json
```

**Important:** For cursor pagination to work properly, you'll need to create specific Firestore composite indexes. See [`docs/setup/URGENT_FIX_CURSOR_PAGINATION.md`](docs/setup/URGENT_FIX_CURSOR_PAGINATION.md) for immediate setup or [`docs/setup/FIRESTORE_INDEXES_CURSOR_PAGINATION.md`](docs/setup/FIRESTORE_INDEXES_CURSOR_PAGINATION.md) for comprehensive index documentation.

### 5. Create a `.env` file

```env
# JWT Auth Secrets
JWT_SECRET_KEY=<your_jwt_secret_key>
JWT_REFRESH_SECRET_KEY=<your_jwt_refresh_secret_key>

# Google APIs
GOOGLE_CLIENT_ID=<your_google_client_id>
GOOGLE_MAPS_API_KEY=<your_google_maps_api_key>
TICKETMASTER_API_KEY=<your_ticketmaster_api_key>

# Local testing
GOOGLE_APPLICATION_CREDENTIALS=firebase_cred.json

# Cloud Run settings
FIREBASE_CRED_SECRET=firebase_cred
FIREBASE_CRED_PATH=/tmp/firebase_cred.json
```

> ⚠️ **Never commit your `.env` or Firebase credentials to source control.**

### 6. Run the development server

```bash
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

---

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) folder:

- **[API Guide](docs/api/overview.md)** - Complete API reference and examples
- **[Quick Start](docs/setup/quick-start.md)** - Get up and running quickly
- **[Authentication](docs/api/authentication.md)** - Auth system documentation
- **[Events API](docs/api/events.md)** - Event management endpoints
- **[Friends System](docs/api/FRIENDS_README.md)** - Complete friend system guide
- **[RSVP System](docs/api/rsvp.md)** - RSVP functionality
- **[Pagination](docs/api/pagination.md)** - Cursor-based pagination guide
- **[Docker Deployment](docs/deployment/docker.md)** - Containerized deployment

For interactive API exploration, visit: `http://localhost:8000/docs`

---

## 🏗️ Architecture

Sahana Backend follows **Clean Architecture** principles with a well-designed separation of concerns:

### Repository Pattern Implementation

The data access layer uses a **specialized repository pattern** for optimal maintainability:

- **BaseRepository**: Common functionality and modular query filters
- **EventCrudRepository**: Basic CRUD operations  
- **EventQueryRepository**: Complex queries and filtering
- **EventArchiveRepository**: Archive management operations
- **EventRsvpRepository**: RSVP-specific operations
- **EventUserRepository**: User-specific event queries
- **EventRepositoryManager**: Facade providing unified interface

### Friend System Architecture

- **FriendRequestService**: Friend request management
- **FriendManagementService**: Existing friendship operations
- **UserDiscoveryService**: User search and discovery
- **FriendService**: Unified facade for all friend operations

### Layer Architecture

```text
Routes (Controllers) → Services (Business Logic) → Repositories (Data Access) → Database
```

**Key Benefits:**

- ✅ **Maintainable**: Small, focused classes with single responsibilities
- ✅ **Testable**: Each layer can be unit tested independently  
- ✅ **Scalable**: Easy to extend with new features
- ✅ **SOLID Compliant**: Follows all SOLID principles

**Architecture Documentation:**

- **[Repository Architecture Guide](docs/architecture/event-repository-architecture.md)** - Detailed implementation guide
- **[Architecture Overview](docs/architecture/README.md)** - Complete architecture documentation
- **[Work History](docs/WORK_LOG.md)** - Development history and decisions

---

## 📦 Project Structure

```text
sahana-backend/
├── .github/workflows/
│   └── deploy.yml              # CI/CD GitHub Actions workflow
├── app/
│   ├── auth/                   # Authentication (Google SSO, JWT, roles)
│   ├── models/                 # Pydantic models for request/response
│   ├── routes/                 # API routes (auth, events, friends, etc.)
│   ├── services/               # Business logic layer
│   │   ├── friend_service.py           # Unified friend system facade
│   │   ├── friend_request_service.py   # Friend request management
│   │   ├── friend_management_service.py # Friend list & status management
│   │   ├── user_discovery_service.py   # User search functionality
│   │   ├── event_service.py            # Event business logic
│   │   └── user_service.py             # User management
│   ├── repositories/           # Data access layer (Repository pattern)
│   │   ├── events/             # Event-related repositories
│   │   ├── friends/            # Friend system repositories
│   │   └── users/              # User repositories
│   ├── scrapers/               # Web scraping for external events
│   ├── utils/                  # Utility functions and helpers
│   ├── test/                   # Unit/integration tests
│   ├── config.py               # Environment configuration
│   └── main.py                 # FastAPI app entrypoint
├── docs/                       # Comprehensive documentation
│   ├── api/                    # API documentation
│   ├── architecture/           # Architecture guides
│   ├── deployment/             # Deployment guides
│   ├── frontend/               # Frontend integration guides
│   └── setup/                  # Setup and configuration
├── Dockerfile                  # Docker container setup
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 📌 Key Features Implemented

### ✅ User Management

- Signup, login (Google/email)
- Profile update (name, bio, contact info, location)
- User discovery and search functionality

### ✅ Event Management

- Create/update events (online/offline, time, location)
- Advanced cursor-based pagination for optimal performance
- Event archiving and soft-delete functionality
- Automated event ingestion from external sources (Ticketmaster, Eventbrite)
- Event roles: creator, organizer, moderator support

### ✅ Friend System 🤝

- **Send Friend Requests** - Search and send requests to other users
- **Accept/Reject Requests** - Manage incoming friend requests
- **Cancel Sent Requests** - Cancel outgoing pending requests
- **Friends List** - View all current friends with rich profiles
- **User Search** - Find users with real-time friendship status
- **Smart Search Integration** - Enhanced event discovery with friend networks
- **Friendship Status Tracking** - Real-time status between any two users

### ✅ RSVP System

- Join an event (adds to rsvpList)
- Cancel RSVP (removes user from list)
- Fetch RSVP'd events for user
- Enhanced RSVP management with friend visibility
- RSVP statistics and analytics

### ✅ Event Discovery

- Filter by category, location, date ranges
- Cursor-based pagination for large datasets
- See event metadata (time, tags, RSVP status)
- Nearby events discovery
- External events integration
- Friend-based event recommendations

### ✅ Location Services

- Auto-detect or manually set user location
- Event cards and detail pages use this for relevance
- Location-based event recommendations
- Multi-city event ingestion support

### ✅ Advanced Pagination

- **Cursor-based pagination** for high-performance data access
- **Legacy offset-based pagination** for backward compatibility
- Intelligent filtering with automatic index selection
- Real-time safe pagination that handles concurrent modifications

### ✅ Event Ingestion & External APIs

- **Ticketmaster Integration** - Automated event fetching and ingestion
- **Eventbrite Integration** - Async web scraping for event data
- **Daily Automated Ingestion** - Background event updates
- **Multi-source Event Aggregation** - Unified event discovery
- **Deduplication & Caching** - Efficient URL caching and event deduplication

---

## 📬 API Endpoints (Selected)

### Authentication

- `POST /auth/login` — login with email/password
- `POST /auth/google` — login via Google SSO

### Events

- `GET /events/` — get all public events (cursor pagination)
- `POST /events/new` — create a new event
- `GET /events/{id}` — get event detail by ID
- `POST /events/{id}/rsvp` — RSVP to an event
- `DELETE /events/{id}/rsvp` — cancel RSVP
- `GET /events/me/created` — events created by user
- `GET /events/me/rsvped` — events the user RSVP'd to
- `GET /events/me/organized` — events organized by user
- `GET /events/me/moderated` — events moderated by user
- `PATCH /events/{id}/archive` — archive an event (soft delete)

### Location-Based Events

- `GET /events/location/nearby` — nearby events by city/state
- `GET /events/location/external` — external events (Ticketmaster/Eventbrite)

### Friend System 🤝

- `POST /friends/request` — send friend request
- `GET /friends/requests` — get friend requests (sent & received)
- `POST /friends/accept/{id}` — accept friend request
- `POST /friends/reject/{id}` — reject friend request
- `DELETE /friends/request/{id}` — cancel sent friend request
- `GET /friends/list` — get friends list
- `GET /friends/search` — search users to befriend
- `GET /friends/status/{user_id}` — get friendship status

### Admin & Ingestion

- `POST /events/fetch-ticketmaster-events` — fetch Ticketmaster events (admin)
- `POST /events/ingest/all` — ingest events for all cities (admin)
- `GET /admin/users` — get all users (admin)

---

## 🐳 Docker Support

### Build and run with Docker

```bash
docker build -t sahana-backend .
docker run -p 8000:8000 --env-file .env sahana-backend
```

Make sure to mount or copy your `firebase_cred.json` if needed.

---

## 🚀 CI/CD with GitHub Actions

- The `.github/workflows/deploy.yml` file defines the deployment pipeline.
- You can extend this to auto-deploy to GCP, Firebase Hosting, or Render.

---

## 🧪 Testing

Tests are located in the `app/test/` directory:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Full API endpoint testing  
- **Friend System Tests**: Comprehensive friend functionality testing
- **Pagination Tests**: Cursor pagination validation

Run tests using:

```bash
pytest app/test/
```

---

## 📊 Recent Major Updates

### Friend System Implementation (July 2025)

- Complete social networking functionality
- Real-time friendship status tracking
- User search and discovery
- Integration with event system

### Advanced Pagination System (June 2025)

- Cursor-based pagination for high performance
- Backward compatibility with offset pagination
- Optimized Firestore queries with proper indexing

### Event Ingestion Pipeline (June 2025)

- Automated Ticketmaster API integration
- Async Eventbrite web scraping
- Multi-source event aggregation
- Daily automated ingestion workflows

### Repository Architecture Refactoring (June 2025)

- Modular repository pattern implementation
- Specialized repositories for different concerns
- Improved maintainability and testability

---

## ✨ Upcoming Features

### Phase 1: Enhanced Social Features

- Real-time notifications for friend requests
- Mutual friends display and discovery
- Friend activity feeds
- Event attendance by friends visibility

### Phase 2: Advanced Event Features

- Event categories and tagging system
- Advanced filtering and search
- Event recommendations based on interests
- Event series and recurring events

### Phase 3: Platform Enhancements

- WebSocket integration for real-time updates
- Mobile push notifications
- Analytics dashboard
- Event promotion tools

---

## 📞 Support & Contributing

- **Documentation**: See [`docs/`](docs/) for detailed guides
- **Issues**: Report bugs via GitHub Issues
- **API Testing**: Use the interactive docs at `/docs`
- **Architecture**: Review the [Architecture Guide](docs/architecture/README.md)
- **Friend System**: See [Friend System Documentation](docs/api/FRIENDS_README.md)

---

## 📄 License

MIT License
