"""Breach data downloader from public sources."""

import httpx
import csv
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import asyncio

from ..config import config

logger = logging.getLogger(__name__)


class BreachDataDownloader:
    """Download and parse breach data from public sources."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or config.breach_data_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sources = config.public_breach_sources or []
    
    async def download_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Download breach data from a URL.
        
        Args:
            url: URL to download from
        
        Returns:
            Dictionary with breach data or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers={"user-agent": "Security-Service/1.0"})
                
                if response.status_code == 200:
                    # Determine format from content type or URL
                    content_type = response.headers.get("content-type", "").lower()
                    
                    if "json" in content_type or url.endswith(".json"):
                        return {"format": "json", "data": response.json(), "source": url}
                    elif "csv" in content_type or url.endswith(".csv"):
                        return {"format": "csv", "data": response.text, "source": url}
                    else:
                        # Try to parse as text/plain (one email per line)
                        return {"format": "text", "data": response.text, "source": url}
                else:
                    logger.error(f"Failed to download from {url}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading from {url}: {e}")
            return None
    
    async def download_from_github(self, repo: str, path: str, branch: str = "main") -> Optional[Dict[str, Any]]:
        """
        Download breach data from GitHub repository.
        
        Args:
            repo: Repository in format "owner/repo"
            path: Path to file in repository
            branch: Branch name (default: main)
        
        Returns:
            Dictionary with breach data or None if failed
        """
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
        return await self.download_from_url(url)
    
    def parse_json_breach_data(self, data: Any, source: str) -> List[Dict[str, Any]]:
        """Parse JSON breach data into standardized format."""
        breaches = []
        
        try:
            if isinstance(data, list):
                for item in data:
                    breach = self._normalize_breach_data(item, source)
                    if breach:
                        breaches.append(breach)
            elif isinstance(data, dict):
                # Handle different JSON structures
                if "breaches" in data:
                    for item in data["breaches"]:
                        breach = self._normalize_breach_data(item, source)
                        if breach:
                            breaches.append(breach)
                elif "emails" in data:
                    # Email list format
                    for email in data["emails"]:
                        breach = self._normalize_breach_data({"email": email, "source": source}, source)
                        if breach:
                            breaches.append(breach)
                else:
                    # Single breach object
                    breach = self._normalize_breach_data(data, source)
                    if breach:
                        breaches.append(breach)
        except Exception as e:
            logger.error(f"Error parsing JSON breach data: {e}")
        
        return breaches
    
    def parse_csv_breach_data(self, csv_text: str, source: str) -> List[Dict[str, Any]]:
        """Parse CSV breach data into standardized format."""
        breaches = []
        
        try:
            # Try to detect delimiter
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(csv_text[:1024]).delimiter
            
            reader = csv.DictReader(csv_text.splitlines(), delimiter=delimiter)
            for row in reader:
                breach = self._normalize_breach_data(row, source)
                if breach:
                    breaches.append(breach)
        except Exception as e:
            logger.error(f"Error parsing CSV breach data: {e}")
        
        return breaches
    
    def parse_text_breach_data(self, text: str, source: str, breach_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse text breach data (one email per line) into standardized format."""
        breaches = []
        
        try:
            for line in text.strip().split('\n'):
                line = line.strip()
                if line and '@' in line:
                    # Assume it's an email address
                    email = line.split()[0]  # Take first word (email)
                    if '@' in email:
                        breach = {
                            "email": email.lower(),
                            "breach_name": breach_name or source,
                            "source": source,
                            "breach_date": None,
                            "data_classes": ["Email addresses"],
                            "is_verified": False
                        }
                        breaches.append(breach)
        except Exception as e:
            logger.error(f"Error parsing text breach data: {e}")
        
        return breaches
    
    def _normalize_breach_data(self, data: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        """Normalize breach data from various formats to standard format."""
        try:
            # Extract email
            email = (
                data.get("email") or
                data.get("Email") or
                data.get("email_address") or
                data.get("EmailAddress") or
                ""
            ).lower().strip()
            
            if not email or '@' not in email:
                return None
            
            # Extract breach name
            breach_name = (
                data.get("breach_name") or
                data.get("BreachName") or
                data.get("breach") or
                data.get("Breach") or
                data.get("name") or
                data.get("Name") or
                source.split('/')[-1]  # Use filename as fallback
            )
            
            # Extract breach date
            breach_date = None
            date_str = (
                data.get("breach_date") or
                data.get("BreachDate") or
                data.get("date") or
                data.get("Date")
            )
            if date_str:
                try:
                    from dateutil import parser
                    breach_date = parser.parse(str(date_str))
                except:
                    pass
            
            # Extract data classes
            data_classes = data.get("data_classes") or data.get("DataClasses") or []
            if isinstance(data_classes, str):
                data_classes = [c.strip() for c in data_classes.split(',')]
            if not data_classes:
                data_classes = ["Email addresses"]  # Default
            
            return {
                "email": email,
                "breach_name": str(breach_name),
                "breach_date": breach_date.isoformat() if breach_date else None,
                "data_classes": data_classes,
                "source": source,
                "is_verified": data.get("is_verified", data.get("IsVerified", False)),
                "pwn_count": data.get("pwn_count") or data.get("PwnCount"),
                "description": data.get("description") or data.get("Description"),
                "metadata": data
            }
        except Exception as e:
            logger.error(f"Error normalizing breach data: {e}")
            return None
    
    async def download_all_sources(self) -> List[Dict[str, Any]]:
        """Download breach data from all configured sources."""
        all_breaches = []
        
        for source in self.sources:
            try:
                logger.info(f"Downloading breach data from: {source}")
                
                # Check if it's a GitHub URL
                if "github.com" in source or "raw.githubusercontent.com" in source:
                    # Parse GitHub URL
                    if "raw.githubusercontent.com" in source:
                        # Already a raw URL
                        result = await self.download_from_url(source)
                    else:
                        # Convert to raw URL format
                        # Format: https://github.com/owner/repo/blob/branch/path
                        # Convert to: https://raw.githubusercontent.com/owner/repo/branch/path
                        url_parts = source.replace("/blob/", "/").replace("github.com", "raw.githubusercontent.com")
                        result = await self.download_from_url(url_parts)
                else:
                    result = await self.download_from_url(source)
                
                if result:
                    # Parse based on format
                    if result["format"] == "json":
                        breaches = self.parse_json_breach_data(result["data"], result["source"])
                    elif result["format"] == "csv":
                        breaches = self.parse_csv_breach_data(result["data"], result["source"])
                    else:
                        breaches = self.parse_text_breach_data(result["data"], result["source"])
                    
                    all_breaches.extend(breaches)
                    logger.info(f"Downloaded {len(breaches)} breach records from {source}")
                
                # Rate limiting between sources
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error downloading from source {source}: {e}")
        
        logger.info(f"Total breaches downloaded: {len(all_breaches)}")
        return all_breaches
    
    def save_to_cache(self, breaches: List[Dict[str, Any]], filename: str) -> Path:
        """Save breach data to cache file."""
        cache_file = self.cache_dir / filename
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file, 'w') as f:
            json.dump(breaches, f, indent=2, default=str)
        
        return cache_file
    
    def load_from_cache(self, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Load breach data from cache file."""
        cache_file = self.cache_dir / filename
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache file {filename}: {e}")
        return None

