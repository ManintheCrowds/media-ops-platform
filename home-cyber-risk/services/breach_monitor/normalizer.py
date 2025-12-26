"""Normalizer component for standardizing breach data format."""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class BreachNormalizer:
    """Normalizes breach data from different sources to standard format."""
    
    def normalize(self, raw_breaches: List[Dict[str, Any]], identifier: str, identifier_type: str, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Normalize breach data to standard format.
        
        Args:
            raw_breaches: Raw breach data from API
            identifier: The identifier that was checked (email, username, etc.)
            identifier_type: Type of identifier (email, username, domain)
            source: Optional source name for tracking
        
        Returns:
            List of normalized breach dictionaries
        """
        normalized = []
        seen_breaches = set()  # For deduplication
        
        for breach in raw_breaches:
            try:
                normalized_breach = self._normalize_single(breach, identifier, identifier_type, source)
                
                # Deduplicate by breach name
                breach_key = (identifier, normalized_breach['breach_name'])
                if breach_key not in seen_breaches:
                    seen_breaches.add(breach_key)
                    normalized.append(normalized_breach)
                else:
                    logger.debug(f"Duplicate breach {normalized_breach['breach_name']} for {identifier}, skipping")
                    
            except Exception as e:
                logger.error(f"Error normalizing breach data: {e}, breach: {breach}")
                continue
        
        return normalized
    
    def _normalize_single(self, breach: Dict[str, Any], identifier: str, identifier_type: str, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Normalize a single breach record.
        
        Args:
            breach: Raw breach dictionary
            identifier: The identifier checked
            identifier_type: Type of identifier
            source: Optional source name
        
        Returns:
            Normalized breach dictionary
        """
        # Extract breach name
        breach_name = (
            breach.get("Name") or
            breach.get("name") or
            breach.get("breach_name") or
            "Unknown"
        )
        
        # Parse breach date
        breach_date = None
        date_str = (
            breach.get("BreachDate") or
            breach.get("breach_date") or
            breach.get("date")
        )
        if date_str:
            try:
                breach_date = date_parser.parse(str(date_str))
            except Exception as e:
                logger.warning(f"Could not parse breach date '{date_str}': {e}")
        
        # Extract data classes
        data_classes = breach.get("DataClasses") or breach.get("data_classes") or []
        if isinstance(data_classes, str):
            data_classes = [c.strip() for c in data_classes.split(',')]
        if not data_classes:
            data_classes = ["Email addresses"]  # Default
        
        # Extract other metadata
        pwn_count = breach.get("PwnCount") or breach.get("pwn_count")
        description = breach.get("Description") or breach.get("description")
        is_verified = breach.get("IsVerified", breach.get("is_verified", True))
        domain = breach.get("Domain") or breach.get("domain")
        
        # Extract source information
        breach_source = source or breach.get("_source") or breach.get("source") or "unknown"
        sources = breach.get("_sources") or breach.get("sources")
        if sources and isinstance(sources, list):
            if breach_source not in sources:
                sources.append(breach_source)
        elif sources and isinstance(sources, str):
            sources = [sources, breach_source] if sources != breach_source else [breach_source]
        else:
            sources = [breach_source]
        
        return {
            "identifier": identifier,
            "identifier_type": identifier_type,
            "breach_name": str(breach_name),
            "breach_date": breach_date,
            "data_classes": data_classes,
            "pwn_count": pwn_count,
            "description": description,
            "is_verified": is_verified,
            "domain": domain,
            "source": breach_source,
            "sources": sources,
            "raw_data": breach  # Keep original for reference
        }
    
    def validate(self, normalized_breach: Dict[str, Any]) -> bool:
        """
        Validate normalized breach data structure.
        
        Args:
            normalized_breach: Normalized breach dictionary
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["identifier", "identifier_type", "breach_name"]
        
        for field in required_fields:
            if field not in normalized_breach:
                logger.error(f"Missing required field '{field}' in normalized breach")
                return False
        
        if not normalized_breach["breach_name"]:
            logger.error("Breach name cannot be empty")
            return False
        
        return True

