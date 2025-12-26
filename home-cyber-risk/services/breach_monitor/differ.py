"""Differ component for detecting new and updated breaches."""

import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class BreachDiffer:
    """Compares new breaches against stored breaches to detect changes."""
    
    def diff(self, new_breaches: List[Dict[str, Any]], stored_breaches: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compare new breaches against stored breaches.
        
        Args:
            new_breaches: List of normalized breach dictionaries from current check
            stored_breaches: List of Breach objects from database
        
        Returns:
            Dictionary with keys: new_breaches, updated_breaches, unchanged_breaches
        """
        # Create lookup map of stored breaches
        stored_map = {}
        for stored in stored_breaches:
            key = (stored.identifier, stored.breach_name)
            stored_map[key] = stored
        
        new_list = []
        updated_list = []
        unchanged_list = []
        
        for new_breach in new_breaches:
            key = (new_breach["identifier"], new_breach["breach_name"])
            
            if key not in stored_map:
                # New breach
                new_list.append(new_breach)
            else:
                # Check if updated
                stored = stored_map[key]
                if self._is_updated(new_breach, stored):
                    updated_list.append({
                        "new": new_breach,
                        "old": self._breach_to_dict(stored)
                    })
                else:
                    unchanged_list.append(new_breach)
        
        logger.info(f"Diff results: {len(new_list)} new, {len(updated_list)} updated, {len(unchanged_list)} unchanged")
        
        return {
            "new_breaches": new_list,
            "updated_breaches": updated_list,
            "unchanged_breaches": unchanged_list
        }
    
    def _is_updated(self, new_breach: Dict[str, Any], stored_breach: Any) -> bool:
        """
        Check if breach has been updated.
        
        Args:
            new_breach: New breach data
            stored_breach: Stored breach object
        
        Returns:
            True if breach has been updated
        """
        # Check data classes
        new_data_classes = set(new_breach.get("data_classes", []))
        stored_data_classes = set(stored_breach.data_classes or [])
        if new_data_classes != stored_data_classes:
            return True
        
        # Check breach date
        new_date = new_breach.get("breach_date")
        stored_date = stored_breach.breach_date
        if new_date and stored_date:
            if isinstance(new_date, str):
                from dateutil import parser as date_parser
                new_date = date_parser.parse(new_date)
            if new_date != stored_date:
                return True
        
        # Check pwn count
        new_pwn_count = new_breach.get("pwn_count")
        if new_pwn_count and new_pwn_count != stored_breach.pwn_count:
            return True
        
        return False
    
    def _breach_to_dict(self, breach: Any) -> Dict[str, Any]:
        """Convert Breach object to dictionary."""
        return {
            "identifier": breach.identifier,
            "identifier_type": breach.identifier_type,
            "breach_name": breach.breach_name,
            "breach_date": breach.breach_date.isoformat() if breach.breach_date else None,
            "data_classes": breach.data_classes,
            "pwn_count": breach.pwn_count,
            "description": breach.description,
            "is_verified": breach.is_verified,
            "domain": breach.domain,
            "first_seen": breach.first_seen.isoformat() if breach.first_seen else None,
            "last_seen": breach.last_seen.isoformat() if breach.last_seen else None
        }
    
    def get_alertable_breaches(self, diff_result: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Get breaches that should trigger alerts.
        
        Args:
            diff_result: Result from diff() method
        
        Returns:
            List of breaches that need alerts (new + updated)
        """
        alertable = []
        
        # New breaches always need alerts
        alertable.extend(diff_result["new_breaches"])
        
        # Updated breaches need alerts if significant changes
        for updated in diff_result["updated_breaches"]:
            new_breach = updated["new"]
            # Alert if data classes changed (new data exposed)
            new_data_classes = set(new_breach.get("data_classes", []))
            old_data_classes = set(updated["old"].get("data_classes", []))
            if new_data_classes - old_data_classes:  # New data classes added
                alertable.append(new_breach)
        
        return alertable

