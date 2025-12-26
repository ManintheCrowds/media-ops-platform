"""Test JSearch API directly with credentials."""
import asyncio
import httpx
from app.config import settings

async def test_jsearch():
    """Test JSearch API directly."""
    print("Testing JSearch API directly...")
    print(f"API Key: {'Set' if settings.jsearch_api_key else 'NOT SET'}")
    if settings.jsearch_api_key:
        print(f"API Key (first 20 chars): {settings.jsearch_api_key[:20]}...")
    print()
    
    if not settings.jsearch_api_key:
        print("ERROR: JSearch API key not configured!")
        return
    
    # Test API call
    url = "https://jsearch.p.rapidapi.com/search"
    params = {
        "query": "python developer in Minneapolis, MN",
        "page": "1",
        "num_pages": "1"
    }
    
    headers = {
        "X-RapidAPI-Key": settings.jsearch_api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    print(f"Making request to: {url}")
    print(f"Query: {params['query']}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            print(f"Status Code: {response.status_code}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                results = data.get("data", [])
                print(f"SUCCESS! Status: {status}")
                print(f"Results returned: {len(results)}")
                print()
                
                if results:
                    print("First job:")
                    job = results[0]
                    print(f"  Title: {job.get('job_title', 'N/A')}")
                    print(f"  Company: {job.get('employer_name', 'N/A')}")
                    print(f"  Location: {job.get('job_city', 'N/A')}, {job.get('job_state', 'N/A')}")
                    print(f"  URL: {job.get('job_apply_link', 'N/A')}")
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
    asyncio.run(test_jsearch())
