"""Direct test of JSearch API with instrumentation."""

import asyncio
import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app.services.api_clients.jsearch_api import JSearchAPIClient

async def main():
    print("Testing JSearch API directly...")
    print()
    
    client = JSearchAPIClient()
    
    try:
        print("Searching for 'Python developer' in 'Minneapolis, MN'...")
        jobs = await client.search_jobs("Python developer", "Minneapolis, MN", limit=5)
        print(f"Found {len(jobs)} jobs")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()
    
    print()
    print("Check debug.log for detailed logs")

if __name__ == "__main__":
    asyncio.run(main())

