"""Multi-source breach aggregator."""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class BreachAggregator:
    """Aggregates breach results from multiple sources."""
    
    def aggregate_results(self, source_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Aggregate results from multiple sources.
        
        Args:
            source_results: Dictionary mapping source names to breach lists
                Example: {"hibp": [...], "public_db": [...], "paste": [...]}
        
        Returns:
            Aggregated and deduplicated list of breaches
        """
        # Group breaches by identifier and breach name
        breach_groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
        
        # Collect all breaches with source information
        for source_name, breaches in source_results.items():
            for breach in breaches:
                # Extract key fields for grouping
                identifier = breach.get("identifier") or breach.get("_identifier") or ""
                breach_name = breach.get("breach_name") or breach.get("Name") or breach.get("name") or "Unknown"
                
                key = (identifier.lower(), breach_name.lower())
                
                # Add source to breach
                if "_source" not in breach:
                    breach["_source"] = source_name
                if "_sources" not in breach:
                    breach["_sources"] = [source_name]
                else:
                    if source_name not in breach["_sources"]:
                        breach["_sources"].append(source_name)
                
                breach_groups[key].append(breach)
        
        # Deduplicate and merge
        aggregated = []
        for key, breaches in breach_groups.items():
            merged_breach = self._merge_breaches(breaches)
            aggregated.append(merged_breach)
        
        logger.info(f"Aggregated {len(aggregated)} unique breaches from {len(source_results)} sources")
        
        return aggregated
    
    def _merge_breaches(self, breaches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple breach records for the same breach from different sources.
        
        Args:
            breaches: List of breach dictionaries for the same breach
        
        Returns:
            Merged breach dictionary
        """
        if len(breaches) == 1:
            return breaches[0]
        
        # Start with first breach as base
        merged = breaches[0].copy()
        
        # Collect all sources
        all_sources = set()
        for breach in breaches:
            if "_source" in breach:
                all_sources.add(breach["_source"])
            if "_sources" in breach:
                all_sources.update(breach["_sources"])
        
        merged["_sources"] = list(all_sources)
        
        # Merge data classes (union)
        all_data_classes = set()
        for breach in breaches:
            data_classes = breach.get("data_classes") or breach.get("DataClasses") or []
            if isinstance(data_classes, str):
                data_classes = [c.strip() for c in data_classes.split(',')]
            all_data_classes.update(data_classes)
        
        if "data_classes" in merged:
            merged["data_classes"] = list(all_data_classes)
        elif "DataClasses" in merged:
            merged["DataClasses"] = list(all_data_classes)
        
        # Use most recent breach date
        dates = []
        for breach in breaches:
            date = breach.get("breach_date") or breach.get("BreachDate")
            if date:
                dates.append(date)
        
        if dates:
            # Keep the most recent date
            merged["breach_date"] = max(dates) if dates else None
            if "BreachDate" in merged:
                merged["BreachDate"] = merged["breach_date"]
        
        # Use highest pwn count
        pwn_counts = [b.get("pwn_count") or b.get("PwnCount") for b in breaches if b.get("pwn_count") or b.get("PwnCount")]
        if pwn_counts:
            merged["pwn_count"] = max(pwn_counts)
            if "PwnCount" in merged:
                merged["PwnCount"] = merged["pwn_count"]
        
        # Merge descriptions (prefer longer/more detailed)
        descriptions = [b.get("description") or b.get("Description") for b in breaches if b.get("description") or b.get("Description")]
        if descriptions:
            # Use longest description
            merged["description"] = max(descriptions, key=len)
            if "Description" in merged:
                merged["Description"] = merged["description"]
        
        # Verification: if any source says verified, mark as verified
        is_verified = any(b.get("is_verified", b.get("IsVerified", True)) for b in breaches)
        merged["is_verified"] = is_verified
        if "IsVerified" in merged:
            merged["IsVerified"] = is_verified
        
        # Calculate confidence based on number of sources
        merged["confidence"] = self.calculate_confidence(len(all_sources))
        
        return merged
    
    def calculate_confidence(self, source_count: int) -> float:
        """
        Calculate confidence score based on number of sources confirming breach.
        
        Args:
            source_count: Number of sources that found this breach
        
        Returns:
            Confidence score (0.0-1.0)
        """
        if source_count == 0:
            return 0.0
        elif source_count == 1:
            return 0.6  # Single source = moderate confidence
        elif source_count == 2:
            return 0.8  # Two sources = high confidence
        else:
            return 1.0  # Three+ sources = very high confidence
    
    def deduplicate_breaches(self, breaches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate breaches by identifier and breach name.
        
        Args:
            breaches: List of breach dictionaries
        
        Returns:
            Deduplicated list
        """
        seen = set()
        deduplicated = []
        
        for breach in breaches:
            identifier = breach.get("identifier") or breach.get("_identifier") or ""
            breach_name = breach.get("breach_name") or breach.get("Name") or breach.get("name") or "Unknown"
            
            key = (identifier.lower(), breach_name.lower())
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(breach)
        
        return deduplicated

