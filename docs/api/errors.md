# Error Handling and Status Codes

This document describes the error handling system and status codes used in the Sahana Backend API.

## HTTP Status Codes

The API uses standard HTTP status codes to indicate the success or failure of requests.

### Success Codes (2xx)

| Code | Name | Description |
|------|------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `204` | No Content | Request successful, no content to return |

### Client Error Codes (4xx)

| Code | Name | Description |
|------|------|-------------|
| `400` | Bad Request | Invalid request parameters or body |
| `401` | Unauthorized | Authentication required or invalid |
| `403` | Forbidden | Access denied (insufficient permissions) |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource already exists or conflict |
| `422` | Unprocessable Entity | Validation error |
| `429` | Too Many Requests | Rate limit exceeded |

### Server Error Codes (5xx)

| Code | Name | Description |
|------|------|-------------|
| `500` | Internal Server Error | Unexpected server error |
| `502` | Bad Gateway | Invalid response from upstream server |
| `503` | Service Unavailable | Service temporarily unavailable |

## Error Response Format

All errors return a consistent JSON structure:

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2025-06-28T10:00:00Z"
}
```

For validation errors (422), the format includes field-specific details:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

## Authentication Errors

### Invalid Token (401)

```json
{
  "detail": "Invalid authentication credentials",
  "error_code": "INVALID_TOKEN"
}
```

### Token Expired (401)

```json
{
  "detail": "Token has expired",
  "error_code": "TOKEN_EXPIRED"
}
```

### Missing Token (401)

```json
{
  "detail": "Authentication required",
  "error_code": "MISSING_TOKEN"
}
```

### Insufficient Permissions (403)

```json
{
  "detail": "You don't have permission to access this resource",
  "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

## Event-Related Errors

### Event Not Found (404)

```json
{
  "detail": "Event not found",
  "error_code": "EVENT_NOT_FOUND"
}
```

### Event Full (409)

```json
{
  "detail": "Event has reached maximum capacity",
  "error_code": "EVENT_FULL",
  "max_attendees": 50,
  "current_attendees": 50
}
```

### Already RSVP'd (409)

```json
{
  "detail": "You have already RSVP'd to this event",
  "error_code": "ALREADY_RSVPED"
}
```

### Past Event (400)

```json
{
  "detail": "Cannot RSVP to past events",
  "error_code": "PAST_EVENT"
}
```

### Event Cancelled (400)

```json
{
  "detail": "Cannot RSVP to cancelled event",
  "error_code": "EVENT_CANCELLED"
}
```

## User-Related Errors

### User Not Found (404)

```json
{
  "detail": "User not found",
  "error_code": "USER_NOT_FOUND"
}
```

### Email Already Exists (409)

```json
{
  "detail": "User with this email already exists",
  "error_code": "EMAIL_EXISTS"
}
```

### Invalid Credentials (401)

```json
{
  "detail": "Invalid email or password",
  "error_code": "INVALID_CREDENTIALS"
}
```

## Validation Errors (422)

Common validation error types:

### Required Field Missing

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Invalid Email Format

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### String Too Short/Long

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 8}
    }
  ]
}
```

### Invalid Date Format

```json
{
  "detail": [
    {
      "loc": ["body", "date_time"],
      "msg": "invalid datetime format",
      "type": "value_error.datetime"
    }
  ]
}
```

## Rate Limiting Errors (429)

```json
{
  "detail": "Rate limit exceeded. Try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 3600
}
```

Rate limit headers are included in the response:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200
```

## Server Errors (5xx)

### Internal Server Error (500)

```json
{
  "detail": "An internal server error occurred",
  "error_code": "INTERNAL_ERROR"
}
```

### Service Unavailable (503)

```json
{
  "detail": "Service temporarily unavailable",
  "error_code": "SERVICE_UNAVAILABLE"
}
```

## Error Code Reference

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_TOKEN` | 401 | JWT token is invalid or malformed |
| `TOKEN_EXPIRED` | 401 | JWT token has expired |
| `MISSING_TOKEN` | 401 | Authorization header missing |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permissions |
| `EVENT_NOT_FOUND` | 404 | Event ID doesn't exist |
| `USER_NOT_FOUND` | 404 | User ID doesn't exist |
| `EVENT_FULL` | 409 | Event reached max capacity |
| `ALREADY_RSVPED` | 409 | User already RSVP'd to event |
| `NOT_RSVPED` | 400 | User hasn't RSVP'd to event |
| `EMAIL_EXISTS` | 409 | Email already registered |
| `INVALID_CREDENTIALS` | 401 | Login credentials incorrect |
| `PAST_EVENT` | 400 | Action not allowed on past event |
| `EVENT_CANCELLED` | 400 | Action not allowed on cancelled event |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `FILE_TOO_LARGE` | 400 | Uploaded file exceeds size limit |
| `INVALID_FILE_TYPE` | 400 | File type not allowed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily down |

## Error Handling Best Practices

### Client-Side Handling

1. **Check HTTP Status Code**: Use status codes to determine error type
2. **Parse Error Response**: Extract `error_code` for programmatic handling
3. **Display User-Friendly Messages**: Use `detail` for user feedback
4. **Handle Common Scenarios**: Implement retry logic for rate limits
5. **Log Errors**: Keep error logs for debugging

### Example Error Handling (JavaScript)

```javascript
async function handleApiCall(apiFunction) {
  try {
    const response = await apiFunction();
    return response;
  } catch (error) {
    if (error.status === 401 && error.data.error_code === 'TOKEN_EXPIRED') {
      // Refresh token and retry
      await refreshToken();
      return apiFunction();
    } else if (error.status === 429) {
      // Rate limited, wait and retry
      const retryAfter = error.headers['retry-after'] || 60;
      await sleep(retryAfter * 1000);
      return apiFunction();
    } else {
      // Show error to user
      showErrorMessage(error.data.detail);
      throw error;
    }
  }
}
```

## Debugging Tips

1. **Check Request Format**: Ensure JSON is valid and Content-Type is set
2. **Verify Authentication**: Include valid Bearer token in Authorization header
3. **Review Validation Errors**: Check field requirements and formats
4. **Monitor Rate Limits**: Respect rate limit headers
5. **Use Interactive Docs**: Test endpoints at `/docs` for quick debugging
