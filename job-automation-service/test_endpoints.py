#!/usr/bin/env python3
"""Test scheduler endpoints directly."""
import httpx

BASE_URL = "http://localhost:8004"

def test_endpoint(method, path, json_body=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "POST":
            response = httpx.post(url, json=json_body or {})
        else:
            response = httpx.request(method, url)
        print(f"{method} {path}: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        print(f"{method} {path}: ERROR - {e}")
        return False

if __name__ == "__main__":
    print("Testing scheduler endpoints...\n")
    
    # Test all scheduler endpoints
    results = []
    results.append(("POST /api/v1/scheduler/start", test_endpoint("POST", "/api/v1/scheduler/start", {})))
    results.append(("POST /api/v1/scheduler/stop", test_endpoint("POST", "/api/v1/scheduler/stop")))
    results.append(("POST /api/v1/scheduler/search", test_endpoint("POST", "/api/v1/scheduler/search", {"location": "Minneapolis, MN"})))
    
    print("\n" + "="*50)
    print("Summary:")
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

