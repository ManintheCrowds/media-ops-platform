"""Quick script to check if API keys are configured."""

import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.config import settings

print("=" * 60)
print("API Key Configuration Check")
print("=" * 60)
print()

# Check Adzuna
print("Adzuna API:")
print(f"  API ID: {'[OK] Set' if settings.adzuna_api_id else '[MISSING] Not Set'}")
if settings.adzuna_api_id:
    print(f"    Value: {settings.adzuna_api_id[:10]}...")
print(f"  API Key: {'[OK] Set' if settings.adzuna_api_key else '[MISSING] Not Set'}")
if settings.adzuna_api_key:
    print(f"    Value: {'*' * 20}")
print()

# Check JSearch
print("JSearch API:")
print(f"  API Key: {'[OK] Set' if settings.jsearch_api_key else '[MISSING] Not Set'}")
if settings.jsearch_api_key:
    print(f"    Value: {'*' * 20}")
print()

# Check The Muse
print("The Muse API:")
print(f"  API Key: {'[OK] Set' if settings.the_muse_api_key else '[SKIP] Not Set (optional)'}")
print()

# Check .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    print(f"[OK] .env file found at: {env_path}")
else:
    print(f"[MISSING] .env file NOT found at: {env_path}")
    print()
    print("To create .env file:")
    print("  1. Copy .env.example to .env")
    print("  2. Edit .env and add your API keys")
    print("  3. Format: ADZUNA_API_ID=your_id_here")
    print()

print("=" * 60)

