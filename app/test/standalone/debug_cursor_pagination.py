#!/usr/bin/env python3
"""
Test script to debug cursor pagination implementation
"""
import sys
sys.path.append('/Users/rajesh/Desktop/Sahana/sahana-backend')

from app.models.pagination import CursorPaginationParams, EventFilters
from app.services.event_service import get_all_events_cursor_paginated, get_all_events

def test_cursor_pagination():
    """Test cursor pagination to see what's being returned"""
    print("🔍 Testing cursor pagination implementation...")
    
    try:
        # Test 1: Basic cursor pagination (first page)
        print("\n1. Testing first page with cursor pagination:")
        cursor_params = CursorPaginationParams(page_size=12)
        filters = EventFilters()
        
        result = get_all_events_cursor_paginated(cursor_params, filters)
        print(f"   Result type: {type(result)}")
        print(f"   Result dict: {result.model_dump() if hasattr(result, 'model_dump') else result}")
        
        # Test 2: Compare with legacy method
        print("\n2. Testing legacy get_all_events:")
        legacy_result = get_all_events()
        print(f"   Legacy result type: {type(legacy_result)}")
        print(f"   Legacy result length: {len(legacy_result) if isinstance(legacy_result, list) else 'Not a list'}")
        
        # Test 3: Check if service imports work
        print("\n3. Testing imports:")
        from app.repositories.events import EventRepositoryManager
        repo = EventRepositoryManager()
        print(f"   Repository created: {type(repo)}")
        
        # Test 4: Test repository method directly
        print("\n4. Testing repository method directly:")
        events, next_cursor, prev_cursor, has_next, has_previous = repo.get_all_events_cursor_paginated(cursor_params, filters)
        print(f"   Events count: {len(events)}")
        print(f"   Next cursor: {next_cursor}")
        print(f"   Has next: {has_next}")
        print(f"   Has previous: {has_previous}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cursor_pagination()
