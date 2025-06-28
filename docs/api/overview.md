# Sahana API Guide

This guide provides comprehensive documentation for the Sahana Backend API. The API is built with FastAPI and provides endpoints for user authentication, event management, RSVP functionality, and more.

## 🌐 Base Information

- **Base URL**: `http://localhost:8000` (development)
- **API Version**: v1
- **Protocol**: HTTPS (production) / HTTP (development)
- **Content-Type**: `application/json`
- **Interactive Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 🔐 Authentication

The Sahana API uses **JWT (JSON Web Token)** based authentication with support for:

- Google SSO
- Email/Password authentication

### Authentication Headers

Include the JWT token in the Authorization header for protected endpoints:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | Login with email/password |
| `POST` | `/auth/google` | Login via Google SSO |
| `POST` | `/auth/signup` | Create new user account |
| `POST` | `/auth/refresh` | Refresh JWT token |
| `POST` | `/auth/logout` | Logout and invalidate token |

## 📋 Core API Endpoints

### 👤 User Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/users/me` | Get current user profile | ✅ |
| `PUT` | `/users/me` | Update user profile | ✅ |
| `GET` | `/users/{user_id}` | Get user by ID | ❌ |

### 🎉 Event Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/events/` | Get all events (with filters) | ❌ |
| `POST` | `/events/` | Create new event | ✅ |
| `GET` | `/events/{event_id}` | Get event details | ❌ |
| `PUT` | `/events/{event_id}` | Update event | ✅ |
| `DELETE` | `/events/{event_id}` | Delete event | ✅ |
| `GET` | `/events/me/created` | Get events created by user | ✅ |
| `GET` | `/events/me/rsvped` | Get events user RSVP'd to | ✅ |

### 🎟️ RSVP Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/events/{event_id}/rsvp` | RSVP to an event | ✅ |
| `DELETE` | `/events/{event_id}/rsvp` | Cancel RSVP | ✅ |
| `GET` | `/events/{event_id}/rsvps` | Get event RSVPs | ❌ |

### 🔧 Administrative

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/admin/users` | Get all users | ✅ (Admin) |
| `GET` | `/admin/events` | Get all events | ✅ (Admin) |

## 🔍 Query Parameters

### Event Filtering

The `/events/` endpoint supports various filters:

```
GET /events/?category=technology&location=San Francisco&page=1&page_size=10
```

**Available Filters:**

- `category` (string): Filter by event category
- `location` (string): Filter by event location
- `date_from` (ISO date): Events starting from this date
- `date_to` (ISO date): Events ending before this date
- `online` (boolean): Filter online events only
- `search` (string): Search in event title and description

### Pagination Parameters

All list endpoints support optional pagination:

- `page` (integer): Page number (1-based, enables pagination)
- `page_size` (integer): Items per page (1-100, default: 10)

## 📝 Request/Response Examples

### Authentication

#### Login Request

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Login Response

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "dGhpc2lzYXJlZnJlc2h0b2tlbg...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "name": "John Doe",
    "profile_picture": "https://..."
  }
}
```

### Event Creation

#### Create Event Request

```http
POST /events/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "title": "Tech Meetup 2025",
  "description": "Join us for an exciting tech meetup!",
  "category": "technology",
  "date_time": "2025-07-15T18:00:00Z",
  "location": {
    "address": "123 Tech Street, San Francisco, CA",
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "is_online": false,
  "max_attendees": 50,
  "tags": ["technology", "networking", "startup"]
}
```

#### Create Event Response

```json
{
  "id": "event_123",
  "title": "Tech Meetup 2025",
  "description": "Join us for an exciting tech meetup!",
  "category": "technology",
  "date_time": "2025-07-15T18:00:00Z",
  "location": {
    "address": "123 Tech Street, San Francisco, CA",
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "is_online": false,
  "max_attendees": 50,
  "current_attendees": 1,
  "tags": ["technology", "networking", "startup"],
  "created_by": "user123",
  "created_at": "2025-06-28T10:00:00Z",
  "updated_at": "2025-06-28T10:00:00Z",
  "rsvp_status": "going"
}
```

### Event Listing with Pagination

#### Request

```http
GET /events/?page=1&page_size=5&category=technology
```

#### Response

```json
{
  "items": [
    {
      "id": "event_123",
      "title": "Tech Meetup 2025",
      "category": "technology",
      "date_time": "2025-07-15T18:00:00Z",
      "location": {
        "address": "123 Tech Street, San Francisco, CA",
        "latitude": 37.7749,
        "longitude": -122.4194
      },
      "current_attendees": 15,
      "max_attendees": 50,
      "rsvp_status": null
    }
  ],
  "total_count": 25,
  "page": 1,
  "page_size": 5,
  "total_pages": 5,
  "has_next": true,
  "has_previous": false
}
```

## ⚠️ Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-06-28T10:00:00Z"
}
```

### Common Status Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Success |
| `201` | Created successfully |
| `400` | Bad request - invalid parameters |
| `401` | Unauthorized - invalid or missing token |
| `403` | Forbidden - insufficient permissions |
| `404` | Not found - resource doesn't exist |
| `409` | Conflict - resource already exists |
| `422` | Validation error - invalid data format |
| `500` | Internal server error |

### Error Examples

#### 401 Unauthorized

```json
{
  "detail": "Invalid authentication credentials",
  "error_code": "INVALID_TOKEN"
}
```

#### 404 Not Found

```json
{
  "detail": "Event not found",
  "error_code": "EVENT_NOT_FOUND"
}
```

#### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 🚀 Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Authenticated users**: 1000 requests per hour
- **Unauthenticated users**: 100 requests per hour

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 🧪 Testing the API

### Using curl

```bash
# Get all events
curl -X GET "http://localhost:8000/events/"

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Create event (with auth token)
curl -X POST "http://localhost:8000/events/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Event", "description": "Test", "date_time": "2025-07-15T18:00:00Z"}'
```

### Using Python requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# Login
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "user@example.com",
    "password": "password123"
})
token = login_response.json()["access_token"]

# Get events with authentication
headers = {"Authorization": f"Bearer {token}"}
events_response = requests.get(f"{BASE_URL}/events/", headers=headers)
```

## 📱 SDK and Client Libraries

Consider using these tools for easier API integration:

- **JavaScript/TypeScript**: Use `fetch` or `axios`
- **Python**: Use `requests` or `httpx`
- **Mobile Apps**: Platform-specific HTTP clients
- **Swagger Codegen**: Generate client libraries from OpenAPI spec

## 🔗 Related Documentation

- [Authentication Details](authentication.md)
- [Event Management](events.md)
- [RSVP System](rsvp.md)
- [Pagination Guide](pagination.md)
- [Error Codes Reference](errors.md)

---

*For interactive API testing, visit: [http://localhost:8000/docs](http://localhost:8000/docs)*
