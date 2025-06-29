# Architecture Documentation Index

This folder contains comprehensive architecture documentation for the Sahana Backend system.

## Repository Architecture

### Core Architecture Documents

- **[Event Repository Architecture](./event-repository-architecture.md)** - Detailed guide to the modular repository pattern implementation
- **[Repository Refactoring Summary](./REPOSITORY_REFACTORING_SUMMARY.md)** - Summary of the monolithic to modular repository transformation
- **[Archive Implementation Summary](./ARCHIVE_IMPLEMENTATION_SUMMARY.md)** - Event archiving system architecture and implementation

## Architecture Overview

The Sahana Backend follows Clean Architecture principles with a well-defined separation of concerns:

```
┌─────────────────────────────────────────────────┐
│                 Routes Layer                    │
│            (Thin Controllers)                   │
├─────────────────────────────────────────────────┤
│                Services Layer                   │
│           (Business Logic)                      │
├─────────────────────────────────────────────────┤
│              Repository Layer                   │
│             (Data Access)                       │
├─────────────────────────────────────────────────┤
│               Database Layer                    │
│            (Firebase Firestore)                 │
└─────────────────────────────────────────────────┘
```

### Repository Pattern Implementation

The repository layer uses a specialized repository pattern with:

- **BaseRepository**: Common functionality and modular filters
- **EventCrudRepository**: Basic CRUD operations
- **EventQueryRepository**: Complex queries and filtering
- **EventArchiveRepository**: Archive management
- **EventRsvpRepository**: RSVP operations
- **EventUserRepository**: User-specific queries
- **EventRepositoryManager**: Facade providing unified interface

### Key Architectural Principles

1. **Single Responsibility Principle**: Each class has one focused purpose
2. **Open/Closed Principle**: Open for extension, closed for modification
3. **Dependency Inversion**: High-level modules don't depend on low-level modules
4. **Separation of Concerns**: Clear boundaries between layers
5. **Modularity**: Reusable components and clear interfaces

## Quick Navigation

- **Getting Started**: See [../setup/quick-start.md](../setup/quick-start.md)
- **API Documentation**: See [../api/README.md](../api/README.md)
- **Development Guide**: See [../README.md](../README.md)
- **Work History**: See [../WORK_LOG.md](../WORK_LOG.md)

## Architecture Benefits

✅ **Maintainable**: Small, focused classes easy to understand and modify  
✅ **Testable**: Each component can be unit tested independently  
✅ **Scalable**: Easy to extend with new features and functionality  
✅ **Robust**: Comprehensive error handling and logging  
✅ **Performance**: Optimized queries and efficient data access patterns  
✅ **Type Safe**: Full typing throughout the codebase  

The architecture is designed to support long-term maintainability and team development while ensuring production reliability and performance.
