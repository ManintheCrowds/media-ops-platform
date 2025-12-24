"""Gitea integration client."""

import httpx
from typing import Optional, Dict, Any
from app.config import settings


class GiteaClient:
    """Client for Gitea API integration."""
    
    def __init__(self):
        self.base_url = settings.gitea_url.rstrip('/')
        self.api_token = settings.gitea_api_token
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
    
    async def get_repository(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get a Gitea repository."""
        try:
            response = await self._session.get(f"/repos/{owner}/{repo}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def get_branch(self, owner: str, repo: str, branch: str) -> Optional[Dict[str, Any]]:
        """Get a specific branch of a repository."""
        try:
            response = await self._session.get(f"/repos/{owner}/{repo}/branches/{branch}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None







