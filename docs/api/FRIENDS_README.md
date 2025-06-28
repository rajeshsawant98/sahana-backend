# Sahana Friends System 🤝

A complete friend request and social networking system for the Sahana event platform.

## 🚀 Quick Start

### Backend Setup
The friends system backend is already integrated into the Sahana FastAPI application. The system includes:

- **8 REST API endpoints** for complete friend functionality
- **Firestore database integration** for scalable data storage
- **JWT authentication** with role-based access control
- **Comprehensive error handling** and validation

### Frontend Setup
Follow the [Frontend Implementation Guide](./docs/frontend/friends-implementation-guide.md) to integrate the React components.

## 📚 Documentation

### API Documentation
- **[Friends API Reference](./docs/api/friends.md)** - Complete API documentation with examples
- **[Users API Updates](./docs/api/users.md)** - Updated user API documentation with friends integration

### Frontend Documentation  
- **[Frontend Implementation Guide](./docs/frontend/friends-implementation-guide.md)** - Comprehensive React + TypeScript implementation

## 🏗️ Architecture Overview

### Backend Architecture
```
app/
├── models/friend.py              # Pydantic models for friends system
├── repositories/friend_repository.py  # Database operations with Firestore
├── services/friend_service.py    # Business logic layer
└── routes/friend_routes.py       # FastAPI REST endpoints
```

### Database Design
- **Collection**: `friend_requests` - Stores all friend relationships
- **Collection**: `users` - Referenced for user profiles
- **Approach**: Single record per relationship, bidirectional friendship logic

### Key Features Implemented

✅ **Send Friend Request** - Search and send requests to other users  
✅ **Accept/Reject Requests** - Manage incoming friend requests  
✅ **Cancel Sent Requests** - Cancel outgoing pending requests  
✅ **Friends List** - View all current friends with rich profiles  
✅ **User Search** - Find users with real-time friendship status  
✅ **Cache Management** - Efficient invalidation strategy  

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/friends/request` | Send friend request |
| `GET` | `/api/friends/requests` | Get all friend requests |
| `POST` | `/api/friends/accept/{id}` | Accept friend request |
| `POST` | `/api/friends/reject/{id}` | Reject friend request |
| `DELETE` | `/api/friends/request/{id}` | Cancel friend request |
| `GET` | `/api/friends/list` | Get friends list |
| `GET` | `/api/friends/search` | Search users |
| `GET` | `/api/friends/status/{user_id}` | Get friendship status |

## 🧪 Testing

### Backend Tests
```bash
# Run friend system tests
cd /Users/rajesh/Desktop/Sahana/sahana-backend
python -m pytest app/test/test_friend_system.py -v
python -m pytest app/test/test_friend_integration.py -v
```

### Frontend Tests
```bash
# Run React component tests
npm test -- --testPathPattern=friends
```

## 📊 Database Structure

### Friend Requests Collection (`friend_requests`)
```json
{
  "id": "uuid-string",
  "sender_id": "user1@example.com",
  "receiver_id": "user2@example.com", 
  "status": "pending|accepted|rejected",
  "created_at": "2025-06-28T10:00:00Z",
  "updated_at": "2025-06-28T11:00:00Z"
}
```

### Users Collection (`users`) - Referenced
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "bio": "Event organizer",
  "profile_picture": "https://...",
  "location": {...},
  "interests": [...]
}
```

## 🔄 Friendship Status Flow

```
none → pending_sent → friends
  ↓        ↓
rejected   cancelled
```

- **none**: No relationship exists
- **pending_sent**: Current user sent request
- **pending_received**: Current user received request  
- **friends**: Request was accepted
- **rejected**: Request was rejected
- **cancelled**: Request was cancelled

## 🚦 Cache Invalidation Strategy

The system implements intelligent cache invalidation:

### Triggers for Cache Invalidation:
- ✨ **Friend request sent** → Update requests cache
- ✅ **Friend request accepted** → Update both friends and requests cache  
- ❌ **Friend request rejected** → Update requests cache
- 🚫 **Friend request cancelled** → Update requests cache
- 👤 **User profile updated** → Update friend profiles cache

### Frontend Cache Management:
- Redux Toolkit for state management
- Automatic cache invalidation on mutations
- Optimistic UI updates with rollback on errors

## 🔒 Security Features

- **Authentication required** for all endpoints
- **Authorization checks** prevent unauthorized access
- **Input validation** and sanitization
- **Rate limiting** ready (through FastAPI)
- **Privacy controls** for profile visibility

## 🎯 Performance Optimizations

### Backend:
- **Efficient Firestore queries** with proper indexing
- **Batch operations** for related data fetching
- **Connection pooling** and query optimization

### Frontend:
- **Component memoization** with React.memo
- **Debounced search** to reduce API calls
- **Virtual scrolling** for large friend lists
- **Code splitting** for lazy loading

## 🌟 Future Enhancements

### Planned Features:
- **🔔 Real-time notifications** for friend requests
- **👥 Mutual friends** display and discovery
- **🏷️ Friend categories** and custom tags
- **📊 Social analytics** and insights
- **🔍 Advanced search** with filters
- **💬 Integrated messaging** system

### Technical Improvements:
- **WebSocket integration** for real-time updates
- **GraphQL endpoint** for flexible queries
- **Background job processing** for notifications
- **Analytics and monitoring** dashboard

## 🚀 Deployment

### Backend Deployment
The friends system is automatically included when deploying the Sahana backend:

```bash
# The friends routes are already registered in app/main.py
docker build -t sahana-backend .
docker run -p 8080:8080 sahana-backend
```

### Frontend Integration
Follow the setup instructions in the [Frontend Implementation Guide](./docs/frontend/friends-implementation-guide.md).

## 📈 Metrics & Monitoring

### Key Metrics to Track:
- Friend request send/accept/reject rates
- Search query performance and usage
- User engagement with friends features
- API response times and error rates

### Monitoring Setup:
```python
# Example metrics collection
from prometheus_client import Counter, Histogram

friend_requests_total = Counter('friend_requests_total', 'Total friend requests', ['status'])
search_duration = Histogram('user_search_duration_seconds', 'User search query duration')
```

## 🤝 Contributing

### Development Workflow:
1. **Backend changes** → Update models, services, routes
2. **API changes** → Update documentation in `docs/api/friends.md`
3. **Frontend changes** → Follow patterns in implementation guide
4. **Testing** → Add unit and integration tests
5. **Documentation** → Update relevant docs

### Code Standards:
- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Strict mode, comprehensive typing
- **Testing**: Maintain >90% coverage
- **Documentation**: Keep docs in sync with code

---

## 📞 Support

For questions or issues with the friends system:

1. **Check the documentation** in `/docs/api/friends.md`
2. **Review the implementation guide** for frontend integration
3. **Run the test suite** to verify functionality
4. **Check logs** for error details and debugging info

The friends system is production-ready and scalable for the Sahana platform! 🎉
