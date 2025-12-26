"""Test Adzuna API directly with credentials."""
import asyncio
import httpx
from app.config import settings

async def test_adzuna():
    """Test Adzuna API directly."""
    print("Testing Adzuna API directly...")
    print(f"API ID: {settings.adzuna_api_id}")
    print(f"API Key: {'Set' if settings.adzuna_api_key else 'NOT SET'}")
    print()
    
    if not settings.adzuna_api_id or not settings.adzuna_api_key:
        print("ERROR: Credentials not configured!")
        return
    
    # Test API call
    url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
    params = {
        "app_id": settings.adzuna_api_id,
        "app_key": settings.adzuna_api_key,
        "what": "python developer",
        "where": "Minneapolis, MN",
        "results_per_page": 5
    }
    
    print(f"Making request to: {url}")
    print(f"Params: app_id={params['app_id']}, what={params['what']}, where={params['where']}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            print(f"Status Code: {response.status_code}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                results = data.get("results", [])
                print(f"SUCCESS! Found {count} jobs")
                print(f"Results returned: {len(results)}")
                print()
                
                if results:
                    print("First job:")
                    job = results[0]
                    print(f"  Title: {job.get('title', 'N/A')}")
                    print(f"  Company: {job.get('company', {}).get('display_name', 'N/A')}")
                    print(f"  Location: {job.get('location', {}).get('display_name', 'N/A')}")
                    print(f"  URL: {job.get('redirect_url', 'N/A')}")
                else:
                    print("No jobs in results array")
            else:
                print(f"ERROR: API returned status {response.status_code}")
                print(f"Response: {response.text[:500]}")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_adzuna())

