"""Direct test of JSearch API using httpx to verify key and subscription."""

import asyncio
import httpx
import json
from app.config import settings

async def test_direct():
    """Test JSearch API directly with detailed output."""
    api_key = settings.jsearch_api_key
    
    print("=" * 60)
    print("Direct JSearch API Test")
    print("=" * 60)
    print(f"API Key: {api_key[:15]}...{api_key[-10:] if len(api_key) > 25 else ''}")
    print(f"Key Length: {len(api_key)}")
    print()
    
    url = "https://jsearch.p.rapidapi.com/search"
    params = {
        "query": "Python developer in Minneapolis, MN",
        "page": "1",
        "num_pages": "1"
    }
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    
    print("Request Details:")
    print(f"  URL: {url}")
    print(f"  Params: {params}")
    print(f"  Headers: {list(headers.keys())}")
    print()
    
    async with httpx.AsyncClient() as client:
        try:
            print("Making request...")
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print()
            
            try:
                response_json = response.json()
                print("Response Body:")
                print(json.dumps(response_json, indent=2))
                
                if response.status_code == 200:
                    data = response_json.get("data", [])
                    print(f"\n✅ SUCCESS! Found {len(data)} jobs")
                else:
                    print(f"\n❌ ERROR: {response_json.get('message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"Response Text: {response.text[:500]}")
                print(f"Error parsing JSON: {e}")
                
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code}")
            try:
                error_json = e.response.json()
                print(f"Error Message: {error_json}")
            except:
                print(f"Error Text: {e.response.text[:500]}")
        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct())

