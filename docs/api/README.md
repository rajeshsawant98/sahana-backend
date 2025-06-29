# API Documentation Index

Welcome to the Sahana Backend API Documentation. This comprehensive guide covers all available endpoints, authentication methods, and integration examples.

## Quick Start

1. **[Complete Endpoints Summary](ENDPOINTS_SUMMARY.md)** - Full table of all 35+ API endpoints
2. **[Authentication Guide](authentication.md)** - Get started with user registration and JWT tokens
3. **[API Reference](API_DOCUMENTATION.md)** - Complete endpoint documentation with examples
4. **[Error Handling](errors.md)** - Error codes and troubleshooting
5. **[Examples](examples.md)** - Common use cases and code samples

## API Categories

### Core Features

- **[Authentication](API_DOCUMENTATION.md#authentication-endpoints)** - User registration, login, token management
- **[User Management](API_DOCUMENTATION.md#user-management)** - Profile management, user operations
- **[Event Management](API_DOCUMENTATION.md#event-management)** - Create, update, delete events
- **[Event RSVP](API_DOCUMENTATION.md#event-rsvp)** - Event attendance management
- **[Friend System](API_DOCUMENTATION.md#friend-system)** - Social features and friend relationships

### Advanced Features

- **[Event Roles](API_DOCUMENTATION.md#event-roles)** - Organizers and moderators
- **[Event Archive](API_DOCUMENTATION.md#event-archive)** - Soft delete and restore functionality
- **[Location-Based](API_DOCUMENTATION.md#location-based-events)** - Geographic event discovery
- **[Event Ingestion](API_DOCUMENTATION.md#event-ingestion)** - External event import

### Administration

- **[Admin Operations](API_DOCUMENTATION.md#admin-operations)** - System administration

## Implementation Status

🎉 **All API endpoints are fully implemented and production-ready!**

- ✅ **35+ endpoints** covering all major functionality
- ✅ **Complete RSVP system** with attendance management
- ✅ **Advanced friend system** with social features
- ✅ **Comprehensive pagination** on all list endpoints
- ✅ **Role-based access control** throughout
- ✅ **External API integrations** (Ticketmaster, Eventbrite)
- ✅ **Archive system** with soft delete functionality
- ✅ **Admin management** features

## Quick Reference

### Base URL

```
https://your-sahana-backend.com/api
```

### Authentication Header

```
Authorization: Bearer <your-jwt-token>
```

### Common Response Format

```json
{
  "data": { ... },
  "pagination": { ... },
  "message": "Success message"
}
```

## API Features

### 🔐 Security

- JWT-based authentication
- Role-based access control
- Rate limiting protection
- Input validation and sanitization

### 📊 Performance

- Pagination support on all list endpoints
- Efficient database indexing
- Caching for external integrations
- Async processing for bulk operations

### 🛠 Developer Experience

- Consistent REST API design
- Comprehensive error messages
- Detailed documentation with examples
- Postman collection available

## Integration Examples

### Frontend Integration

```javascript
// Example: Create an event
const response = await fetch('/api/events/new', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    eventName: 'Tech Meetup',
    location: { city: 'SF', state: 'CA' },
    startTime: '2025-07-15T18:00:00Z'
  })
});
```

### Mobile App Integration

```swift
// Example: RSVP to event
let url = URL(string: "https://api.sahana.com/events/\(eventId)/rsvp")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
```

## Support

### Documentation

- **API Reference**: Complete endpoint documentation
- **Guides**: Step-by-step integration guides
- **Examples**: Code samples in multiple languages
- **Troubleshooting**: Common issues and solutions

### Tools

- **Postman Collection**: Ready-to-use API collection
- **SDK**: Official SDKs for popular languages
- **Testing**: Sandbox environment for development

---

*For technical support, please refer to the troubleshooting guide or contact the development team.*
