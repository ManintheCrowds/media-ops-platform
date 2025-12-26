"""Check if API credentials are configured."""
from app.config import settings

print("API Credentials Status:")
print(f"  Adzuna API ID: {'[OK] Set' if settings.adzuna_api_id else '[MISSING] Not Set'}")
print(f"  Adzuna API Key: {'[OK] Set' if settings.adzuna_api_key else '[MISSING] Not Set'}")
print(f"  JSearch API Key: {'[OK] Set' if settings.jsearch_api_key else '[MISSING] Not Set'}")

if not settings.adzuna_api_id or not settings.adzuna_api_key:
    print("\n[WARNING] Adzuna API credentials are not configured.")
    print("   To configure, add to .env file:")
    print("   ADZUNA_API_ID=your_api_id")
    print("   ADZUNA_API_KEY=your_api_key")
else:
    print("\n[OK] Adzuna API credentials are configured.")

