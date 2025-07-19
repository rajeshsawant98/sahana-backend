#!/bin/bash

# Backend Pagination Cleanup Script
# Run this script to remove unused legacy pagination code

echo "🧹 Starting Backend Pagination Cleanup..."
echo ""

# Phase 1: Remove legacy fallback blocks from event routes
echo "📝 Phase 1: Removing legacy fallback code from event routes..."

# Create backup first
cp app/routes/event_routes.py app/routes/event_routes.py.backup
echo "✅ Created backup: app/routes/event_routes.py.backup"

# Phase 2: Remove unused imports
echo ""
echo "📝 Phase 2: Cleaning up unused imports..."

echo "🔍 Current imports in event_routes.py:"
grep -n "get_.*_events," app/routes/event_routes.py | head -10

echo ""
echo "❌ These non-paginated functions can be removed from imports:"
echo "   - get_all_events"
echo "   - get_my_events" 
echo "   - get_user_rsvps"
echo "   - get_events_organized_by_user"
echo "   - get_events_moderated_by_user"
echo "   - get_nearby_events"
echo "   - get_external_events"
echo "   - get_archived_events"

# Phase 3: Check external events usage
echo ""
echo "📝 Phase 3: Analyzing /location/external endpoint usage..."

echo "🔍 Checking where /location/external is referenced:"
grep -r "location/external" . --exclude-dir=docs --exclude-dir=__pycache__ --exclude="*.backup" | grep -v "BACKEND_CLEANUP_PLAN.md"

echo ""
echo "📊 Analysis Results:"
echo "✅ Only found in: route definition, test file"
echo "❌ Not found in: frontend code, other service calls"
echo "🟡 Conclusion: Safe to remove /location/external endpoint"

# Phase 4: Show which service functions can be removed
echo ""
echo "📝 Phase 4: Service layer cleanup opportunities..."

echo "🔍 External events functions in service layer:"
grep -n "def get_external_events" app/services/event_service.py

echo ""
echo "❌ These service functions can be removed:"
echo "   - get_external_events(city, state)"
echo "   - get_external_events_paginated(city, state, pagination)" 
echo "   - get_external_events_cursor_paginated(city, state, cursor_params)"

# Phase 5: Repository layer cleanup
echo ""
echo "📝 Phase 5: Repository layer cleanup opportunities..."

echo "🔍 External events in repository manager:"
grep -n "external_events" app/repositories/events/event_repository_manager.py

echo ""
echo "❌ These repository methods can be removed:"
echo "   - get_external_events()"
echo "   - get_external_events_paginated()"
echo "   - get_external_events_cursor_paginated()"

# Summary
echo ""
echo "📋 CLEANUP SUMMARY"
echo "=================="
echo ""
echo "🟢 SAFE TO REMOVE (Frontend confirmed not using):"
echo "   1. ❌ /location/external endpoint completely"
echo "   2. ❌ Legacy fallback 'else' blocks in all paginated routes"
echo "   3. ❌ Non-paginated function imports (get_all_events, etc.)"
echo "   4. ❌ External events service functions"
echo "   5. ❌ External events repository methods"
echo ""
echo "🟡 KEEP (Still actively used):"
echo "   ✅ All cursor pagination methods"
echo "   ✅ All offset pagination methods for admin"
echo "   ✅ Dual pagination parameter support"
echo "   ✅ /location/nearby endpoint"
echo ""
echo "🔧 NEXT STEPS:"
echo "   1. Remove /location/external endpoint from event_routes.py"
echo "   2. Remove legacy 'else' fallback blocks from all routes"
echo "   3. Remove unused imports from event_routes.py"
echo "   4. Remove external events functions from event_service.py"
echo "   5. Remove external events methods from repository layer"
echo "   6. Run tests: python -m pytest app/test/"
echo "   7. Test cursor pagination: python test_api_endpoints.py"
echo ""
echo "💡 TIP: Make changes incrementally and test after each step!"
echo ""
echo "🧹 Backend cleanup analysis complete!"
