"""Security service configuration."""

from pydantic_settings import BaseSettings
from typing import Optional, List


class SecurityServiceConfig(BaseSettings):
    """Security service configuration."""
    
    # Service Configuration
    service_name: str = "security-service"
    service_port: int = 8001
    debug: bool = False
    
    # Database Configuration
    database_url: str = "postgresql://platform:platform@postgres:5432/platform"
    
    # Redis Configuration
    redis_url: str = "redis://redis:6379"
    redis_db: int = 0
    
    # Prometheus Configuration
    prometheus_url: str = "http://prometheus:9090"
    metrics_enabled: bool = True
    
    # Threat Intelligence
    abuseipdb_api_key: Optional[str] = None
    virustotal_api_key: Optional[str] = None
    threat_intel_update_interval: int = 3600  # seconds
    
    # Alerting Configuration
    alert_email_enabled: bool = False
    alert_email_smtp_host: Optional[str] = None
    alert_email_smtp_port: int = 587
    alert_email_smtp_user: Optional[str] = None
    alert_email_smtp_password: Optional[str] = None
    alert_email_from: Optional[str] = None
    alert_email_to: List[str] = []
    alert_slack_webhook: Optional[str] = None
    alert_webhook_url: Optional[str] = None
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_ip: int = 100
    rate_limit_window: int = 60  # seconds
    rate_limit_per_user: int = 200
    rate_limit_per_endpoint: dict = {}
    
    # pfSense Integration
    pfsense_url: Optional[str] = None
    pfsense_api_key: Optional[str] = None
    pfsense_verify_ssl: bool = False
    pfsense_timeout: int = 30
    
    # VLAN Mappings
    vlan_management: int = 10
    vlan_dmz: int = 20
    vlan_web: int = 30
    vlan_database: int = 40
    vlan_storage: int = 50
    vlan_iot: int = 60
    vlan_guest: int = 70
    
    # IDS Configuration
    ids_enabled: bool = True
    ids_signature_file: str = "signatures.yaml"
    ids_brute_force_threshold: int = 5
    ids_brute_force_window: int = 300  # seconds
    
    # Anomaly Detection
    anomaly_detection_enabled: bool = True
    anomaly_baseline_days: int = 7
    anomaly_threshold_multiplier: float = 2.0
    
    # DDoS Protection
    ddos_protection_enabled: bool = True
    ddos_threshold_requests: int = 1000
    ddos_threshold_window: int = 60  # seconds
    ddos_block_duration: int = 3600  # seconds
    
    # Log Aggregation
    log_retention_days: int = 90
    log_aggregation_enabled: bool = True
    
    # Compliance
    audit_log_enabled: bool = True
    audit_log_retention_days: int = 365
    compliance_report_schedule: str = "0 0 * * 0"  # Weekly on Sunday
    
    # Malware Scanning
    malware_scanning_enabled: bool = True
    clamav_host: Optional[str] = None
    clamav_port: int = 3310
    
    # Vulnerability Scanning
    vulnerability_scanning_enabled: bool = True
    vulnerability_scan_schedule: str = "0 2 * * *"  # Daily at 2 AM
    
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False


# Global config instance
config = SecurityServiceConfig()
