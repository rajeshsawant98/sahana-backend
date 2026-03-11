#!/usr/bin/env python3
"""
Simple test script to verify cursor pagination status on the main endpoint
"""

import requests
import json
import time

def test_main_events_endpoint():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Main Events Endpoint - Cursor Pagination Status")
    print("=" * 60)
    
    # Test 1: Cursor pagination (should work)
    print("\n✅ Test 1: Cursor Pagination")
    response = requests.get(f"{base_url}/api/events", params={"page_size": 2})
    if response.status_code == 200:
        data = response.json()
        if "pagination" in data and "next_cursor" in data["pagination"]:
            print(f"  ✅ Cursor pagination working!")
            print(f"  📊 Items: {len(data['items'])}")
            print(f"  📄 Has next: {data['pagination']['has_next']}")
            print(f"  🔗 Next cursor: {data['pagination']['next_cursor'][:50]}..." if data['pagination']['next_cursor'] else "None")
        else:
            print(f"  ❌ Unexpected response structure: {list(data.keys())}")
    else:
        print(f"  ❌ HTTP Error: {response.status_code}")
    
    # Test 2: Legacy pagination  
    print("\n🔄 Test 2: Legacy Pagination")
    response = requests.get(f"{base_url}/api/events", params={"page": 1, "page_size": 2})
    if response.status_code == 200:
        data = response.json()
        if "total_count" in data:
            print(f"  ✅ Legacy pagination working!")
            print(f"  📊 Items: {len(data['items'])}")
            print(f"  📈 Total count: {data['total_count']}")
            print(f"  📄 Page: {data['page']}")
        else:
            print(f"  ⚠️  Returns cursor format for legacy request")
            print(f"  📊 Items: {len(data.get('items', []))}")
    else:
        print(f"  ❌ HTTP Error: {response.status_code}")
    
    # Test 3: No pagination (default behavior)
    print("\n📦 Test 3: Default Behavior (No Pagination)")
    response = requests.get(f"{base_url}/api/events")
    if response.status_code == 200:
        data = response.json()
        if "events" in data:
            print(f"  ✅ Legacy format returned!")
            print(f"  📊 Events count: {len(data['events'])}")
        else:
            print(f"  ⚠️  Returns paginated format by default")
            print(f"  📊 Items: {len(data.get('items', []))}")
    else:
        print(f"  ❌ HTTP Error: {response.status_code}")
    
    # Test 4: Cursor navigation
    print("\n🔗 Test 4: Cursor Navigation") 
    first_response = requests.get(f"{base_url}/api/events", params={"page_size": 2})
    if first_response.status_code == 200:
        first_data = first_response.json()
        next_cursor = first_data["pagination"]["next_cursor"]
        
        if next_cursor:
            second_response = requests.get(f"{base_url}/api/events", params={
                "page_size": 2,
                "cursor": next_cursor
            })
            
            if second_response.status_code == 200:
                second_data = second_response.json()
                print(f"  ✅ Cursor navigation working!")
                print(f"  📊 Second page items: {len(second_data['items'])}")
                print(f"  📄 Has previous: {second_data['pagination']['has_previous']}")
            else:
                print(f"  ❌ Cursor navigation failed: {second_response.status_code}")
        else:
            print(f"  ⚠️  No next cursor available (single page)")
    
    # Test 5: Filters with cursor pagination
    print("\n🔍 Test 5: Filters with Cursor Pagination")
    response = requests.get(f"{base_url}/api/events", params={
        "page_size": 3,
        "city": "Denver"
    })
    if response.status_code == 200:
        data = response.json()
        if "pagination" in data:
            print(f"  ✅ Filters working with cursor pagination!")
            print(f"  📊 Filtered items: {len(data['items'])}")
            
            # Check if items actually match filter
            denver_count = sum(1 for item in data['items'] 
                             if item.get('location', {}).get('city') == 'Denver')
            print(f"  🎯 Denver events: {denver_count}/{len(data['items'])}")
        else:
            print(f"  ❌ Unexpected response structure")
    else:
        print(f"  ❌ HTTP Error: {response.status_code}")

if __name__ == "__main__":
    test_main_events_endpoint()
