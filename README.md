# Sahana Backend

The backend for **Sahana**, a social meetup and event discovery platform. Built using **FastAPI**, connected to **Firebase** for authentication and Firestore as the primary database. This backend supports features such as event creation, RSVP system, user profiles, authentication, and location services.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **FastAPI**
- **Firebase Authentication** (Google SSO & email/password)
- **Firestore** (as NoSQL database)
- **Uvicorn** (ASGI server)
- **Docker** (containerized deployment)
- **GitHub Actions** (CI/CD)

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
- **[RSVP System](docs/api/rsvp.md)** - RSVP functionality
- **[Pagination](docs/api/pagination.md)** - Pagination usage guide
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

### Layer Architecture

```
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

```
sahana-backend/
├── .github/workflows/
│   └── deploy.yml              # CI/CD GitHub Actions workflow
├── app/
│   ├── auth/                   # Google SSO, JWT, login utilities
│   ├── db/                     # Firestore access layer
│   ├── models/                 # Pydantic models for request/response
│   ├── routes/                 # API routes: auth, events, rsvp, etc.
│   ├── services/               # Business logic (e.g. RSVP handlers)
│   ├── repositories/           # Firestore data access layer (Repository pattern)
│   ├── utils/                  # Utility functions and helpers
│   ├── test/                   # Unit/integration tests
│   ├── __init__.py
│   ├── config.py               # Env config handling
│   ├── db.py                   # Firebase client / DB init
│   └── main.py                 # FastAPI app entrypoint
├── .env                        # Environment variables
├── .gitignore
├── Dockerfile                  # Docker container setup
├── firebase_cred.json          # Firebase admin SDK credentials
├── README.md                   # Project documentation
└── requirements.txt            # Python dependencies
```

---

## 📦 Dependencies (requirements.txt)

### Web & API

- `fastapi`
- `uvicorn`
- `pydantic`
- `requests`
- `beautifulsoup4`

### Authentication & Security

- `authlib`
- `google-auth`
- `python-jose`
- `passlib`
- `bcrypt`

### Firebase & Cloud

- `firebase-admin`
- `google-cloud-secret-manager`

### Configuration & Storage

- `python-dotenv`
- `sqlalchemy`
- `databases`

### AI Integration (Optional)

- `openai`

---

## 🔐 Authentication

- Supports **Google SSO** and **email/password** login
- JWT token-based authentication
- Access token stored in Redux, refresh token stored in HttpOnly cookie or localStorage

---

## 📌 Key Features Implemented

### ✅ User Management

- Signup, login (Google/email)
- Profile update (name, bio, contact info, location)

### ✅ Event Management

- Create/update events (online/offline, time, location)
- Firestore stores each event document

### ✅ RSVP System

- Join an event (adds to rsvpList)
- Cancel RSVP (removes user from list)
- Fetch RSVP’d events for user

### ✅ Event Discovery

- Filter by category, location
- See event metadata (time, tags, RSVP status)

### ✅ Location Services

- Auto-detect or manually set user location
- Event cards and detail pages use this for relevance

### ✅ Event Detail API

- Full event detail by ID
- RSVP status included for logged-in user

---

## 📬 API Endpoints (Selected)

- `POST /auth/login` — login with email/password
- `POST /auth/google` — login via Google SSO
- `GET /events/` — get all public events
- `POST /events/{id}/rsvp` — RSVP to an event
- `DELETE /events/{id}/rsvp` — Cancel RSVP
- `GET /events/me/rsvped` — Events the user RSVP’d to
- `GET /events/me/created` — Events created by user
- `GET /events/{id}` — Get event detail by ID

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

Tests are located in the `app/test/` directory.
Run them using `pytest` (support coming soon).

---

## ✨ Upcoming Features

- Role-based permissions (event creator vs attendee)
- Real-time RSVP count updates
- Notification system (email reminders, RSVP updates)
- Attendee visibility and profiles

---

## 📄 License

MIT License
