# Authentication API

This document covers the authentication system for the Sahana Backend API.

## Overview

Sahana uses JWT (JSON Web Token) based authentication with support for:

- Email/password authentication
- Google SSO (OAuth 2.0)
- Token refresh mechanism

## Endpoints

### Login with Email/Password

**Endpoint:** `POST /auth/login`

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**

```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "name": "John Doe",
    "profile_picture": "https://example.com/photo.jpg"
  }
}
```

### Google SSO Login

**Endpoint:** `POST /auth/google`

**Request Body:**

```json
{
  "credential": "google_jwt_credential"
}
```

**Response:** Same as email/password login

### User Registration

**Endpoint:** `POST /auth/signup`

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe",
  "confirm_password": "secure_password"
}
```

### Token Refresh

**Endpoint:** `POST /auth/refresh`

**Request Body:**

```json
{
  "refresh_token": "your_refresh_token"
}
```

### Logout

**Endpoint:** `POST /auth/logout`

**Headers:** `Authorization: Bearer <access_token>`

## Token Usage

Include the access token in the Authorization header for protected endpoints:

```
Authorization: Bearer <your_access_token>
```

## Token Expiration

- **Access Token:** 1 hour (3600 seconds)
- **Refresh Token:** 7 days

Use the refresh token to obtain a new access token before it expires.

## Error Responses

### Invalid Credentials

```json
{
  "detail": "Invalid email or password",
  "error_code": "INVALID_CREDENTIALS"
}
```

### Token Expired

```json
{
  "detail": "Token has expired",
  "error_code": "TOKEN_EXPIRED"
}
```

### Invalid Token

```json
{
  "detail": "Invalid token",
  "error_code": "INVALID_TOKEN"
}
```
