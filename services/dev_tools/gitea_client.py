"""Gitea API client."""

import httpx
import logging
from typing import Optional, Dict, List, Any
from services.base import BaseServiceClient
from services.dev_tools.config import GiteaConfig
from app.exceptions import GiteaError

logger = logging.getLogger(__name__)


class GiteaClient(BaseServiceClient):
    """Client for interacting with Gitea API."""
    
    def __init__(self, config: Optional[GiteaConfig] = None):
        self.config = config or GiteaConfig()
        self.api_token = self.config.api_token
        super().__init__(self.config.base_url)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for Gitea API."""
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"
        return headers
    
    def _get_api_base_url(self) -> str:
        """Get Gitea API base URL."""
        return f"{self.base_url}/api/v1"
    
    def _get_ping_endpoint(self) -> str:
        """Get Gitea health check endpoint."""
        return "/api/v1/version"
    
    async def get_version(self) -> Optional[Dict[str, Any]]:
        """Get Gitea version information."""
        # This method doesn't use the session, so we handle it separately
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/version")
                if response.status_code == 200:
                    return response.json()
                else:
                    raise GiteaError(f"Failed to get version: HTTP {response.status_code}")
        except GiteaError:
            raise
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error in {self.__class__.__name__}.get_version(): {e}")
            raise GiteaError(f"HTTP error while getting version: {e}")
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout in {self.__class__.__name__}.get_version(): {e}")
            raise GiteaError(f"Timeout while getting version: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}.get_version(): {e}", exc_info=True)
            raise GiteaError(f"Unexpected error while getting version: {e}")
    
    async def get_repositories(self, page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        """Get list of repositories."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get(
                "/repos/search",
                params={"page": page, "limit": limit}
            ),
            "get_repositories",
            default_return={}
        )
        # Gitea returns {"data": [...]} format
        if isinstance(result, dict):
            return result.get("data", [])
        return []
    
    async def get_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Get repositories for a specific user."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get(f"/users/{username}/repos"),
            "get_user_repositories",
            default_return=[]
        )
        return result if isinstance(result, list) else []
    
    async def create_repository(self, name: str, description: str = "", private: bool = False) -> Optional[Dict[str, Any]]:
        """Create a new repository."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.post(
                "/user/repos",
                json={
                    "name": name,
                    "description": description,
                    "private": private
                }
            ),
            "create_repository",
            default_return=None,
            raise_on_error=True,
            exception_class=GiteaError
        )
        return result
    
    async def get_repository(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get(f"/repos/{owner}/{repo}"),
            "get_repository",
            default_return=None,
            raise_on_error=True,
            exception_class=GiteaError
        )
        return result


