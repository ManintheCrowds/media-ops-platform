"""pfSense API integration for firewall management and monitoring."""

import httpx
import logging
from typing import Dict, Any, Optional, List
from ..config import config

logger = logging.getLogger(__name__)


class PfSenseClient:
    """pfSense API client for firewall management."""
    
    def __init__(self):
        self.base_url = config.pfsense_url
        self.api_key = config.pfsense_api_key
        self.verify_ssl = config.pfsense_verify_ssl
        self.timeout = config.pfsense_timeout
        self.enabled = bool(self.base_url and self.api_key)
        
        if self.enabled:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                verify=self.verify_ssl,
                timeout=self.timeout,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
        else:
            self.client = None
            logger.warning("pfSense integration not configured")
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request to pfSense."""
        if not self.enabled:
            return {"error": "pfSense integration not configured"}
        
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"pfSense API error: {e}")
            return {"error": str(e), "success": False}
        except Exception as e:
            logger.error(f"Unexpected error in pfSense API: {e}")
            return {"error": str(e), "success": False}
    
    async def create_firewall_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create firewall rule via pfSense API."""
        if not self.enabled:
            return {"error": "pfSense integration not configured"}
        
        endpoint = "/api/v1/firewall/rule"
        return await self._request("POST", endpoint, json=rule_data)
    
    async def update_firewall_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing firewall rule via pfSense API."""
        if not self.enabled:
            return {"error": "pfSense integration not configured"}
        
        endpoint = f"/api/v1/firewall/rule/{rule_id}"
        return await self._request("PUT", endpoint, json=rule_data)
    
    async def delete_firewall_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete firewall rule via pfSense API."""
        if not self.enabled:
            return {"error": "pfSense integration not configured"}
        
        endpoint = f"/api/v1/firewall/rule/{rule_id}"
        return await self._request("DELETE", endpoint)
    
    async def get_firewall_rules(self, interface: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all firewall rules from pfSense."""
        if not self.enabled:
            return []
        
        endpoint = "/api/v1/firewall/rule"
        params = {}
        if interface:
            params["interface"] = interface
        
        result = await self._request("GET", endpoint, params=params)
        if "data" in result:
            return result["data"]
        return []
    
    async def get_firewall_rule(self, rule_id: str) -> Dict[str, Any]:
        """Get specific firewall rule by ID."""
        if not self.enabled:
            return {}
        
        endpoint = f"/api/v1/firewall/rule/{rule_id}"
        result = await self._request("GET", endpoint)
        if "data" in result:
            return result["data"]
        return {}
    
    async def create_ip_alias(self, alias_name: str, ip_addresses: List[str]) -> Dict[str, Any]:
        """Create IP alias in pfSense."""
        if not self.enabled:
            return {"error": "pfSense integration not configured"}
        
        endpoint = "/api/v1/firewall/alias"
        data = {
            "name": alias_name,
            "address": ip_addresses,
            "type": "host"
        }
        return await self._request("POST", endpoint, json=data)
    
    async def get_traffic_stats(self, interface: Optional[str] = None) -> Dict[str, Any]:
        """Get traffic statistics from pfSense."""
        if not self.enabled:
            return {}
        
        endpoint = "/api/v1/status/traffic"
        params = {}
        if interface:
            params["interface"] = interface
        
        result = await self._request("GET", endpoint, params=params)
        if "data" in result:
            return result["data"]
        return {}
    
    async def get_interface_stats(self, interface: Optional[str] = None) -> Dict[str, Any]:
        """Get interface statistics from pfSense."""
        if not self.enabled:
            return {}
        
        endpoint = "/api/v1/status/interface"
        params = {}
        if interface:
            params["interface"] = interface
        
        result = await self._request("GET", endpoint, params=params)
        if "data" in result:
            return result["data"]
        return {}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status from pfSense."""
        if not self.enabled:
            return {}
        
        endpoint = "/api/v1/status/system"
        result = await self._request("GET", endpoint)
        if "data" in result:
            return result["data"]
        return {}
    
    async def get_firewall_logs(self, limit: int = 100, interface: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get firewall logs from pfSense."""
        if not self.enabled:
            return []
        
        endpoint = "/api/v1/logs/firewall"
        params = {"limit": limit}
        if interface:
            params["interface"] = interface
        
        result = await self._request("GET", endpoint, params=params)
        if "data" in result:
            return result["data"]
        return []
    
    async def get_vpn_connections(self) -> List[Dict[str, Any]]:
        """Get active VPN connections from pfSense."""
        if not self.enabled:
            return []
        
        endpoint = "/api/v1/vpn/openvpn/status"
        result = await self._request("GET", endpoint)
        if "data" in result:
            return result["data"]
        return []
    
    async def block_ip(self, ip_address: str, duration: int = 3600, reason: str = "") -> Dict[str, Any]:
        """Block IP address via firewall rule."""
        if not self.enabled:
            return {"error": "pfSense integration not configured"}
        
        rule_data = {
            "type": "block",
            "interface": "wan",
            "protocol": "any",
            "source": {
                "address": ip_address
            },
            "destination": {
                "any": True
            },
            "description": f"Blocked by security service: {reason}",
            "expire": duration
        }
        
        return await self.create_firewall_rule(rule_data)
    
    async def unblock_ip(self, ip_address: str) -> Dict[str, Any]:
        """Unblock IP address by removing firewall rule."""
        if not self.enabled:
            return {"error": "pfSense integration not configured"}
        
        # Get all firewall rules
        rules = await self.get_firewall_rules()
        
        # Find rule blocking this IP
        for rule in rules:
            if (rule.get("source", {}).get("address") == ip_address and 
                rule.get("type") == "block"):
                return await self.delete_firewall_rule(rule["id"])
        
        return {"error": "Blocking rule not found"}
    
    async def get_bandwidth_usage(self, vlan: Optional[str] = None) -> Dict[str, Any]:
        """Get bandwidth usage per VLAN."""
        if not self.enabled:
            return {}
        
        interface = None
        if vlan:
            # Map VLAN to interface name
            vlan_interfaces = {
                "10": "opt1",  # Management
                "20": "opt2",  # DMZ
                "30": "opt3",  # Web Services
                "40": "opt4",  # Database
                "50": "opt5",  # Storage
                "60": "opt6",  # IoT
                "70": "opt7"   # Guest
            }
            interface = vlan_interfaces.get(vlan)
        
        return await self.get_traffic_stats(interface)
    
    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
