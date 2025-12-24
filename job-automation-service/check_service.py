#!/usr/bin/env python3
"""Quick service health check."""
import httpx
import sys

BASE_URL = "http://localhost:8004"

try:
    response = httpx.get(f"{BASE_URL}/health", timeout=5)
    print(f"[OK] Service is accessible: Status {response.status_code}")
    print(f"  Response: {response.text}")
    sys.exit(0)
except httpx.ConnectError:
    print("[FAIL] Service is not accessible - Connection refused")
    print("  Docker Desktop may not be running or the container is stopped")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error checking service: {e}")
    sys.exit(1)

