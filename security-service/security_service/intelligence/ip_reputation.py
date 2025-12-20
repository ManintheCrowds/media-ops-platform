"""IP reputation service."""

import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.threats import ThreatIntelligence
from ..config import config


class IPReputationService:
    """IP reputation checking with threat intelligence feeds."""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_ttl = timedelta(hours=24)
        
    async def check_ip_reputation(self, ip_address: str, force_refresh: bool = False) -> ThreatIntelligence:
        """Check IP reputation from threat intelligence feeds."""
        # Check cache first
        if not force_refresh:
            cached = self.db.query(ThreatIntelligence).filter(
                ThreatIntelligence.ip_address == ip_address
            ).first()
            
            if cached and cached.updated_at > datetime.now(timezone.utc) - self.cache_ttl:
                return cached
        
        # Query threat intelligence feeds
        reputation_data = await self._query_threat_feeds(ip_address)
        
        # Store or update in database
        threat_intel = self.db.query(ThreatIntelligence).filter(
            ThreatIntelligence.ip_address == ip_address
        ).first()
        
        if threat_intel:
            # Update existing
            threat_intel.reputation_score = reputation_data["score"]
            threat_intel.confidence_level = reputation_data["confidence"]
            threat_intel.threat_categories = reputation_data.get("categories", [])
            threat_intel.is_malicious = "true" if reputation_data["score"] < 50 else "false"
            threat_intel.source = reputation_data["source"]
            threat_intel.country = reputation_data.get("country")
            threat_intel.asn = reputation_data.get("asn")
            threat_intel.isp = reputation_data.get("isp")
            threat_intel.last_seen = datetime.now(timezone.utc)
            threat_intel.updated_at = datetime.now(timezone.utc)
            threat_intel.metadata = reputation_data.get("metadata", {})
        else:
            # Create new
            threat_intel = ThreatIntelligence(
                ip_address=ip_address,
                reputation_score=reputation_data["score"],
                confidence_level=reputation_data["confidence"],
                threat_categories=reputation_data.get("categories", []),
                is_malicious="true" if reputation_data["score"] < 50 else "false",
                source=reputation_data["source"],
                country=reputation_data.get("country"),
                asn=reputation_data.get("asn"),
                isp=reputation_data.get("isp"),
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                metadata=reputation_data.get("metadata", {})
            )
            self.db.add(threat_intel)
        
        self.db.commit()
        self.db.refresh(threat_intel)
        
        return threat_intel
    
    async def _query_threat_feeds(self, ip_address: str) -> Dict[str, Any]:
        """Query threat intelligence feeds."""
        results = []
        
        # Query AbuseIPDB
        if config.abuseipdb_api_key:
            abuseipdb_result = await self._query_abuseipdb(ip_address)
            if abuseipdb_result:
                results.append(abuseipdb_result)
        
        # Query VirusTotal
        if config.virustotal_api_key:
            virustotal_result = await self._query_virustotal(ip_address)
            if virustotal_result:
                results.append(virustotal_result)
        
        # Aggregate results
        if results:
            return self._aggregate_results(results)
        else:
            # Default: unknown reputation
            return {
                "score": 50,  # Neutral
                "confidence": "low",
                "categories": [],
                "source": "internal",
                "metadata": {}
            }
    
    async def _query_abuseipdb(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Query AbuseIPDB API."""
        if not config.abuseipdb_api_key:
            return None
        
        try:
            url = "https://api.abuseipdb.com/api/v2/check"
            headers = {
                "Key": config.abuseipdb_api_key,
                "Accept": "application/json"
            }
            params = {
                "ipAddress": ip_address,
                "maxAgeInDays": 90,
                "verbose": ""
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data:
                        abuse_data = data["data"]
                        abuse_score = abuse_data.get("abuseConfidencePercentage", 0)
                        reputation_score = 100 - abuse_score  # Convert to reputation (0-100)
                        
                        return {
                            "score": reputation_score,
                            "confidence": "high" if abuse_score > 50 else "medium",
                            "categories": abuse_data.get("usageType", "").split(",") if abuse_data.get("usageType") else [],
                            "source": "abuseipdb",
                            "country": abuse_data.get("countryCode"),
                            "isp": abuse_data.get("isp"),
                            "metadata": abuse_data
                        }
        except Exception as e:
            print(f"AbuseIPDB query failed: {e}")
        
        return None
    
    async def _query_virustotal(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Query VirusTotal API."""
        if not config.virustotal_api_key:
            return None
        
        try:
            url = f"https://www.virustotal.com/vtapi/v2/ip-address/report"
            params = {
                "apikey": config.virustotal_api_key,
                "ip": ip_address
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("response_code") == 1:
                        detections = data.get("detected_urls", [])
                        detection_count = len(detections)
                        
                        # Calculate reputation score
                        if detection_count == 0:
                            reputation_score = 100
                        elif detection_count < 3:
                            reputation_score = 75
                        elif detection_count < 10:
                            reputation_score = 50
                        else:
                            reputation_score = 25
                        
                        return {
                            "score": reputation_score,
                            "confidence": "high" if detection_count > 0 else "medium",
                            "categories": [],
                            "source": "virustotal",
                            "country": data.get("as_owner"),
                            "metadata": data
                        }
        except Exception as e:
            print(f"VirusTotal query failed: {e}")
        
        return None
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple threat intelligence sources."""
        if not results:
            return {
                "score": 50,
                "confidence": "low",
                "categories": [],
                "source": "aggregated",
                "metadata": {}
            }
        
        # Weighted average of scores
        total_score = 0
        total_weight = 0
        all_categories = []
        sources = []
        
        for result in results:
            weight = 1.0 if result["confidence"] == "high" else 0.5
            total_score += result["score"] * weight
            total_weight += weight
            all_categories.extend(result.get("categories", []))
            sources.append(result["source"])
        
        avg_score = total_score / total_weight if total_weight > 0 else 50
        
        # Determine overall confidence
        confidences = [r["confidence"] for r in results]
        if "high" in confidences:
            overall_confidence = "high"
        elif "medium" in confidences:
            overall_confidence = "medium"
        else:
            overall_confidence = "low"
        
        return {
            "score": avg_score,
            "confidence": overall_confidence,
            "categories": list(set(all_categories)),
            "source": ",".join(sources),
            "metadata": {"sources": sources, "result_count": len(results)}
        }


