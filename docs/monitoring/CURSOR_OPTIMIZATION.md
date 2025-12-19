# Cursor Connection Optimization Guide

## Overview

This guide provides strategies and configurations to optimize Cursor IDE connection stability and performance.

## DNS Optimization

### Recommended DNS Servers

Use fast, reliable DNS servers:

- **Cloudflare**: `1.1.1.1` and `1.0.0.1`
- **Google**: `8.8.8.8` and `8.8.4.4`
- **Quad9**: `9.9.9.9` and `149.112.112.112`

### pfSense DNS Configuration

1. Navigate to **System > General Setup**
2. Set DNS servers:
   - Primary: `1.1.1.1`
   - Secondary: `8.8.8.8`
3. Enable **DNS Query Forwarding**
4. Enable **DNS Server Override**

### Windows DNS Configuration

```powershell
# Set DNS servers via PowerShell (run as Administrator)
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses "1.1.1.1","8.8.8.8"
```

Or via Network Settings:
1. Open **Network and Sharing Center**
2. Click on your network connection
3. Click **Properties**
4. Select **Internet Protocol Version 4 (TCP/IPv4)**
5. Click **Properties**
6. Select **Use the following DNS server addresses**
7. Enter preferred and alternate DNS servers

### DNS Caching

Enable DNS caching on pfSense:
1. Navigate to **Services > DNS Resolver**
2. Enable **DNS Resolver**
3. Configure cache size (default: 10000 entries)

### DNS Prefetching

Monitor DNS resolution times and prefetch frequently accessed domains:
- `api.cursor.com`
- `cdn.cursor.com`

## Firewall Rule Optimization

### Rule Order

Place Cursor firewall rules early in the rule list to reduce processing overhead:

1. **Allow Cursor HTTPS** (port 443)
2. **Allow Cursor WebSocket** (port 443)
3. Other rules...

### Connection Tracking

Optimize connection tracking timeouts in pfSense:
1. Navigate to **System > Advanced > Firewall & NAT**
2. Set **Firewall Maximum States**: 1000000 (or appropriate for your system)
3. Set **Firewall Maximum Table Entries**: 200000
4. Configure state timeouts:
   - **TCP Established**: 86400 seconds (24 hours)
   - **TCP Closing**: 3600 seconds (1 hour)
   - **TCP Timeout**: 300 seconds (5 minutes)

### Deep Packet Inspection

If using Snort or Suricata, consider:
- Excluding Cursor traffic from deep inspection
- Using pass rules for Cursor endpoints
- Optimizing rule sets to reduce false positives

## Quality of Service (QoS)

### Traffic Shaping

Configure QoS in pfSense to prioritize Cursor traffic:

1. Navigate to **Firewall > Traffic Shaper**
2. Create a queue for Cursor traffic:
   - **Name**: `CursorTraffic`
   - **Bandwidth**: Set appropriate limits
   - **Priority**: High
3. Create a rule to match Cursor endpoints:
   - **Interface**: LAN
   - **Protocol**: TCP
   - **Destination**: CursorEndpoints alias
   - **Port**: 443
   - **Queue**: CursorTraffic

### Bandwidth Limits

If bandwidth is limited:
- Set minimum bandwidth guarantee for Cursor traffic
- Use traffic shaping to prevent saturation
- Monitor bandwidth usage and adjust as needed

## Network Path Optimization

### MTU Configuration

Test and optimize MTU size:

```powershell
# Test MTU (Windows)
ping -f -l 1472 api.cursor.com

# If successful, increase size until failure
# Optimal MTU = successful size + 28 (IP + ICMP headers)
```

Configure MTU in pfSense:
1. Navigate to **Interfaces > [Interface]**
2. Set **MTU**: 1500 (or tested optimal value)

### TCP Settings

Optimize TCP settings on Windows:

```powershell
# Enable TCP Window Scaling
netsh int tcp set global autotuninglevel=normal

# Enable TCP Chimney Offload
netsh int tcp set global chimney=enabled

# Enable Receive Window Auto-Tuning
netsh int tcp set global rss=enabled
```

### Routing Optimization

1. Use traceroute to identify routing issues
2. Consider static routes for Cursor endpoints (if beneficial)
3. Monitor routing changes and adjust as needed

## Connection Pooling and Keep-Alive

### TCP Keep-Alive

Ensure TCP keep-alive is enabled (default on Windows):
- Keep-alive time: 2 hours
- Keep-alive interval: 1 second
- Keep-alive probes: 10

### Connection Reuse

Monitor connection reuse patterns:
- Cursor should maintain persistent connections
- Monitor for excessive connection churn
- Adjust timeouts if connections are closing prematurely

### Retry Logic

Cursor handles retries automatically, but monitor:
- Retry frequency
- Backoff patterns
- Connection recovery time

## VPN/Proxy Considerations

### If Using VPN

- Test Cursor connectivity with VPN enabled/disabled
- Consider split-tunneling for Cursor traffic
- Monitor VPN latency and packet loss
- Use VPN servers with low latency to Cursor endpoints

### If Using Proxy

- Configure proxy bypass for Cursor endpoints
- Test direct connection vs proxy connection
- Monitor proxy performance and errors

## Monitoring and Tuning

### Baseline Metrics

Establish baseline metrics:
- Average latency: < 100ms
- Packet loss: < 1%
- DNS resolution: < 50ms
- Connection duration: > 1 hour

### Continuous Optimization

1. Monitor metrics daily
2. Identify trends and anomalies
3. Adjust configurations based on data
4. Test changes in non-production first
5. Document all changes

## Troubleshooting

### High Latency

1. Check DNS resolution time
2. Test with different DNS servers
3. Check for network congestion
4. Verify firewall rule order
5. Test MTU size

### Packet Loss

1. Check network interface errors
2. Verify cable/connection quality
3. Check for network congestion
4. Test with different network paths
5. Verify QoS configuration

### Frequent Disconnects

1. Check connection timeouts
2. Verify firewall state table limits
3. Monitor for connection errors
4. Check for network interface issues
5. Review Windows Event Logs

## Best Practices

1. **Regular Monitoring**: Review metrics weekly
2. **Documentation**: Document all configuration changes
3. **Testing**: Test changes in staging first
4. **Backup**: Backup configurations before changes
5. **Baseline**: Establish and maintain baseline metrics
6. **Alerts**: Configure alerts for anomalies
7. **Review**: Regular review of optimization effectiveness

## Configuration Files

- Firewall rules: `config/pfsense/cursor-firewall-rules.xml`
- Prometheus alerts: `prometheus/alert_rules.yml`
- Monitoring scripts: `scripts/monitoring/`

## See Also

- [Cursor Monitoring Guide](CURSOR_MONITORING.md)
- [Network Topology](../NETWORK_TOPOLOGY.md)
- [pfSense Configuration](../PFSENSE_CONFIGURATION.md)
