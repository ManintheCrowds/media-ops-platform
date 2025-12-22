"""BookStack integration client."""

import httpx
from typing import Optional, Dict, Any
from app.config import settings


class BookStackClient:
    """Client for BookStack API integration."""
    
    def __init__(self):
        self.base_url = settings.bookstack_url.rstrip('/')
        self.api_id = settings.bookstack_api_id
        self.api_secret = settings.bookstack_api_secret
        self._session: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
    
    async def _get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token for BookStack API."""
        if self._access_token:
            return self._access_token
        
        if not self.api_id or not self.api_secret:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/oauth/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.api_id,
                        "client_secret": self.api_secret,
                        "scope": ""
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data.get("access_token")
                    return self._access_token
        except Exception:
            pass
        return None
    
    async def __aenter__(self):
        token = await self._get_access_token()
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        self._session = httpx.AsyncClient(
            base_url=f"{self.base_url}/api",
            timeout=30.0,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()
    
    async def get_page(self, page_id: int) -> Optional[Dict[str, Any]]:
        """Get a BookStack page by ID."""
        try:
            response = await self._session.get(f"/pages/{page_id}")
            if response.status_code == 200:
                data = response.json()
                return data.get("data") if isinstance(data, dict) and "data" in data else data
        except Exception:
            pass
        return None
    
    async def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get a BookStack book by ID."""
        try:
            response = await self._session.get(f"/books/{book_id}")
            if response.status_code == 200:
                data = response.json()
                return data.get("data") if isinstance(data, dict) and "data" in data else data
        except Exception:
            pass
        return None




