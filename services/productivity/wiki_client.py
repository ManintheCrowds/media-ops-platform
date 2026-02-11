"""Wiki API client for BookStack."""

import httpx
import logging
from typing import Optional, Dict, List, Any
from services.base import BaseServiceClient
from services.productivity.config import WikiConfig
from app.exceptions import WikiError

logger = logging.getLogger(__name__)


class WikiClient(BaseServiceClient):
    """Client for BookStack wiki service."""
    
    def __init__(self, config: Optional[WikiConfig] = None):
        self.config = config or WikiConfig()
        self.api_token = self.config.api_token
        self.api_id = self.config.api_id
        self.api_secret = self.config.api_secret
        self._access_token: Optional[str] = None
        super().__init__(self.config.base_url)
    
    async def _get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token for BookStack API."""
        if self._access_token:
            return self._access_token
        
        if not self.api_id or not self.api_secret:
            raise WikiError("API credentials (api_id and api_secret) are required for OAuth2 authentication")
        
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
                else:
                    raise WikiError(f"Failed to get access token: HTTP {response.status_code}")
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error in {self.__class__.__name__}._get_access_token(): {e}")
            raise WikiError(f"HTTP error while getting access token: {e}")
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout in {self.__class__.__name__}._get_access_token(): {e}")
            raise WikiError(f"Timeout while getting access token: {e}")
        except WikiError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}._get_access_token(): {e}", exc_info=True)
            raise WikiError(f"Unexpected error while getting access token: {e}")
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for BookStack API.
        
        Note: This is called from __aenter__, but OAuth2 token fetching
        is async, so we handle it in the overridden __aenter__ method.
        """
        # This will be overridden by __aenter__ logic
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers
    
    def _get_api_base_url(self) -> str:
        """Get BookStack API base URL."""
        return self.base_url
    
    def _get_ping_endpoint(self) -> str:
        """Get BookStack health check endpoint."""
        return "/"
    
    async def __aenter__(self):
        """Override to handle OAuth2 token fetching."""
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
    
    # ping() is inherited from BaseServiceClient
    
    async def get_pages(self) -> List[Dict[str, Any]]:
        """Get list of pages from BookStack."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get("/api/pages"),
            "get_pages",
            default_return={}
        )
        # BookStack returns {"data": [...]} format
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        elif isinstance(result, list):
            return result
        return []
    
    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific page from BookStack."""
        await self._ensure_session()
        
        try:
            response = await self._session.get(f"/api/pages/{page_id}")
            if response.status_code == 200:
                data = response.json()
                # BookStack returns {"data": {...}} format
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
                return data
            elif response.status_code == 404:
                return None  # Page not found is a valid case
            else:
                raise WikiError(f"Failed to get page {page_id}: HTTP {response.status_code}")
        except WikiError:
            raise
        except Exception as e:
            raise WikiError(f"Error getting page {page_id}: {e}")
    
    async def get_books(self) -> List[Dict[str, Any]]:
        """Get list of books from BookStack."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get("/api/books"),
            "get_books",
            default_return={}
        )
        # BookStack returns {"data": [...]} format
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        elif isinstance(result, list):
            return result
        return []
    
    async def create_page(self, title: str, content: str, book_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Create a new page in BookStack."""
        await self._ensure_session()
        
        # BookStack requires book_id for creating pages
        if not book_id:
            # Try to get first book if none specified
            books = await self.get_books()
            if books:
                book_id = books[0].get("id")
            else:
                raise WikiError("No book_id provided and no books available")
        
        payload = {
            "name": title,
            "html": content,
            "book_id": book_id
        }
        
        try:
            response = await self._session.post("/api/pages", json=payload)
            if response.status_code in [200, 201]:
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
                return data
            else:
                raise WikiError(f"Failed to create page: HTTP {response.status_code}")
        except WikiError:
            raise
        except Exception as e:
            raise WikiError(f"Error creating page: {e}")


