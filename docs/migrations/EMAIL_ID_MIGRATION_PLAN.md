# Email as Canonical ID Migration Plan

## Current State
- **Email Users**: Document ID = email address
- **Google Users**: Document ID = Google UID (`sub` from JWT)
- **Friend Requests**: Use document IDs, causing mismatch issues

## Target State
- **All Users**: Document ID = email address
- **Simplified Logic**: One ID type across the entire system
- **Consistent Friend Requests**: Email-based IDs eliminate mismatch

## Migration Steps

### 1. Update User Creation Logic
- Modify `store_google_user()` to use email as document ID instead of UID
- Ensure all new Google users are stored with email as ID

### 2. Update Friend System Logic
- Remove ID resolution complexity from FriendService
- Use email directly as user ID for all operations
- Simplify all friend request methods

### 3. Backward Compatibility (Optional)
- Create migration script to move existing Google users from UID-based docs to email-based docs
- Or maintain dual lookup capability during transition period

### 4. Testing
- Update all tests to use email-based IDs consistently
- Verify friend system works seamlessly for all user types

## Benefits
- ✅ Eliminates ID mismatch issues in friend requests
- ✅ Simplifies codebase significantly
- ✅ Consistent user identification across all features
- ✅ Email is already unique and human-readable
- ✅ Easier debugging and database queries

## Implementation Priority
**HIGH** - This resolves the core friend system issue and simplifies future development.
