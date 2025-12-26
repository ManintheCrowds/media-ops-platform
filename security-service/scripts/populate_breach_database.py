"""Script to populate breach database from public sources."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from security_service.database import get_db, init_db
from security_service.intelligence.public_breach_sources import PublicBreachSources
from security_service.config import config


async def main():
    """Populate breach database from configured public sources."""
    print("="*70)
    print("Breach Database Population Script")
    print("="*70)
    
    print("\n1. Initializing database...")
    try:
        init_db()
        print("   [OK] Database initialized")
    except Exception as e:
        print(f"   [WARNING] Database initialization: {e}")
        print("   Continuing with existing database...")
    
    print("\n2. Checking configured sources...")
    sources = config.public_breach_sources or []
    if not sources:
        print("   [WARNING] No public breach sources configured!")
        print("   Please set SECURITY_PUBLIC_BREACH_SOURCES in your .env file")
        print("   Example: SECURITY_PUBLIC_BREACH_SOURCES=https://raw.githubusercontent.com/user/repo/breaches.json")
        return
    else:
        print(f"   [OK] Found {len(sources)} configured source(s)")
        for i, source in enumerate(sources, 1):
            print(f"      {i}. {source}")
    
    print("\n3. Populating breach database from public sources...")
    db = next(get_db())
    try:
        public_sources = PublicBreachSources(db)
        result = await public_sources.update_breach_database(force=True)
        
        print("\n4. Update Results:")
        print("   " + "-"*66)
        if result.get("updated"):
            print("   [SUCCESS] Database updated successfully")
            print(f"   Breaches downloaded: {result.get('breaches_downloaded', 0)}")
            
            import_stats = result.get('import_stats', {})
            print(f"   Imported: {import_stats.get('imported', 0)} new breaches")
            print(f"   Updated: {import_stats.get('updated', 0)} existing breaches")
            print(f"   Errors: {import_stats.get('errors', 0)}")
            print(f"   Total processed: {import_stats.get('total_processed', 0)}")
            
            if result.get('last_update'):
                print(f"   Last update: {result.get('last_update')}")
        else:
            print("   [SKIPPED] " + result.get('reason', 'Unknown reason'))
            if result.get('error'):
                print(f"   Error: {result.get('error')}")
        
        print("\n5. Database Statistics:")
        stats = public_sources.get_statistics()
        print(f"   Total breach records: {stats.get('total_breach_records', 0)}")
        print(f"   Unique emails: {stats.get('unique_emails', 0)}")
        print(f"   Unique breach names: {stats.get('unique_breach_names', 0)}")
        print(f"   Unique domains: {stats.get('unique_domains', 0)}")
        
    except Exception as e:
        print(f"\n   [ERROR] Failed to populate database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "="*70)
    print("Population complete!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Check database statistics via API: GET /api/security/breaches/stats")
    print("  2. Test email lookup: GET /api/security/breaches/email/{email}")
    print("  3. Test domain lookup: GET /api/security/breaches/domain/{domain}")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())

