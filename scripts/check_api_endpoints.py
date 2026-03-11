#!/usr/bin/env python3
"""
API Endpoint Testing Script for Cursor Pagination
Tests all event endpoints with actual HTTP requests to verify cursor pagination works.
"""

import requests
import time
from typing import Dict, Any, Optional

def test_endpoint(base_url: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Test a single endpoint with cursor pagination"""
    if params is None:
        params = {}
    
    print(f"\n🔍 Testing: {endpoint}")
    results = {"endpoint": endpoint, "tests": []}
    
    try:
        # Test 1: Basic cursor pagination request
        print("  📄 Test 1: Basic pagination request")
        response = requests.get(f"{base_url}{endpoint}", params={**params, "page_size": 5}, timeout=10)
        
        test_result = {
            "name": "Basic Request",
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "details": ""
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Check response structure
                if "items" in data and "pagination" in data:
                    pagination = data["pagination"]
                    required_fields = ["next_cursor", "has_next", "page_size"]
                    missing_fields = [field for field in required_fields if field not in pagination]
                    
                    if missing_fields:
                        test_result["success"] = False
                        test_result["details"] = f"Missing pagination fields: {missing_fields}"
                    else:
                        test_result["details"] = f"✅ Items: {len(data['items'])}, Has Next: {pagination['has_next']}, Page Size: {pagination['page_size']}"
                        
                        # Test 2: Cursor navigation if next_cursor exists
                        if pagination.get("next_cursor") and pagination.get("has_next"):
                            print("  📄 Test 2: Cursor navigation")
                            cursor_response = requests.get(f"{base_url}{endpoint}", params={
                                **params,
                                "cursor": pagination["next_cursor"],
                                "page_size": 5
                            }, timeout=10)
                            
                            cursor_test = {
                                "name": "Cursor Navigation",
                                "success": cursor_response.status_code == 200,
                                "status_code": cursor_response.status_code,
                                "details": ""
                            }
                            
                            if cursor_response.status_code == 200:
                                cursor_data = cursor_response.json()
                                if "items" in cursor_data:
                                    cursor_test["details"] = f"✅ Next page loaded with {len(cursor_data['items'])} items"
                                else:
                                    cursor_test["success"] = False
                                    cursor_test["details"] = "❌ No items in cursor response"
                            else:
                                cursor_test["details"] = f"❌ Cursor request failed with status {cursor_response.status_code}"
                                
                            results["tests"].append(cursor_test)
                        else:
                            results["tests"].append({
                                "name": "Cursor Navigation",
                                "success": True,
                                "details": "✅ No next cursor available (end of data or single page)"
                            })
                            
                else:
                    test_result["success"] = False
                    test_result["details"] = "❌ Invalid response structure - missing 'items' or 'pagination'"
                    
            except ValueError:  # JSON decode error
                test_result["success"] = False
                test_result["details"] = "❌ Invalid JSON response"
        else:
            test_result["details"] = f"❌ HTTP Error {response.status_code}"
            if response.status_code == 401:
                test_result["details"] += " (Authentication required)"
            elif response.status_code == 403:
                test_result["details"] += " (Forbidden - admin required)"
            elif response.status_code == 404:
                test_result["details"] += " (Endpoint not found)"
                
        results["tests"].append(test_result)
        
        # Test 3: Legacy pagination compatibility
        print("  📄 Test 3: Legacy pagination")
        legacy_response = requests.get(f"{base_url}{endpoint}", params={**params, "page": 1, "page_size": 5}, timeout=10)
        
        legacy_test = {
            "name": "Legacy Compatibility",
            "success": legacy_response.status_code == 200,
            "status_code": legacy_response.status_code,
            "details": ""
        }
        
        if legacy_response.status_code == 200:
            try:
                legacy_data = legacy_response.json()
                if "total_count" in legacy_data:
                    legacy_test["details"] = "✅ Legacy pagination format supported"
                elif "items" in legacy_data and "pagination" in legacy_data:
                    legacy_test["details"] = "✅ Returns cursor format for legacy request"
                else:
                    legacy_test["success"] = False
                    legacy_test["details"] = "❌ Unexpected response format"
            except ValueError:  # JSON decode error
                legacy_test["success"] = False
                legacy_test["details"] = "❌ Invalid JSON in legacy response"
        else:
            legacy_test["details"] = f"❌ Legacy request failed with status {legacy_response.status_code}"
            
        results["tests"].append(legacy_test)
        
    except requests.exceptions.RequestException as e:
        results["tests"].append({
            "name": "Request Error",
            "success": False,
            "details": f"❌ Request failed: {str(e)}"
        })
    
    return results

def main():
    """Run comprehensive endpoint tests"""
    base_url = "http://localhost:8000"
    
    print("🚀 Starting Comprehensive Endpoint Testing")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Define all endpoints to test
    endpoints_to_test = [
        {"path": "/api/events", "name": "All Events", "params": {}, "public": True},
        {"path": "/api/events/location/nearby", "name": "Nearby Events", "params": {"city": "Denver", "state": "CO"}, "public": True},
        {"path": "/api/events/me/created", "name": "User Created Events", "params": {}, "public": False},
        {"path": "/api/events/me/rsvped", "name": "User RSVP Events", "params": {}, "public": False},
        {"path": "/api/events/me/organized", "name": "User Organized Events", "params": {}, "public": False},
        {"path": "/api/events/me/moderated", "name": "User Moderated Events", "params": {}, "public": False},
        {"path": "/api/events/me/archived", "name": "User Archived Events", "params": {}, "public": False},
        {"path": "/api/events/archived", "name": "Admin Archived Events", "params": {}, "public": False},
        {"path": "/api/admin/users", "name": "Admin Users Management", "params": {}, "public": False}
    ]
    
    all_results = []
    total_tests = 0
    passed_tests = 0
    
    for endpoint_config in endpoints_to_test:
        endpoint_path = endpoint_config["path"]
        endpoint_name = endpoint_config["name"]
        params = endpoint_config["params"]
        is_public = endpoint_config["public"]
        
        print(f"\n📍 {endpoint_name}")
        print("-" * 40)
        
        if not is_public:
            print("  ⚠️  Authentication required - testing without auth (expect 401/403)")
        
        results = test_endpoint(base_url, endpoint_path, params)
        all_results.append(results)
        
        # Count tests and display results
        for test in results["tests"]:
            total_tests += 1
            if test["success"]:
                passed_tests += 1
            
            status = "✅" if test["success"] else "❌"
            print(f"    {status} {test['name']}: {test['details']}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Show failed tests details
    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS SUMMARY:")
        for result in all_results:
            for test in result["tests"]:
                if not test["success"]:
                    print(f"  - {result['endpoint']} ({test['name']}): {test['details']}")
    
    # Show public endpoint results
    print(f"\n🌐 PUBLIC ENDPOINT RESULTS:")
    for endpoint_config in endpoints_to_test:
        if endpoint_config["public"]:
            endpoint_path = endpoint_config["path"]
            endpoint_result = next((r for r in all_results if r["endpoint"] == endpoint_path), None)
            if endpoint_result:
                success_count = sum(1 for t in endpoint_result["tests"] if t["success"])
                total_count = len(endpoint_result["tests"])
                status = "✅" if success_count == total_count else "⚠️"
                print(f"  {status} {endpoint_path}: {success_count}/{total_count} tests passed")
    
    print(f"\n🏁 Testing completed at {time.strftime('%H:%M:%S')}")
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "success_rate": success_rate,
        "results": all_results
    }

if __name__ == "__main__":
    main()
