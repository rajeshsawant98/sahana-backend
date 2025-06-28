# Sahana Backend Documentation

Welcome to the Sahana Backend documentation. This directory contains comprehensive documentation for the Sahana social meetup and event discovery platform backend.

## 📋 Table of Contents

### 🚀 Getting Started

- [Quick Start Guide](setup/quick-start.md) - Get up and running quickly
- [Installation Guide](setup/installation.md) - Detailed setup instructions
- [Environment Configuration](setup/environment.md) - Environment variables and configuration

### 📚 API Documentation

- [API Overview](api/overview.md) - Introduction to the Sahana API
- [Authentication API](api/authentication.md) - Login, logout, and user management
- [Events API](api/events.md) - Event creation, discovery, and management
- [Users API](api/users.md) - User profiles and management
- [RSVP API](api/rsvp.md) - Event RSVP system
- [Friends API](api/friends.md) - Friend system endpoints
- [Pagination Guide](api/pagination.md) - Using pagination across endpoints
- [PAGINATION.md](api/PAGINATION.md) - Pagination implementation details
- [Error Handling](api/errors.md) - API error codes and responses
- [Friend System README](api/FRIENDS_README.md) - Comprehensive friend system docs
- [Friend System Details](api/FRIEND_SYSTEM_README.md) - Legacy friend system docs

### 🏗️ Architecture

- [Project Structure](architecture/structure.md) - Overview of the codebase organization
- [Database Schema](architecture/database.md) - Firestore collections and document structure
- [Authentication Flow](architecture/auth-flow.md) - How authentication works
- [Redundancy Analysis](architecture/REDUNDANCY_ANALYSIS_REPORT.md) - Code quality and optimization report

### 🔄 Migrations & Changes

- [Email ID Migration Plan](migrations/EMAIL_ID_MIGRATION_PLAN.md) - Migration strategy documentation
- [Email ID Migration Complete](migrations/EMAIL_ID_MIGRATION_COMPLETE.md) - Migration results and impact
- [Email ID Demo Script](migrations/demo_email_id_system.py) - Demonstration of new ID system

### 🎨 Frontend Integration

- [Friend System Implementation Guide](frontend/friends-implementation-guide.md) - Frontend integration for friend system

### 🚀 Deployment

- [Docker Deployment](deployment/docker.md) - Running with Docker
- [Cloud Deployment](deployment/cloud.md) - Deploying to cloud platforms
- [CI/CD Pipeline](deployment/cicd.md) - GitHub Actions workflow

### 🧪 Testing

- [Testing Guide](testing/guide.md) - How to run and write tests
- [API Testing](testing/api-testing.md) - Testing API endpoints

### 🔧 Development

- [Contributing Guidelines](development/contributing.md) - How to contribute to the project
- [Code Style](development/code-style.md) - Coding standards and conventions
- [Debugging](development/debugging.md) - Debugging tips and tools

## 🔗 Quick Links

- [Main README](../README.md) - Project overview and quick setup
- [API Base URL](http://localhost:8000) - Local development server
- [API Documentation](http://localhost:8000/docs) - Interactive Swagger docs
- [Requirements](../requirements.txt) - Python dependencies

## 🆘 Support

If you need help:

1. Check the relevant documentation section above
2. Look at the [API documentation](http://localhost:8000/docs) for interactive examples
3. Review the [troubleshooting section](troubleshooting.md)
4. Open an issue on GitHub

## 🔧 Recent Updates

- **Email-as-Canonical-ID Migration** (December 2025) - Simplified friend system and eliminated ID mismatch issues
- **Code Quality Improvements** (December 2025) - Standardized error handling and eliminated redundant code
- **Friend System MVP** (December 2025) - Complete friend system with API and frontend integration

---

**Last updated**: December 28, 2025
