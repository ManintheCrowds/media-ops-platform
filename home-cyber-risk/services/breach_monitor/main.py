"""Main breach monitoring service."""

import asyncio
import logging
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from .fetcher import HIBPFetcher
from .fetcher_public import PublicBreachFetcher
from .fetcher_paste import PasteSiteFetcher
from .fetcher_pwdb import PwdbPublicFetcher
from .normalizer import BreachNormalizer
from .storage import BreachStorage
from .differ import BreachDiffer
from .notifier import NotifierManager
from .risk_scorer import RiskScorer
from .aggregator import BreachAggregator
from .logging_config import setup_logging

# Load environment variables
load_dotenv()

# Configure logging with Loki integration
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    loki_url=os.getenv("LOKI_URL")
)
logger = logging.getLogger(__name__)


class BreachMonitor:
    """Main breach monitoring service."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize breach monitor.
        
        Args:
            dry_run: If True, don't store data or send alerts
        """
        self.dry_run = dry_run
        self.api_key = os.getenv("HIBP_API_KEY")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///data/breaches.db")
        
        # Initialize multiple fetchers
        self.fetchers = []
        
        # HIBP fetcher (always available, but may not have API key)
        self.fetchers.append(HIBPFetcher(api_key=self.api_key))
        
        # Public breach database fetcher (if enabled) - now API-based
        if os.getenv("ENABLE_PUBLIC_BREACH_DB", "true").lower() == "true":
            self.fetchers.append(PublicBreachFetcher())
        
        # Pwdb-Public fetcher (if enabled)
        if os.getenv("ENABLE_PWDB_PUBLIC", "true").lower() == "true":
            github_token = os.getenv("GITHUB_TOKEN")  # Optional, but recommended for rate limits
            self.fetchers.append(PwdbPublicFetcher(github_token=github_token))
        
        # Paste site fetcher (if enabled)
        if os.getenv("ENABLE_PASTE_MONITORING", "true").lower() == "true":
            github_token = os.getenv("GITHUB_TOKEN")  # Optional
            self.fetchers.append(PasteSiteFetcher(github_token=github_token))
        
        # Initialize other components
        self.normalizer = BreachNormalizer()
        self.storage = BreachStorage(self.database_url)
        self.differ = BreachDiffer()
        self.notifier = NotifierManager()
        self.risk_scorer = RiskScorer()
        self.aggregator = BreachAggregator()
        
        logger.info(f"Breach monitor initialized (dry_run={dry_run}, {len(self.fetchers)} fetchers)")
        
        # Log fetcher health status
        for fetcher in self.fetchers:
            health = fetcher.get_health_status()
            logger.debug(f"Fetcher {health['source']} initialized (healthy: {health['is_healthy']})")
    
    def load_identifiers(self, config_path: str = "config/identifiers.yml") -> Dict[str, Any]:
        """
        Load identifiers from configuration file.
        
        Args:
            config_path: Path to identifiers YAML file
        
        Returns:
            Dictionary with emails, usernames, domains lists
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Identifiers file not found: {config_path}")
            return {"emails": [], "usernames": [], "domains": []}
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            return {
                "emails": config.get("emails", []),
                "usernames": config.get("usernames", []),
                "domains": config.get("domains", []),
                "metadata": config.get("metadata", {})
            }
        except Exception as e:
            logger.error(f"Error loading identifiers: {e}")
            return {"emails": [], "usernames": [], "domains": []}
    
    async def check_identifier(self, identifier: str, identifier_type: str) -> Dict[str, Any]:
        """
        Check a single identifier for breaches.
        
        Args:
            identifier: Email, username, or domain to check
            identifier_type: Type of identifier (email, username, domain)
        
        Returns:
            Dictionary with check results
        """
        logger.info(f"Checking {identifier_type}: {identifier}")
        
        try:
            # Fetch breaches from all sources
            source_results = {}
            
            for fetcher in self.fetchers:
                try:
                    if identifier_type == "email":
                        raw_breaches = await fetcher.check_email(identifier)
                    elif identifier_type == "username":
                        raw_breaches = await fetcher.check_username(identifier)
                    else:
                        continue
                    
                    if raw_breaches:
                        source_results[fetcher.source_name] = raw_breaches
                        logger.debug(f"Found {len(raw_breaches)} breaches from {fetcher.source_name}")
                except Exception as e:
                    logger.warning(f"Error fetching from {fetcher.source_name}: {e}")
                    continue
            
            # Normalize breaches from each source first
            all_normalized = []
            for source_name, raw_breaches in source_results.items():
                normalized = self.normalizer.normalize(raw_breaches, identifier, identifier_type, source=source_name)
                all_normalized.extend(normalized)
            
            # Aggregate normalized breaches from all sources
            if all_normalized:
                # Group by breach name for aggregation
                source_results_normalized = {}
                for breach in all_normalized:
                    source = breach.get("source", "unknown")
                    if source not in source_results_normalized:
                        source_results_normalized[source] = []
                    source_results_normalized[source].append(breach)
                
                aggregated_breaches = self.aggregator.aggregate_results(source_results_normalized)
            else:
                aggregated_breaches = []
            
            # Apply risk scoring
            scored_breaches = []
            for breach in aggregated_breaches:
                scored = self.risk_scorer.score_breach(breach)
                scored_breaches.append(scored)
            
            normalized_breaches = scored_breaches
            
            # Get stored breaches
            stored_breaches = self.storage.get_breaches(identifier=identifier, identifier_type=identifier_type)
            
            # Diff to find new/updated breaches
            diff_result = self.differ.diff(normalized_breaches, stored_breaches)
            
            # Store new breaches (if not dry run)
            if not self.dry_run:
                all_breaches = diff_result["new_breaches"] + [
                    b["new"] for b in diff_result["updated_breaches"]
                ]
                if all_breaches:
                    store_result = self.storage.store_breaches(all_breaches)
                    logger.info(f"Stored breaches: {store_result}")
                
                # Record check history
                self.storage.record_check(
                    identifier=identifier,
                    identifier_type=identifier_type,
                    breaches_found=len(normalized_breaches),
                    new_breaches=len(diff_result["new_breaches"]),
                    updated_breaches=len(diff_result["updated_breaches"]),
                    success=True
                )
            
            # Get alertable breaches
            alertable = self.differ.get_alertable_breaches(diff_result)
            
            # Send alerts (if not dry run and there are alertable breaches)
            alert_results = {}
            if not self.dry_run and alertable:
                alert_results = self.notifier.send_alert(alertable, identifier)
                logger.info(f"Alert results: {alert_results}")
            
            return {
                "success": True,
                "identifier": identifier,
                "identifier_type": identifier_type,
                "total_breaches": len(normalized_breaches),
                "new_breaches": len(diff_result["new_breaches"]),
                "updated_breaches": len(diff_result["updated_breaches"]),
                "alertable_breaches": len(alertable),
                "alert_results": alert_results,
                "dry_run": self.dry_run
            }
            
        except Exception as e:
            logger.error(f"Error checking {identifier}: {e}", exc_info=True)
            
            # Record failed check
            if not self.dry_run:
                self.storage.record_check(
                    identifier=identifier,
                    identifier_type=identifier_type,
                    breaches_found=0,
                    new_breaches=0,
                    updated_breaches=0,
                    success=False,
                    error_message=str(e)
                )
            
            return {
                "success": False,
                "identifier": identifier,
                "identifier_type": identifier_type,
                "error": str(e)
            }
    
    async def run_check(self, config_path: str = "config/identifiers.yml") -> Dict[str, Any]:
        """
        Run breach check for all configured identifiers.
        
        Args:
            config_path: Path to identifiers configuration file
        
        Returns:
            Dictionary with overall check results
        """
        logger.info("Starting breach check")
        
        identifiers = self.load_identifiers(config_path)
        
        results = {
            "emails": [],
            "usernames": [],
            "domains": [],
            "summary": {
                "total_checked": 0,
                "total_breaches": 0,
                "new_breaches": 0,
                "updated_breaches": 0,
                "successful_checks": 0,
                "failed_checks": 0
            }
        }
        
        # Check emails
        for email in identifiers["emails"]:
            result = await self.check_identifier(email, "email")
            results["emails"].append(result)
            if result["success"]:
                results["summary"]["successful_checks"] += 1
                results["summary"]["total_breaches"] += result.get("total_breaches", 0)
                results["summary"]["new_breaches"] += result.get("new_breaches", 0)
                results["summary"]["updated_breaches"] += result.get("updated_breaches", 0)
            else:
                results["summary"]["failed_checks"] += 1
            results["summary"]["total_checked"] += 1
        
        # Check usernames
        for username in identifiers["usernames"]:
            result = await self.check_identifier(username, "username")
            results["usernames"].append(result)
            if result["success"]:
                results["summary"]["successful_checks"] += 1
                results["summary"]["total_breaches"] += result.get("total_breaches", 0)
                results["summary"]["new_breaches"] += result.get("new_breaches", 0)
                results["summary"]["updated_breaches"] += result.get("updated_breaches", 0)
            else:
                results["summary"]["failed_checks"] += 1
            results["summary"]["total_checked"] += 1
        
        # Domains are not directly checkable via HIBP API
        # They would need to be checked via domain breach API (paid feature)
        # For now, we'll skip domain checking or implement separately
        
        logger.info(f"Breach check complete: {results['summary']}")
        
        # Log fetcher health status after check
        health_status = {}
        for fetcher in self.fetchers:
            health = fetcher.get_health_status()
            health_status[health['source']] = {
                'success_rate': health['success_rate'],
                'is_healthy': health['is_healthy'],
                'last_error': health['last_error']
            }
        results['fetcher_health'] = health_status
        logger.info(f"Fetcher health: {health_status}")
        
        return results


async def main():
    """Main entry point."""
    import sys
    
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    config_path = "config/identifiers.yml"
    
    # Allow config path override
    if "--config" in sys.argv:
        idx = sys.argv.index("--config")
        if idx + 1 < len(sys.argv):
            config_path = sys.argv[idx + 1]
    
    monitor = BreachMonitor(dry_run=dry_run)
    results = await monitor.run_check(config_path)
    
    # Print summary
    print("\n" + "="*70)
    print("Breach Check Summary")
    print("="*70)
    print(f"Total checked: {results['summary']['total_checked']}")
    print(f"Successful: {results['summary']['successful_checks']}")
    print(f"Failed: {results['summary']['failed_checks']}")
    print(f"Total breaches: {results['summary']['total_breaches']}")
    print(f"New breaches: {results['summary']['new_breaches']}")
    print(f"Updated breaches: {results['summary']['updated_breaches']}")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())

