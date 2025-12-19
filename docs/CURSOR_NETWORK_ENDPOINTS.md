# Cursor Network Endpoints

## Overview

This document lists all known network endpoints that Cursor IDE uses for its operations, particularly for AI features. This information is gathered through network discovery and monitoring.

## Primary Endpoints

### API Endpoints

- **api.cursor.com** (HTTPS, Port 443)
  - Primary API endpoint for Cursor services
  - Used for authentication, feature requests, and data synchronization
  - Protocol: HTTPS/TLS 1.2+

- ***.cursor.sh** (HTTPS, Port 443)
  - Additional Cursor service domains
  - May include regional endpoints or CDN services

### WebSocket Endpoints

- **wss://api.cursor.com** (WebSocket Secure, Port 443)
  - Real-time communication for AI features
  - Used for streaming completions and chat responses
  - Maintains persistent connections

### CDN and Static Resources

- **cdn.cursor.com** (HTTPS, Port 443)
  - Content delivery network for static assets
  - May include updates, extensions, or other resources

## Network Discovery

To discover additional endpoints, run:

```powershell
.\scripts\monitoring\cursor-endpoint-discovery.ps1
```

This script will:
- Monitor active Cursor connections
- Capture DNS queries
- Identify all domains and IPs Cursor connects to
- Export results for analysis

## Known IP Addresses

IP addresses are discovered dynamically and may change. Use the discovery script to get current IPs.

## Ports Used

- **443** - HTTPS/WebSocket Secure (primary)
- **80** - HTTP (redirects to HTTPS, rarely used)

## Protocols

- **HTTPS** - REST API calls, authentication
- **WSS (WebSocket Secure)** - Real-time AI features, streaming
- **TLS 1.2+** - Encryption standard

## Connection Patterns

### Typical Connection Flow

1. DNS resolution for `api.cursor.com`
2. TCP connection on port 443
3. TLS handshake
4. HTTP/WebSocket upgrade (if applicable)
5. Persistent connection maintained for AI features

### Connection Characteristics

- **Keep-Alive**: Enabled for persistent connections
- **Timeout**: Typically 30-60 seconds for idle connections
- **Retry Logic**: Automatic reconnection on failure
- **Compression**: May use gzip/brotli for HTTP responses

## Firewall Configuration

For pfSense, create firewall aliases for:
- `api.cursor.com`
- `*.cursor.sh`
- `cdn.cursor.com`

See `config/pfsense/cursor-firewall-rules.xml` for firewall rule configuration.

## Monitoring

All endpoints should be monitored for:
- Connection success/failure rates
- Latency
- Packet loss
- DNS resolution time
- Connection duration

## Updates

This document should be updated when:
- New endpoints are discovered
- Endpoints change or are deprecated
- Connection patterns change significantly

Last updated: 2025-12-19
