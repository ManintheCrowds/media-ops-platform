"""Wiki API client for BookStack."""

import httpx
from typing import Optional, Dict, List, Any
from services.productivity.config import WikiConfig


class WikiClient:
    """Client for BookStack wiki service."""
    
    def __init__(self, config: Optional[WikiConfig] = None):
        self.config = config or WikiConfig()
        self.base_url = self.config.base_url.rstrip('/')
        self.api_token = self.config.api_token
        self.api_id = self.config.api_id
        self.api_secret = self.config.api_secret
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
        headers = {}
        
        # Try to get OAuth2 token if API credentials are provided
        if self.api_id and self.api_secret:
            token = await self._get_access_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        self._session = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()
    
    async def ping(self) -> bool:
        """Check if wiki is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # BookStack root endpoint
                response = await client.get(self.base_url)
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_pages(self) -> List[Dict[str, Any]]:
        """Get list of pages from BookStack."""
        if not self._session:
            async with self:
                return await self.get_pages()
        
        try:
            # BookStack API endpoint for pages
            response = await self._session.get("/api/pages")
            if response.status_code == 200:
                data = response.json()
                # BookStack returns {"data": [...]} format
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
                elif isinstance(data, list):
                    return data
                return []
        except Exception:
            pass
        return []
    
    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific page from BookStack."""
        if not self._session:
            async with self:
                return await self.get_page(page_id)
        
        try:
            response = await self._session.get(f"/api/pages/{page_id}")
            if response.status_code == 200:
                data = response.json()
                # BookStack returns {"data": {...}} format
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
                return data
        except Exception:
            pass
        return None
    
    async def get_books(self) -> List[Dict[str, Any]]:
        """Get list of books from BookStack."""
        if not self._session:
            async with self:
                return await self.get_books()
        
        try:
            response = await self._session.get("/api/books")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
                elif isinstance(data, list):
                    return data
                return []
        except Exception:
            pass
        return []
    
    async def create_page(self, title: str, content: str, book_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Create a new page in BookStack."""
        if not self._session:
            async with self:
                return await self.create_page(title, content, book_id)
        
        try:
            # BookStack requires book_id for creating pages
            if not book_id:
                # Try to get first book if none specified
                books = await self.get_books()
                if books:
                    book_id = books[0].get("id")
                else:
                    return None
            
            payload = {
                "name": title,
                "html": content,
                "book_id": book_id
            }
            
            response = await self._session.post("/api/pages", json=payload)
            if response.status_code in [200, 201]:
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
                return data
        except Exception:
            pass
        return None


