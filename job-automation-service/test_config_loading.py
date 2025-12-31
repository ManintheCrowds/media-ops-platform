"""Test config loading with explicit dotenv."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("TESTING CONFIG LOADING")
print("=" * 80)
print()

# Test dotenv loading
from dotenv import load_dotenv
import os

env_path = Path(r"D:\software\job-automation-service\.env")
print(f"1. Checking .env file:")
print(f"   Path: {env_path}")
print(f"   Exists: {env_path.exists()}")
print()

if env_path.exists():
    print("2. Loading .env file with dotenv...")
    load_dotenv(env_path, override=True)
    print(f"   [OK] Loaded .env file")
    print()
    
    print("3. Checking environment variables:")
    print(f"   ADZUNA_API_ID: {os.getenv('ADZUNA_API_ID', 'NOT SET')}")
    print(f"   ADZUNA_API_KEY: {'Set' if os.getenv('ADZUNA_API_KEY') else 'NOT SET'}")
    print(f"   JSEARCH_API_KEY: {'Set' if os.getenv('JSEARCH_API_KEY') else 'NOT SET'}")
    print()
    
    print("4. Loading Settings class...")
    from app.config import settings
    print(f"   [CONFIG] message should appear above")
    print()
    
    print("5. Settings values:")
    print(f"   Adzuna API ID: {settings.adzuna_api_id}")
    print(f"   Adzuna API Key: {'Set' if settings.adzuna_api_key else 'NOT SET'}")
    print(f"   JSearch API Key: {'Set' if settings.jsearch_api_key else 'NOT SET'}")
    print()
    
    print("6. Testing JobSourceManager...")
    from app.services.job_source_manager import JobSourceManager
    manager = JobSourceManager()
    print(f"   Has Adzuna client: {manager.has_api_client('adzuna')}")
    print()
    
    if manager.has_api_client('adzuna'):
        print("[SUCCESS] Config loading works!")
    else:
        print("[ERROR] Config loading failed - Adzuna client not available")
else:
    print("[ERROR] .env file not found!")

print()
print("=" * 80)





