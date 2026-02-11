"""URL validation for SSRF (Server-Side Request Forgery) protection."""

import ipaddress
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse
import re


def is_private_ip(ip: str) -> bool:
    """
    Check if an IP address is in private or reserved ranges.
    
    Args:
        ip: IP address string (IPv4 or IPv6)
        
    Returns:
        True if IP is private/reserved, False otherwise
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        
        # Check for private/reserved ranges
        return (
            ip_obj.is_private or
            ip_obj.is_loopback or
            ip_obj.is_link_local or
            ip_obj.is_reserved or
            ip_obj.is_multicast
        )
    except ValueError:
        # Invalid IP address format
        return False


def matches_allowed_pattern(url: str, patterns: list[str]) -> bool:
    """
    Check if URL matches any allowed internal service pattern.
    
    Supports wildcards:
    - http://seafile:* matches any port on seafile hostname
    - http://seafile:8000 matches specific hostname and port
    
    Args:
        url: URL to check
        patterns: List of allowed URL patterns with wildcards
        
    Returns:
        True if URL matches any pattern, False otherwise
    """
    if not patterns:
        return False
    
    parsed = urlparse(url)
    url_scheme = parsed.scheme
    url_hostname = parsed.hostname
    url_port = parsed.port
    
    for pattern in patterns:
        pattern_parsed = urlparse(pattern)
        pattern_scheme = pattern_parsed.scheme
        pattern_netloc = pattern_parsed.netloc
        
        # Check if pattern has wildcard port (e.g., "seafile:*")
        has_wildcard_port = pattern_netloc and pattern_netloc.endswith(":*")
        
        # Extract hostname - if wildcard port, remove ":*" first
        if has_wildcard_port:
            pattern_hostname = pattern_netloc.replace(":*", "")
        else:
            pattern_hostname = pattern_parsed.hostname
        
        pattern_port = None
        if not has_wildcard_port:
            try:
                pattern_port = pattern_parsed.port
            except ValueError:
                # Invalid port in pattern - treat as non-match
                continue
        
        # Check scheme match
        if pattern_scheme and url_scheme != pattern_scheme:
            continue
        
        # Check hostname match (supports wildcard *)
        if pattern_hostname:
            if pattern_hostname == "*":
                # Wildcard matches any hostname
                pass
            elif "*" in pattern_hostname:
                # Convert wildcard pattern to regex
                pattern_regex = pattern_hostname.replace(".", r"\.").replace("*", ".*")
                if not re.match(f"^{pattern_regex}$", url_hostname or ""):
                    continue
            elif pattern_hostname != url_hostname:
                continue
        else:
            continue
        
        # Check port match (supports wildcard *)
        if has_wildcard_port:
            # Wildcard port matches any port (or no port with default)
            return True
        elif pattern_port is not None:
            # Specific port must match
            if url_port == pattern_port:
                return True
            elif url_port is None:
                # No port in URL, check if pattern port is default
                if pattern_scheme == "http" and pattern_port == 80:
                    return True
                elif pattern_scheme == "https" and pattern_port == 443:
                    return True
        else:
            # No port specified in pattern, matches any port
            return True
    
    return False


def validate_service_url(
    url: str,
    allowed_internal_patterns: Optional[list[str]] = None
) -> Tuple[bool, str]:
    """
    Validate a service URL to prevent SSRF attacks.
    
    Blocks:
    - Non-HTTP(S) schemes (file://, ftp://, javascript:, data:, etc.)
    - Localhost variations (localhost, 127.0.0.1, 0.0.0.0, ::1)
    - Private IP ranges (10.x, 192.168.x, 172.16-31.x, etc.)
    - Link-local and reserved IP ranges
    
    Allows:
    - HTTP and HTTPS URLs to public IPs
    - URLs matching allowed_internal_patterns (for legitimate internal services)
    
    Args:
        url: URL string to validate
        allowed_internal_patterns: List of allowed internal service URL patterns
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if URL is safe, False otherwise
        - error_message: Description of validation failure, empty if valid
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"
    
    url = url.strip()
    if not url:
        return False, "URL cannot be empty"
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"
    
    # Validate scheme - only allow http and https
    allowed_schemes = {"http", "https"}
    if parsed.scheme not in allowed_schemes:
        dangerous_schemes = {
            "file", "ftp", "gopher", "javascript", "data", "vbscript",
            "mailto", "tel", "ssh", "sftp", "ldap", "ldaps"
        }
        if parsed.scheme.lower() in dangerous_schemes:
            return False, f"Dangerous URL scheme '{parsed.scheme}' is not allowed"
        return False, f"URL scheme '{parsed.scheme}' is not allowed. Only http:// and https:// are permitted"
    
    # Check if URL matches allowed internal patterns
    if allowed_internal_patterns:
        if matches_allowed_pattern(url, allowed_internal_patterns):
            return True, ""
    
    # Validate hostname/netloc
    hostname = parsed.hostname
    if not hostname:
        return False, "URL must include a hostname"
    
    # Check for localhost variations
    localhost_variations = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "::",
        "0:0:0:0:0:0:0:1",
        "0:0:0:0:0:0:0:0"
    }
    if hostname.lower() in localhost_variations:
        return False, "Localhost addresses are not allowed for security reasons"
    
    # Check for private IP addresses
    # First, try to parse as IP address
    try:
        ip_obj = ipaddress.ip_address(hostname)
        if is_private_ip(hostname):
            return False, "Private IP addresses are not allowed for security reasons"
    except ValueError:
        # Not a direct IP address, check if it resolves to private IP
        # For hostname-based URLs, we'll check common private hostname patterns
        # Note: We can't do DNS resolution here as it would be slow and could be exploited
        # Instead, we rely on IP address checking and pattern matching
        
        # Check for common private hostname patterns that might be used for SSRF
        private_hostname_patterns = [
            r"^127\.",  # 127.x.x.x
            r"^10\.",   # 10.x.x.x
            r"^192\.168\.",  # 192.168.x.x
            r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",  # 172.16-31.x.x
            r"^169\.254\.",  # Link-local
        ]
        for pattern in private_hostname_patterns:
            if re.match(pattern, hostname):
                return False, "Private network hostnames are not allowed for security reasons"
    
    # Additional validation: check for path traversal attempts in path
    if parsed.path:
        # Check for path traversal patterns
        dangerous_path_patterns = [
            "../",
            "..\\",
            "..%2F",
            "..%5C",
            "%2e%2e%2f",
            "%2e%2e%5c"
        ]
        path_lower = parsed.path.lower()
        for pattern in dangerous_path_patterns:
            if pattern.lower() in path_lower:
                return False, "Path traversal attempts are not allowed"
    
    # URL is valid
    return True, ""





