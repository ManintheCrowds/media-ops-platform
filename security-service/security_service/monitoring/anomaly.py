"""Anomaly detection engine."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.security_events import SecurityEvent, EventType
from ..config import config


class AnomalyDetectionEngine:
    """Anomaly detection engine using statistical analysis."""
    
    def __init__(self, db: Session):
        self.db = db
        self.baseline_days = config.anomaly_baseline_days
        self.threshold_multiplier = config.anomaly_threshold_multiplier
        self.baselines = {}
        
    def establish_baseline(self):
        """Establish baseline metrics from historical data."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.baseline_days)
        
        # Traffic volume baseline
        traffic_baseline = self._calculate_traffic_baseline(start_date, end_date)
        self.baselines["traffic_volume"] = traffic_baseline
        
        # Failed authentication baseline
        auth_baseline = self._calculate_auth_baseline(start_date, end_date)
        self.baselines["failed_auth"] = auth_baseline
        
        # Geographic baseline
        geo_baseline = self._calculate_geographic_baseline(start_date, end_date)
        self.baselines["geographic"] = geo_baseline
        
        # API usage baseline
        api_baseline = self._calculate_api_baseline(start_date, end_date)
        self.baselines["api_usage"] = api_baseline
    
    def _calculate_traffic_baseline(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate traffic volume baseline."""
        # Get hourly traffic counts
        hourly_counts = defaultdict(int)
        
        events = self.db.query(SecurityEvent).filter(
            SecurityEvent.detected_at >= start_date,
            SecurityEvent.detected_at <= end_date
        ).all()
        
        for event in events:
            hour_key = event.detected_at.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour_key] += 1
        
        if not hourly_counts:
            return {"mean": 0, "std": 0, "max": 0}
        
        values = list(hourly_counts.values())
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = variance ** 0.5
        max_value = max(values)
        
        return {
            "mean": mean,
            "std": std,
            "max": max_value
        }
    
    def _calculate_auth_baseline(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate failed authentication baseline."""
        failed_auths = self.db.query(SecurityEvent).filter(
            SecurityEvent.event_type == EventType.UNAUTHORIZED_ACCESS.value,
            SecurityEvent.detected_at >= start_date,
            SecurityEvent.detected_at <= end_date
        ).count()
        
        days = (end_date - start_date).days or 1
        daily_avg = failed_auths / days
        
        return {
            "daily_average": daily_avg,
            "total": failed_auths
        }
    
    def _calculate_geographic_baseline(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate geographic access baseline."""
        # This would require IP geolocation data
        # For now, return empty baseline
        return {
            "countries": {},
            "top_countries": []
        }
    
    def _calculate_api_baseline(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate API usage baseline."""
        endpoint_counts = defaultdict(int)
        
        events = self.db.query(SecurityEvent).filter(
            SecurityEvent.detected_at >= start_date,
            SecurityEvent.detected_at <= end_date,
            SecurityEvent.endpoint.isnot(None)
        ).all()
        
        for event in events:
            if event.endpoint:
                endpoint_counts[event.endpoint] += 1
        
        return {
            "endpoints": dict(endpoint_counts),
            "top_endpoints": sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies based on established baselines."""
        if not self.baselines:
            self.establish_baseline()
        
        anomalies = []
        
        # Check traffic volume anomaly
        traffic_anomaly = self._check_traffic_anomaly()
        if traffic_anomaly:
            anomalies.append(traffic_anomaly)
        
        # Check authentication anomaly
        auth_anomaly = self._check_auth_anomaly()
        if auth_anomaly:
            anomalies.append(auth_anomaly)
        
        # Check API usage anomaly
        api_anomaly = self._check_api_anomaly()
        if api_anomaly:
            anomalies.append(api_anomaly)
        
        return anomalies
    
    def _check_traffic_anomaly(self) -> Optional[Dict[str, Any]]:
        """Check for traffic volume anomalies."""
        baseline = self.baselines.get("traffic_volume", {})
        if not baseline or baseline.get("mean", 0) == 0:
            return None
        
        # Check last hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        recent_count = self.db.query(SecurityEvent).filter(
            SecurityEvent.detected_at >= start_time,
            SecurityEvent.detected_at <= end_time
        ).count()
        
        threshold = baseline["mean"] + (baseline["std"] * self.threshold_multiplier)
        
        if recent_count > threshold:
            return {
                "type": "traffic_volume",
                "severity": "high",
                "description": f"Unusual traffic volume detected: {recent_count} events (baseline: {baseline['mean']:.2f})",
                "current_value": recent_count,
                "baseline_mean": baseline["mean"],
                "threshold": threshold
            }
        
        return None
    
    def _check_auth_anomaly(self) -> Optional[Dict[str, Any]]:
        """Check for authentication anomalies."""
        baseline = self.baselines.get("failed_auth", {})
        if not baseline:
            return None
        
        # Check last hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        recent_failures = self.db.query(SecurityEvent).filter(
            SecurityEvent.event_type == EventType.UNAUTHORIZED_ACCESS.value,
            SecurityEvent.detected_at >= start_time,
            SecurityEvent.detected_at <= end_time
        ).count()
        
        hourly_avg = baseline["daily_average"] / 24
        threshold = hourly_avg * self.threshold_multiplier
        
        if recent_failures > threshold:
            return {
                "type": "failed_authentication",
                "severity": "high",
                "description": f"Unusual number of failed authentications: {recent_failures} (baseline: {hourly_avg:.2f}/hour)",
                "current_value": recent_failures,
                "baseline_avg": hourly_avg,
                "threshold": threshold
            }
        
        return None
    
    def _check_api_anomaly(self) -> Optional[Dict[str, Any]]:
        """Check for API usage anomalies."""
        baseline = self.baselines.get("api_usage", {})
        if not baseline:
            return None
        
        # Check for unusual endpoint access patterns
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        endpoint_counts = defaultdict(int)
        events = self.db.query(SecurityEvent).filter(
            SecurityEvent.detected_at >= start_time,
            SecurityEvent.detected_at <= end_time,
            SecurityEvent.endpoint.isnot(None)
        ).all()
        
        for event in events:
            if event.endpoint:
                endpoint_counts[event.endpoint] += 1
        
        # Check for endpoints with unusual access
        baseline_endpoints = baseline.get("endpoints", {})
        anomalies = []
        
        for endpoint, count in endpoint_counts.items():
            baseline_count = baseline_endpoints.get(endpoint, 0)
            threshold = baseline_count * self.threshold_multiplier if baseline_count > 0 else 10
            
            if count > threshold:
                anomalies.append({
                    "endpoint": endpoint,
                    "current_count": count,
                    "baseline_count": baseline_count,
                    "threshold": threshold
                })
        
        if anomalies:
            return {
                "type": "api_usage",
                "severity": "medium",
                "description": f"Unusual API usage patterns detected for {len(anomalies)} endpoints",
                "anomalies": anomalies
            }
        
        return None

