"""Fetcher for public breach databases (free sources) - API-based."""

import logging
import json
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode
from .fetcher_base import BaseFetcher

logger = logging.getLogger(__name__)


class PublicBreachFetcher(BaseFetcher):
    """Fetches breach data from public breach database APIs."""
    
    # Public breach database API endpoints
    # Format: {"name": "source_name", "url": "api_url_template", "method": "get|post"}
    # URL template can use {identifier} placeholder
    PUBLIC_API_SOURCES = [
        # Add public breach database API endpoints here
        # Example:
        # {
        #     "name": "example_api",
        #     "url": "https://api.example.com/breach/{identifier}",
        #     "method": "get"
        # }
    ]
    
    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "public_db"
    
    def __init__(self, rate_limit_delay: float = 1.0):
        """
        Initialize public breach fetcher.
        
        Args:
            rate_limit_delay: Delay between requests (default 1s for free sources)
        """
        super().__init__(rate_limit_delay=rate_limit_delay)
    
    async def _query_api(self, api_config: Dict[str, str], identifier: str) -> Optional[List[Dict[str, Any]]]:
        """
        Query a public breach API for an identifier.
        
        Args:
            api_config: API configuration dict with url, method, etc.
            identifier: Email or username to check
        
        Returns:
            List of breach records or None if failed
        """
        try:
            url_template = api_config.get("url", "")
            method = api_config.get("method", "get").lower()
            
            # Replace identifier placeholder in URL
            url = url_template.replace("{identifier}", identifier)
            
            # Add query params if specified
            if "params" in api_config:
                params = {k: v.replace("{identifier}", identifier) for k, v in api_config["params"].items()}
                url = f"{url}?{urlencode(params)}"
            
            result = await self._make_request(url, headers=api_config.get("headers"), timeout=60.0)
            if result is None:
                return None
            
            # Try to parse as JSON
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    # Try CSV
                    return self._parse_csv(result)
            
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                # If it's a dict, try to extract a list
                for key in ['breaches', 'data', 'records', 'results']:
                    if key in result and isinstance(result[key], list):
                        return result[key]
                # If it's a single breach record
                if 'name' in result or 'breach_name' in result:
                    return [result]
            
            return None
        except Exception as e:
            logger.error(f"Error querying API {api_config.get('name', 'unknown')}: {e}")
            return None
    
    def _parse_csv(self, csv_text: str) -> List[Dict[str, Any]]:
        """
        Parse CSV breach data.
        
        Args:
            csv_text: CSV text content
        
        Returns:
            List of breach dictionaries
        """
        breaches = []
        try:
            reader = csv.DictReader(csv_text.splitlines())
            for row in reader:
                # Normalize CSV row to breach format
                breach = {
                    "name": row.get("name") or row.get("breach_name") or "Unknown",
                    "breach_date": row.get("breach_date") or row.get("date"),
                    "data_classes": row.get("data_classes", "").split(",") if row.get("data_classes") else [],
                    "description": row.get("description") or "",
                    "pwn_count": int(row.get("pwn_count", 0)) if row.get("pwn_count") else None
                }
                breaches.append(breach)
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
        
        return breaches
    
    
    async def check_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Check if email has been breached in public databases via API calls.
        
        Args:
            email: Email address to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        if not self.PUBLIC_API_SOURCES:
            logger.debug("No public API sources configured")
            return []
        
        all_breaches = []
        email_lower = email.lower()
        
        # Query each configured API source
        for api_config in self.PUBLIC_API_SOURCES:
            try:
                breaches = await self._query_api(api_config, email_lower)
                if breaches:
                    # Normalize each breach
                    for breach in breaches:
                        normalized = self._normalize_breach(breach, email, "email")
                        all_breaches.append(normalized)
                    logger.debug(f"Found {len(breaches)} breaches from {api_config.get('name', 'unknown')}")
            except Exception as e:
                logger.warning(f"Error checking email in {api_config.get('name', 'unknown')}: {e}")
                continue
        
        return all_breaches
    
    async def check_username(self, username: str) -> List[Dict[str, Any]]:
        """
        Check if username has been breached in public databases via API calls.
        
        Args:
            username: Username to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        if not self.PUBLIC_API_SOURCES:
            logger.debug("No public API sources configured")
            return []
        
        all_breaches = []
        username_lower = username.lower()
        
        # Query each configured API source
        for api_config in self.PUBLIC_API_SOURCES:
            try:
                breaches = await self._query_api(api_config, username_lower)
                if breaches:
                    # Normalize each breach
                    for breach in breaches:
                        normalized = self._normalize_breach(breach, username, "username")
                        all_breaches.append(normalized)
                    logger.debug(f"Found {len(breaches)} breaches from {api_config.get('name', 'unknown')}")
            except Exception as e:
                logger.warning(f"Error checking username in {api_config.get('name', 'unknown')}: {e}")
                continue
        
        return all_breaches
    
    def _normalize_breach(self, breach: Dict[str, Any], identifier: str, identifier_type: str) -> Dict[str, Any]:
        """
        Normalize breach record to standard format.
        
        Args:
            breach: Raw breach record
            identifier: Identifier that was checked
            identifier_type: Type of identifier
        
        Returns:
            Normalized breach dictionary
        """
        # Parse date if present
        breach_date = None
        date_str = breach.get("breach_date") or breach.get("date")
        if date_str:
            try:
                from dateutil import parser as date_parser
                breach_date = date_parser.parse(str(date_str))
            except Exception:
                pass
        
        # Extract data classes
        data_classes = breach.get("data_classes", [])
        if isinstance(data_classes, str):
            data_classes = [c.strip() for c in data_classes.split(',')]
        if not data_classes:
            data_classes = ["Email addresses", "Usernames"]
        
        return {
            "Name": breach.get("name") or breach.get("breach_name") or "Unknown",
            "BreachDate": breach_date.isoformat() if breach_date else None,
            "DataClasses": data_classes,
            "Description": breach.get("description") or "",
            "PwnCount": breach.get("pwn_count") or breach.get("count"),
            "IsVerified": breach.get("is_verified", True),
            "Domain": breach.get("domain"),
            # Add source identifier
            "_source": self.source_name,
            "_identifier": identifier,
            "_identifier_type": identifier_type
        }

