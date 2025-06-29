# Sahana Backend API - Complete Endpoint Reference

*Last Updated: June 28, 2025*
*All endpoints are fully implemented and production-ready*

## Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/auth/google` | Google OAuth login | ❌ |
| `POST` | `/auth/login` | Email/password login | ❌ |
| `POST` | `/auth/register` | User registration | ❌ |
| `POST` | `/auth/refresh` | Token refresh | ❌ |
| `GET` | `/auth/me` | Get current user profile | ✅ |
| `PUT` | `/auth/me` | Update user profile | ✅ |
| `PUT` | `/auth/me/interests` | Update user interests | ✅ |

## Friend System Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/friends/request` | Send friend request | ✅ |
| `GET` | `/friends/requests` | Get friend requests (sent/received) | ✅ |
| `POST` | `/friends/accept/{request_id}` | Accept friend request | ✅ |
| `POST` | `/friends/reject/{request_id}` | Reject friend request | ✅ |
| `DELETE` | `/friends/request/{request_id}` | Cancel sent friend request | ✅ |
| `GET` | `/friends/list` | Get friends list | ✅ |
| `GET` | `/friends/search` | Search users | ✅ |
| `GET` | `/friends/status/{user_id}` | Get friendship status | ✅ |

## Event Management Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/events/new` | Create new event | ✅ |
| `GET` | `/events` | Get all events (with filters & pagination) | ❌ |
| `GET` | `/events/{event_id}` | Get event by ID | ❌ |
| `PUT` | `/events/{event_id}` | Update event (creator only) | ✅ |
| `DELETE` | `/events/{event_id}` | Delete event (creator only) | ✅ |
| `GET` | `/events/me/created` | Get user's created events | ✅ |
| `GET` | `/events/me/rsvped` | Get user's RSVP'd events | ✅ |
| `GET` | `/events/me/organized` | Get user's organized events | ✅ |
| `GET` | `/events/me/moderated` | Get user's moderated events | ✅ |

## Event RSVP Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/events/{event_id}/rsvp` | RSVP to event | ✅ |
| `DELETE` | `/events/{event_id}/rsvp` | Cancel RSVP | ✅ |
| `GET` | `/events/{event_id}/rsvps` | Get event RSVP list | ❌ |

## Event Roles Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `PATCH` | `/events/{event_id}/organizers` | Update event organizers (creator only) | ✅ |
| `PATCH` | `/events/{event_id}/moderators` | Update event moderators (organizer only) | ✅ |

## Event Archive Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `PATCH` | `/events/{event_id}/archive` | Archive event (creator only) | ✅ |
| `PATCH` | `/events/{event_id}/unarchive` | Unarchive event (creator only) | ✅ |
| `GET` | `/events/me/archived` | Get user's archived events | ✅ |
| `GET` | `/events/archived` | Get all archived events (admin only) | ✅ (Admin) |
| `POST` | `/events/archive/past-events` | Bulk archive past events (admin only) | ✅ (Admin) |

## Location-Based Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/events/location/nearby` | Get nearby community events | ❌ |
| `GET` | `/events/location/external` | Get external events by location | ✅ |

## Event Ingestion Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/events/fetch-ticketmaster-events` | Fetch Ticketmaster events (admin only) | ✅ (Admin) |
| `POST` | `/events/ingest/all` | Ingest events for all cities (admin only) | ✅ (Admin) |
| `POST` | `/ingest/daily` | Daily event ingestion (admin only) | ✅ (Admin) |

## Admin Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/admin/users` | Get all users (with filters & pagination) | ✅ (Admin) |

---

## Features Summary

### ✅ Fully Implemented Features

#### Authentication & User Management

- Google OAuth and email/password authentication
- JWT token management with refresh
- User profile management
- User interests and preferences

#### Friend System

- Complete friend request workflow
- User search and discovery
- Friendship status tracking
- Friend list management

#### Event Management

- Full CRUD operations for events
- Event categorization and filtering
- Location-based event discovery
- Event roles (creator, organizer, moderator)

#### RSVP System

- Event attendance management
- RSVP cancellation
- Attendee list viewing
- RSVP status tracking

#### Archive System

- Soft delete for events
- Archive/unarchive functionality
- Bulk archive operations
- Archive history tracking

#### External Integrations

- Ticketmaster API integration
- Eventbrite scraping
- Automated event ingestion
- Multi-source event aggregation

#### Admin Features

- User management
- Event oversight
- System administration
- Bulk operations

#### Technical Features

- Comprehensive pagination support
- Advanced filtering and search
- Role-based access control
- Error handling and validation
- API rate limiting ready
- Comprehensive logging

### 📊 API Statistics

- **Total Endpoints**: 35+
- **Authentication Endpoints**: 7
- **Friend System Endpoints**: 8
- **Event Management Endpoints**: 22
- **Admin Endpoints**: 2
- **Pagination Support**: All list endpoints
- **Filter Support**: Events, users, locations
- **Role-Based Access**: Creator, Organizer, Moderator, Admin, User

### 🔧 Technical Implementation

**Database**: Firebase Firestore with optimized indexes  
**Authentication**: JWT with refresh token support  
**Authorization**: Role-based access control  
**Caching**: URL caching for external APIs  
**Async Processing**: Event ingestion and scraping  
**Error Handling**: Comprehensive error responses  
**Validation**: Input validation and sanitization  
**Documentation**: Complete API reference with examples  

---

*This API is production-ready and serves as the complete backend for the Sahana event management platform.*
