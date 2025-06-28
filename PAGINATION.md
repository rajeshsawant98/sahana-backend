# API Pagination Documentation

This document describes the pagination features added to the Sahana Backend APIs.

## Overview

Pagination has been seamlessly integrated into existing endpoints using optional query parameters. When pagination parameters are provided, endpoints return structured paginated responses. Without pagination parameters, endpoints maintain their original behavior for backward compatibility.

## How It Works

**Pagination is optional and enabled by providing the `page` parameter:**

- **Without pagination**: `GET /api/events` → Returns legacy format `{"events": [...]}`
- **With pagination**: `GET /api/events?page=1` → Returns paginated format with metadata

## Pagination Parameters

To enable pagination on any supported endpoint, include:

- `page` (integer): Page number (1-based, minimum: 1) - **Required to enable pagination**
- `page_size` (integer): Number of items per page (minimum: 1, maximum: 100, default: 10)

## Response Formats

### Without Pagination (Legacy)
```json
{
  "events": [...],     // or "users": [...] 
  "count": 25          // optional count field
}
```

### With Pagination (New)
```json
{
  "items": [...],          // Array of data items
  "total_count": 150,      // Total number of items across all pages
  "page": 1,               // Current page number
  "page_size": 10,         // Items per page
  "total_pages": 15,       // Total number of pages
  "has_next": true,        // Whether there's a next page
  "has_previous": false    // Whether there's a previous page
}
```

## Available Endpoints with Pagination Support

All the endpoints below support optional pagination. Simply add `page=1` (or any page number) to enable pagination mode.

### Event Endpoints

#### 1. Get All Events
- **Endpoint**: `GET /api/events`
- **Authentication**: None required
- **Pagination**: Add `?page=1` to enable
- **Parameters**:
  - Standard pagination parameters (`page`, `page_size`)
  - **Filters**:
    - `city` (string): Filter by city
    - `state` (string): Filter by state  
    - `category` (string): Filter by category
    - `is_online` (boolean): Filter by online events
    - `creator_email` (string): Filter by creator email
    - `start_date` (string): Filter by start date (ISO format)
    - `end_date` (string): Filter by end date (ISO format)

**Examples**:
```bash
# Legacy mode (no pagination)
GET /api/events?city=Austin&state=Texas

# Pagination mode  
GET /api/events?page=1&page_size=20&city=Austin&state=Texas&is_online=false
```

#### 2. My Created Events
- **Endpoint**: `GET /api/events/me/created`
- **Authentication**: User login required
- **Pagination**: Add `?page=1` to enable

#### 3. My RSVP'd Events
- **Endpoint**: `GET /api/events/me/rsvped`
- **Authentication**: User login required
- **Pagination**: Add `?page=1` to enable

#### 4. My Organized Events
- **Endpoint**: `GET /api/events/me/organized`
- **Authentication**: User login required
- **Pagination**: Add `?page=1` to enable

#### 5. My Moderated Events
- **Endpoint**: `GET /api/events/me/moderated`
- **Authentication**: User login required
- **Pagination**: Add `?page=1` to enable

#### 6. External Events by Location
- **Endpoint**: `GET /api/events/location/external`
- **Authentication**: User login required
- **Pagination**: Add `?page=1` to enable
- **Required Parameters**: `city`, `state`

#### 7. Nearby Events by Location
- **Endpoint**: `GET /api/events/location/nearby`
- **Authentication**: None required
- **Pagination**: Add `?page=1` to enable
- **Required Parameters**: `city`, `state`

### Admin Endpoints

#### 8. Get All Users
- **Endpoint**: `GET /api/admin/users`
- **Authentication**: Admin access required
- **Pagination**: Add `?page=1` to enable
- **Filters**:
  - `role` (string): Filter by user role
  - `profession` (string): Filter by profession

## Usage Examples

### Basic Usage

```bash
# Legacy mode - no pagination
curl "http://localhost:8080/api/events"

# Pagination mode - add page parameter
curl "http://localhost:8080/api/events?page=1&page_size=10"

# Default page size (10) when only page is specified
curl "http://localhost:8080/api/events?page=2"
```

### With Filters

```bash
# Legacy mode with filters
curl "http://localhost:8080/api/events?city=Austin&state=Texas&is_online=true"

# Pagination mode with filters
curl "http://localhost:8080/api/events?page=1&page_size=10&city=Austin&state=Texas&is_online=true"

# Get events by specific creator (paginated)
curl "http://localhost:8080/api/events?page=1&creator_email=user@example.com"
```

### User-specific Events

```bash
# Legacy mode - user's created events (requires authentication)
curl -H "Authorization: Bearer <your-token>" \
  "http://localhost:8080/api/events/me/created"

# Pagination mode - user's created events
curl -H "Authorization: Bearer <your-token>" \
  "http://localhost:8080/api/events/me/created?page=1&page_size=20"
```

### Admin Operations

```bash
# Legacy mode - all users (requires admin authentication)
curl -H "Authorization: Bearer <admin-token>" \
  "http://localhost:8080/api/admin/users"

# Pagination mode - all users with admin role filter
curl -H "Authorization: Bearer <admin-token>" \
  "http://localhost:8080/api/admin/users?page=1&page_size=10&role=admin"
```

## Implementation Notes

1. **Performance**: Pagination uses database-level `offset` and `limit` for efficiency
2. **Sorting**: Results are ordered by creation time (most recent first) for events, and by email for users
3. **Error Handling**: Invalid pagination parameters return appropriate HTTP error codes
4. **Backward Compatibility**: Original non-paginated endpoints remain available
5. **Bug Fix (June 27, 2025)**: Fixed nearby events pagination endpoint that was incorrectly filtering by `origin="community"` while legacy endpoint had no origin filter. Both endpoints now return all events regardless of origin for consistency.

## Event Origin Types

Events in the system have an `origin` field that indicates their source:
- **external**: Events imported from external sources (Ticketmaster, etc.)
- **community**: Events created by users within the platform

### Endpoint Behavior by Origin:
- **Nearby Events** (`/api/events/location/nearby`): Returns **all events** regardless of origin
- **External Events** (`/api/events/location/external`): Returns **only external events** (`origin="external"`)

## Migration Strategy

You can gradually migrate from non-paginated to paginated endpoints:

1. **Phase 1**: Use both endpoints in parallel
2. **Phase 2**: Update frontend to use paginated endpoints
3. **Phase 3**: Optionally deprecate non-paginated endpoints (not required)

## Best Practices

1. **Page Size**: Use appropriate page sizes (10-50 items typically)
2. **Caching**: Consider caching frequently accessed pages
3. **Deep Pagination**: For very large datasets, consider cursor-based pagination in the future
4. **Error Handling**: Handle cases where requested page exceeds total pages

## Bug Fixes and Status Updates

### ✅ Nearby Events Pagination Bug (Fixed - June 27, 2025)

**Issue**: The `/api/events/location/nearby` endpoint with pagination parameters returned empty results while the legacy endpoint returned correct data.

**Root Cause**: The paginated version had an extra filter for `origin == "community"` events, while all events in the database have `origin == "external"`.

**Fix**: Removed the origin filter to match the legacy behavior. Both endpoints now return all nearby events regardless of origin.

**Validation**:

- ✅ Both legacy and paginated endpoints return identical data
- ✅ Regression test added (`test_nearby_events_bug_fix.py`)
- ✅ All pagination tests pass

## Future Enhancements

Potential future improvements:

- Cursor-based pagination for better performance on large datasets
- Search functionality combined with pagination
- Sorting options (by date, name, popularity, etc.)
- Advanced filtering with multiple values per filter
