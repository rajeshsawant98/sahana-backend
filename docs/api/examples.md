# API Examples and Use Cases

This document provides practical examples and common use cases for integrating with the Sahana Backend API.

## Table of Contents

1. [Authentication Flows](#authentication-flows)
2. [Event Management](#event-management)
3. [Friend System Integration](#friend-system-integration)
4. [Admin Operations](#admin-operations)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Frontend Integration](#frontend-integration)
7. [Mobile App Integration](#mobile-app-integration)

## Authentication Flows

### Complete Registration Flow

```javascript
// 1. Register new user
async function registerUser(userData) {
  try {
    const response = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: userData.email,
        password: userData.password,
        firstName: userData.firstName,
        lastName: userData.lastName
      })
    });

    if (response.ok) {
      const data = await response.json();
      // Store tokens
      localStorage.setItem('accessToken', data.accessToken);
      localStorage.setItem('refreshToken', data.refreshToken);
      return { success: true, user: data };
    } else {
      const error = await response.json();
      return { success: false, error: error.error.message };
    }
  } catch (error) {
    return { success: false, error: 'Network error' };
  }
}

// Usage
const result = await registerUser({
  email: 'john.doe@example.com',
  password: 'SecurePass123!',
  firstName: 'John',
  lastName: 'Doe'
});

if (result.success) {
  console.log('Registration successful:', result.user);
  // Redirect to dashboard
} else {
  console.error('Registration failed:', result.error);
  // Show error message
}
```

### Login with Auto-Refresh

```javascript
class AuthManager {
  constructor() {
    this.accessToken = localStorage.getItem('accessToken');
    this.refreshToken = localStorage.getItem('refreshToken');
    this.refreshPromise = null;
  }

  async login(email, password) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (response.ok) {
      const data = await response.json();
      this.setTokens(data.accessToken, data.refreshToken);
      return data;
    } else {
      throw new Error('Login failed');
    }
  }

  async makeAuthenticatedRequest(url, options = {}) {
    let token = this.accessToken;

    // Try the request with current token
    let response = await this.fetchWithAuth(url, token, options);

    // If unauthorized, try to refresh token
    if (response.status === 401 && this.refreshToken) {
      token = await this.refreshAccessToken();
      if (token) {
        response = await this.fetchWithAuth(url, token, options);
      }
    }

    return response;
  }

  async fetchWithAuth(url, token, options) {
    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async refreshAccessToken() {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this._performRefresh();
    try {
      const newToken = await this.refreshPromise;
      return newToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  async _performRefresh() {
    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken: this.refreshToken })
      });

      if (response.ok) {
        const data = await response.json();
        this.setTokens(data.accessToken, data.refreshToken);
        return data.accessToken;
      } else {
        this.logout();
        return null;
      }
    } catch (error) {
      this.logout();
      return null;
    }
  }

  setTokens(accessToken, refreshToken) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
  }

  logout() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/login';
  }
}
```

## Event Management

### Create and Manage Event Workflow

```javascript
class EventManager {
  constructor(authManager) {
    this.auth = authManager;
  }

  async createEvent(eventData) {
    const response = await this.auth.makeAuthenticatedRequest('/api/events/new', {
      method: 'POST',
      body: JSON.stringify({
        eventName: eventData.name,
        description: eventData.description,
        location: {
          address: eventData.address,
          city: eventData.city,
          state: eventData.state,
          zipCode: eventData.zipCode
        },
        startTime: eventData.startTime,
        duration: eventData.duration,
        categories: eventData.categories,
        isOnline: eventData.isOnline,
        joinLink: eventData.joinLink || '',
        imageUrl: eventData.imageUrl || ''
      })
    });

    if (response.ok) {
      const data = await response.json();
      return { success: true, eventId: data.eventId };
    } else {
      const error = await response.json();
      return { success: false, error: error.error.message };
    }
  }

  async getEvents(filters = {}) {
    const queryParams = new URLSearchParams();
    
    // Add pagination
    if (filters.page) queryParams.append('page', filters.page);
    if (filters.pageSize) queryParams.append('page_size', filters.pageSize);
    
    // Add filters
    if (filters.city) queryParams.append('city', filters.city);
    if (filters.state) queryParams.append('state', filters.state);
    if (filters.category) queryParams.append('category', filters.category);
    if (filters.isOnline !== undefined) queryParams.append('is_online', filters.isOnline);

    const url = `/api/events?${queryParams.toString()}`;
    const response = await this.auth.makeAuthenticatedRequest(url);

    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to fetch events');
    }
  }

  async rsvpToEvent(eventId) {
    const response = await this.auth.makeAuthenticatedRequest(`/api/events/${eventId}/rsvp`, {
      method: 'POST'
    });

    if (response.ok) {
      return await response.json();
    } else {
      const error = await response.json();
      throw new Error(error.error.message);
    }
  }

  async cancelRsvp(eventId) {
    const response = await this.auth.makeAuthenticatedRequest(`/api/events/${eventId}/rsvp`, {
      method: 'DELETE'
    });

    return response.ok;
  }

  async archiveEvent(eventId, reason) {
    const response = await this.auth.makeAuthenticatedRequest(`/api/events/${eventId}/archive`, {
      method: 'PATCH',
      body: JSON.stringify({ reason })
    });

    if (response.ok) {
      return await response.json();
    } else {
      const error = await response.json();
      throw new Error(error.error.message);
    }
  }
}

// Usage Example
async function completeEventWorkflow() {
  const authManager = new AuthManager();
  const eventManager = new EventManager(authManager);

  try {
    // 1. Create an event
    const eventResult = await eventManager.createEvent({
      name: 'Tech Meetup San Francisco',
      description: 'Monthly tech networking event',
      address: '123 Tech Street',
      city: 'San Francisco',
      state: 'CA',
      zipCode: '94102',
      startTime: '2025-07-15T18:00:00Z',
      duration: 120,
      categories: ['technology', 'networking'],
      isOnline: false
    });

    if (eventResult.success) {
      console.log('Event created:', eventResult.eventId);

      // 2. RSVP to the event (different user)
      await eventManager.rsvpToEvent(eventResult.eventId);
      console.log('RSVP successful');

      // 3. Get event details
      const events = await eventManager.getEvents({ 
        city: 'San Francisco',
        page: 1,
        pageSize: 10
      });
      console.log('Events found:', events.events.length);

    } else {
      console.error('Event creation failed:', eventResult.error);
    }
  } catch (error) {
    console.error('Workflow error:', error.message);
  }
}
```

## Friend System Integration

### Complete Friend Management

```javascript
class FriendManager {
  constructor(authManager) {
    this.auth = authManager;
  }

  async sendFriendRequest(friendEmail) {
    const response = await this.auth.makeAuthenticatedRequest('/api/friends/request', {
      method: 'POST',
      body: JSON.stringify({ friendEmail })
    });

    if (response.ok) {
      return await response.json();
    } else {
      const error = await response.json();
      throw new Error(error.error.message);
    }
  }

  async acceptFriendRequest(requesterEmail) {
    const response = await this.auth.makeAuthenticatedRequest('/api/friends/accept', {
      method: 'POST',
      body: JSON.stringify({ requesterEmail })
    });

    return response.ok;
  }

  async declineFriendRequest(requesterEmail) {
    const response = await this.auth.makeAuthenticatedRequest('/api/friends/decline', {
      method: 'POST',
      body: JSON.stringify({ requesterEmail })
    });

    return response.ok;
  }

  async getFriends() {
    const response = await this.auth.makeAuthenticatedRequest('/api/friends');
    
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to fetch friends');
    }
  }

  async getPendingRequests() {
    const response = await this.auth.makeAuthenticatedRequest('/api/friends/pending');
    
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to fetch pending requests');
    }
  }

  async checkFriendshipStatus(userId) {
    const response = await this.auth.makeAuthenticatedRequest(`/api/friends/status/${userId}`);
    
    if (response.ok) {
      return await response.json();
    } else {
      return { status: 'none' };
    }
  }
}

// Usage Example: Friend Request Workflow
async function friendRequestWorkflow() {
  const authManager = new AuthManager();
  const friendManager = new FriendManager(authManager);

  try {
    // 1. Send friend request
    const request = await friendManager.sendFriendRequest('friend@example.com');
    console.log('Friend request sent:', request.message);

    // 2. Check pending requests (as the recipient)
    const pendingRequests = await friendManager.getPendingRequests();
    console.log('Pending requests:', pendingRequests.pending_requests);

    // 3. Accept a friend request
    if (pendingRequests.pending_requests.length > 0) {
      const firstRequest = pendingRequests.pending_requests[0];
      await friendManager.acceptFriendRequest(firstRequest.requesterEmail);
      console.log('Friend request accepted');
    }

    // 4. Get friends list
    const friends = await friendManager.getFriends();
    console.log('Current friends:', friends.friends);

  } catch (error) {
    console.error('Friend workflow error:', error.message);
  }
}
```

## Admin Operations

### Admin Dashboard Data Fetching

```javascript
class AdminManager {
  constructor(authManager) {
    this.auth = authManager;
  }

  async getAllUsers(page = 1, pageSize = 50) {
    const response = await this.auth.makeAuthenticatedRequest(
      `/api/users?page=${page}&page_size=${pageSize}`
    );

    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to fetch users');
    }
  }

  async getAllArchivedEvents(page = 1, pageSize = 20) {
    const response = await this.auth.makeAuthenticatedRequest(
      `/api/events/archived?page=${page}&page_size=${pageSize}`
    );

    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to fetch archived events');
    }
  }

  async bulkArchivePastEvents() {
    const response = await this.auth.makeAuthenticatedRequest('/api/events/archive/past-events', {
      method: 'POST'
    });

    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to archive past events');
    }
  }

  async ingestTicketmasterEvents(city, state) {
    const response = await this.auth.makeAuthenticatedRequest('/api/events/fetch-ticketmaster-events', {
      method: 'POST',
      body: JSON.stringify({ city, state })
    });

    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to ingest Ticketmaster events');
    }
  }
}

// Admin Dashboard Component Example
async function loadAdminDashboard() {
  const authManager = new AuthManager();
  const adminManager = new AdminManager(authManager);

  try {
    // Load dashboard data in parallel
    const [users, archivedEvents] = await Promise.all([
      adminManager.getAllUsers(1, 20),
      adminManager.getAllArchivedEvents(1, 10)
    ]);

    // Display statistics
    console.log('Dashboard Data:');
    console.log(`Total Users: ${users.pagination.total}`);
    console.log(`Archived Events: ${archivedEvents.pagination.total}`);

    // Bulk operations
    const archiveResult = await adminManager.bulkArchivePastEvents();
    console.log(`Archived ${archiveResult.archived_count} past events`);

  } catch (error) {
    console.error('Dashboard loading error:', error.message);
  }
}
```

## Error Handling Patterns

### Robust Error Handling

```javascript
class ApiErrorHandler {
  static async handleResponse(response) {
    if (response.ok) {
      return await response.json();
    }

    const errorData = await response.json().catch(() => ({}));
    
    switch (response.status) {
      case 400:
        throw new ValidationError(errorData.error?.message || 'Invalid request');
      case 401:
        throw new AuthenticationError('Authentication required');
      case 403:
        throw new AuthorizationError('Access denied');
      case 404:
        throw new NotFoundError('Resource not found');
      case 409:
        throw new ConflictError(errorData.error?.message || 'Resource conflict');
      case 422:
        throw new ValidationError(errorData.error?.message || 'Validation failed');
      case 429:
        throw new RateLimitError('Rate limit exceeded');
      case 500:
        throw new ServerError('Internal server error');
      default:
        throw new ApiError(`HTTP ${response.status}: ${errorData.error?.message || 'Unknown error'}`);
    }
  }

  static handleError(error) {
    if (error instanceof AuthenticationError) {
      // Redirect to login
      window.location.href = '/login';
    } else if (error instanceof ValidationError) {
      // Show validation errors
      this.showValidationErrors(error.message);
    } else if (error instanceof RateLimitError) {
      // Show rate limit message
      this.showRateLimitMessage();
    } else {
      // Show generic error
      this.showGenericError(error.message);
    }
  }

  static showValidationErrors(message) {
    // Implementation for showing validation errors
    console.error('Validation Error:', message);
  }

  static showRateLimitMessage() {
    // Implementation for rate limit message
    console.warn('Rate limit exceeded. Please try again later.');
  }

  static showGenericError(message) {
    // Implementation for generic error display
    console.error('Error:', message);
  }
}

// Custom Error Classes
class ApiError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ApiError';
  }
}

class ValidationError extends ApiError {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
  }
}

class AuthenticationError extends ApiError {
  constructor(message) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

class AuthorizationError extends ApiError {
  constructor(message) {
    super(message);
    this.name = 'AuthorizationError';
  }
}

class NotFoundError extends ApiError {
  constructor(message) {
    super(message);
    this.name = 'NotFoundError';
  }
}

class ConflictError extends ApiError {
  constructor(message) {
    super(message);
    this.name = 'ConflictError';
  }
}

class RateLimitError extends ApiError {
  constructor(message) {
    super(message);
    this.name = 'RateLimitError';
  }
}

class ServerError extends ApiError {
  constructor(message) {
    super(message);
    this.name = 'ServerError';
  }
}
```

## Frontend Integration

### React Hook for API Integration

```jsx
import { useState, useEffect, useCallback } from 'react';

// Custom hook for API calls
export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const apiCall = useCallback(async (url, options = {}) => {
    setLoading(true);
    setError(null);

    try {
      const authManager = new AuthManager();
      const response = await authManager.makeAuthenticatedRequest(url, options);
      const data = await ApiErrorHandler.handleResponse(response);
      return data;
    } catch (err) {
      setError(err.message);
      ApiErrorHandler.handleError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { apiCall, loading, error };
};

// Event Management Component
export const EventManager = () => {
  const { apiCall, loading, error } = useApi();
  const [events, setEvents] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);

  const loadEvents = useCallback(async (page = 1) => {
    try {
      const data = await apiCall(`/api/events?page=${page}&page_size=10`);
      setEvents(data.events);
      setCurrentPage(page);
    } catch (error) {
      console.error('Failed to load events:', error);
    }
  }, [apiCall]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  const handleRsvp = async (eventId) => {
    try {
      await apiCall(`/api/events/${eventId}/rsvp`, { method: 'POST' });
      // Reload events to update RSVP status
      await loadEvents(currentPage);
    } catch (error) {
      console.error('RSVP failed:', error);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Events</h2>
      {events.map(event => (
        <div key={event.eventId}>
          <h3>{event.eventName}</h3>
          <p>{event.description}</p>
          <button onClick={() => handleRsvp(event.eventId)}>
            RSVP
          </button>
        </div>
      ))}
    </div>
  );
};
```

## Mobile App Integration

### iOS Swift Example

```swift
import Foundation

class SahanaAPI {
    private let baseURL = "https://api.sahana.com"
    private var accessToken: String?
    private var refreshToken: String?
    
    // MARK: - Authentication
    
    func login(email: String, password: String, completion: @escaping (Result<LoginResponse, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/auth/login") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let loginData = LoginRequest(email: email, password: password)
        
        do {
            request.httpBody = try JSONEncoder().encode(loginData)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(APIError.noData))
                return
            }
            
            do {
                let loginResponse = try JSONDecoder().decode(LoginResponse.self, from: data)
                self.accessToken = loginResponse.accessToken
                self.refreshToken = loginResponse.refreshToken
                
                // Store tokens securely
                self.storeTokensInKeychain(accessToken: loginResponse.accessToken,
                                         refreshToken: loginResponse.refreshToken)
                
                completion(.success(loginResponse))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    // MARK: - Authenticated Requests
    
    func makeAuthenticatedRequest<T: Codable>(
        endpoint: String,
        method: HTTPMethod = .GET,
        body: Data? = nil,
        responseType: T.Type,
        completion: @escaping (Result<T, Error>) -> Void
    ) {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = body
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            // Handle 401 Unauthorized - try to refresh token
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 401 {
                self.refreshAccessToken { refreshResult in
                    switch refreshResult {
                    case .success:
                        // Retry the original request
                        self.makeAuthenticatedRequest(endpoint: endpoint,
                                                    method: method,
                                                    body: body,
                                                    responseType: responseType,
                                                    completion: completion)
                    case .failure(let error):
                        completion(.failure(error))
                    }
                }
                return
            }
            
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(APIError.noData))
                return
            }
            
            do {
                let response = try JSONDecoder().decode(responseType, from: data)
                completion(.success(response))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    // MARK: - Token Management
    
    private func refreshAccessToken(completion: @escaping (Result<Void, Error>) -> Void) {
        guard let refreshToken = refreshToken,
              let url = URL(string: "\(baseURL)/auth/refresh") else {
            completion(.failure(APIError.noRefreshToken))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let refreshData = RefreshRequest(refreshToken: refreshToken)
        
        do {
            request.httpBody = try JSONEncoder().encode(refreshData)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            // Handle refresh response
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(APIError.noData))
                return
            }
            
            do {
                let refreshResponse = try JSONDecoder().decode(RefreshResponse.self, from: data)
                self.accessToken = refreshResponse.accessToken
                self.refreshToken = refreshResponse.refreshToken
                
                // Update stored tokens
                self.storeTokensInKeychain(accessToken: refreshResponse.accessToken,
                                         refreshToken: refreshResponse.refreshToken)
                
                completion(.success(()))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    private func storeTokensInKeychain(accessToken: String, refreshToken: String) {
        // Implementation for storing tokens securely in iOS Keychain
        // This is a simplified example - use proper Keychain services in production
        UserDefaults.standard.set(accessToken, forKey: "access_token")
        UserDefaults.standard.set(refreshToken, forKey: "refresh_token")
    }
}

// MARK: - Data Models

struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct LoginResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let user: User
}

struct RefreshRequest: Codable {
    let refreshToken: String
}

struct RefreshResponse: Codable {
    let accessToken: String
    let refreshToken: String
}

struct User: Codable {
    let userId: String
    let email: String
    let firstName: String
    let lastName: String
}

enum HTTPMethod: String {
    case GET = "GET"
    case POST = "POST"
    case PUT = "PUT"
    case DELETE = "DELETE"
    case PATCH = "PATCH"
}

enum APIError: Error {
    case noData
    case noRefreshToken
    case invalidResponse
}

// MARK: - Usage Example

class EventViewController: UIViewController {
    private let api = SahanaAPI()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        loadEvents()
    }
    
    private func loadEvents() {
        api.makeAuthenticatedRequest(
            endpoint: "/api/events?page=1&page_size=20",
            responseType: EventsResponse.self
        ) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let eventsResponse):
                    self.updateUI(with: eventsResponse.events)
                case .failure(let error):
                    self.showError(error)
                }
            }
        }
    }
    
    private func updateUI(with events: [Event]) {
        // Update UI with events
    }
    
    private func showError(_ error: Error) {
        // Show error to user
    }
}
```

---

*These examples demonstrate production-ready patterns for integrating with the Sahana Backend API. Adapt them to your specific use case and always implement proper error handling and security measures.*
