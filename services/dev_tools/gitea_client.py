"""Gitea API client."""

import httpx
from typing import Optional, Dict, List, Any
from services.dev_tools.config import GiteaConfig


class GiteaClient:
    """Client for interacting with Gitea API."""
    
    def __init__(self, config: Optional[GiteaConfig] = None):
        self.config = config or GiteaConfig()
        self.base_url = self.config.base_url.rstrip('/')
        self.api_token = self.config.api_token
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"
        
        self._session = httpx.AsyncClient(
            base_url=f"{self.base_url}/api/v1",
            timeout=30.0,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()
    
    async def ping(self) -> bool:
        """Check if Gitea is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/version")
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_version(self) -> Optional[Dict[str, Any]]:
        """Get Gitea version information."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/version")
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None
    
    async def get_repositories(self, page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        """Get list of repositories."""
        if not self._session:
            async with self:
                return await self.get_repositories(page, limit)
        
        try:
            response = await self._session.get(
                "/repos/search",
                params={"page": page, "limit": limit}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
        except Exception:
            pass
        return []
    
    async def get_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Get repositories for a specific user."""
        if not self._session:
            async with self:
                return await self.get_user_repositories(username)
        
        try:
            response = await self._session.get(f"/users/{username}/repos")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []
    
    async def create_repository(self, name: str, description: str = "", private: bool = False) -> Optional[Dict[str, Any]]:
        """Create a new repository."""
        if not self._session:
            async with self:
                return await self.create_repository(name, description, private)
        
        try:
            response = await self._session.post(
                "/user/repos",
                json={
                    "name": name,
                    "description": description,
                    "private": private
                }
            )
            if response.status_code == 201:
                return response.json()
        except Exception:
            pass
        return None
    
    async def get_repository(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        if not self._session:
            async with self:
                return await self.get_repository(owner, repo)
        
        try:
            response = await self._session.get(f"/repos/{owner}/{repo}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None


