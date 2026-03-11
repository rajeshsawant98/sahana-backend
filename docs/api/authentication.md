# Authentication API

This document covers the authentication system for the Sahana Backend API.

## Overview

Sahana uses JWT (JSON Web Token) based authentication with support for:

- Email/password authentication
- Google SSO (OAuth 2.0)
- Token refresh mechanism

## Endpoints

### Login with Email/Password

**Endpoint:** `POST /api/auth/login`

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
  "message": "User authenticated successfully",
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "token_type": "bearer",
  "email": "user@example.com"
}
```

### Google SSO Login

**Endpoint:** `POST /api/auth/google`

**Request Body:**

```json
{
  "token": "google_id_token"
}
```

**Response:** Same as email/password login (without `email` field)

### User Registration

**Endpoint:** `POST /api/auth/register`

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe"
}
```

**Response:** Same as login response

### Get Current User Profile

**Endpoint:** `GET /api/auth/me`

**Headers:** `Authorization: Bearer <access_token>`

### Update Profile

**Endpoint:** `PUT /api/auth/me`

**Headers:** `Authorization: Bearer <access_token>`

### Update Interests

**Endpoint:** `PUT /api/auth/me/interests`

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**

```json
{
  "interests": ["Technology", "Music", "Travel"]
}
```

### Token Refresh

**Endpoint:** `POST /api/auth/refresh`

**Request Body:**

```json
{
  "refresh_token": "your_refresh_token"
}
```

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
  "detail": "Invalid credentials"
}
```

### Token Expired / Invalid Token

```json
{
  "detail": "Token has expired"
}
```
