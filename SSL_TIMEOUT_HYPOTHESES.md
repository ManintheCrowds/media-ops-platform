# SSL Timeout Debug - Hypotheses

## Problem
Darktide backend authentication fails with: `schannel: timed out sending data (bytes sent: 0)`

The timeout occurs ~21 seconds after the connection attempt starts (22:23:12.526 → 22:23:33.707).

## Hypotheses to Test

### Hypothesis A: Firewall is blocking SSL handshake packets
**Theory:** Windows Firewall or security software is silently dropping SSL handshake packets before they can be sent, causing the timeout.

**Evidence to collect:**
- Firewall block events in Windows Event Log
- Firewall rules that might interfere
- Security software intercepting SSL traffic

### Hypothesis B: Network adapter priority is wrong
**Theory:** Traffic is being routed through a non-primary or misconfigured network adapter (e.g., TAP adapter, disabled adapter), causing routing delays.

**Evidence to collect:**
- Network adapter priorities (InterfaceMetric)
- Which adapter is actually being used for outbound traffic
- Adapter status and link speed

### Hypothesis C: VPN/TAP adapter is interfering with SSL traffic
**Theory:** The TAP-Windows Adapter V9 for OpenVPN Connect (detected in system info) is intercepting or interfering with SSL handshake packets.

**Evidence to collect:**
- TAP adapter status and configuration
- Whether TAP adapter is active during connection attempt
- Network routing through TAP adapter

### Hypothesis D: DNS resolution is slow/failing for backend servers
**Theory:** DNS lookup for `bsp-sup-sd.atoma-discovery.com` is taking too long or failing, delaying the SSL handshake start.

**Evidence to collect:**
- DNS resolution time for backend hostnames
- DNS resolution success/failure
- DNS server response times

### Hypothesis E: Windows schannel timeout settings are too short
**Theory:** Windows schannel (SSL/TLS) has timeout values configured that are shorter than the network latency, causing premature timeouts.

**Evidence to collect:**
- Schannel ClientCacheTime and ServerCacheTime registry values
- Schannel error events in Windows Event Log
- Timeout configuration vs actual network latency

### Hypothesis F: Network congestion or packet loss causing timeouts
**Theory:** Network path to backend servers has high latency, packet loss, or congestion, preventing SSL handshake from completing.

**Evidence to collect:**
- Connectivity test results (Test-NetConnection)
- Network connection states during connection attempt
- Packet loss or latency measurements

## Monitoring Script

The script `darktide_ssl_timeout_debug.ps1` will:
1. Check firewall blocks
2. Monitor network adapter priorities
3. Detect VPN/TAP adapter interference
4. Test DNS resolution times
5. Check schannel timeout settings
6. Test network connectivity
7. Monitor Darktide process network connections in real-time
8. Capture schannel errors from Event Log

All evidence is logged to: `d:\portfolio-harness\.cursor\debug.log` in NDJSON format.



