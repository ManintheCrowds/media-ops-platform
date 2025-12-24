"""Check if JobSourceManager can be imported and initialized."""

import sys

print("Testing imports...")

try:
    from app.services.job_source_manager import JobSourceManager
    print("[OK] JobSourceManager imported")
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    manager = JobSourceManager()
    print("[OK] JobSourceManager initialized")
    print(f"  Adzuna available: {manager.has_api_client('adzuna')}")
    print(f"  JSearch available: {manager.has_api_client('jsearch')}")
except Exception as e:
    print(f"[ERROR] Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[SUCCESS] All imports and initialization working!")

