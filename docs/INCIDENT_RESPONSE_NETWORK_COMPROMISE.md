# Network Compromise Incident Response Guide

## Incident Summary

**Date**: [Current Date]  
**Severity**: HIGH  
**Type**: Unauthorized Device / Potential Network Compromise  
**Device Identified**: Roko_Basilisk 2  
**Router**: CenturyLink C550xk (192.168.0.1)  
**Alert Source**: Norton Security

## Immediate Actions Required

### 1. Isolate the Threat (IMMEDIATE)

**Disconnect from Network**:
- Disconnect the affected device from Wi-Fi
- If possible, disconnect the router from the internet temporarily
- Do NOT power off devices yet (preserve evidence)

**Change Router Credentials**:
1. Access router admin panel: `http://192.168.0.1`
2. Change admin password immediately
3. Change Wi-Fi password (WPA2/WPA3)
4. Enable MAC address filtering if available

### 2. Identify the Device

**Check Router Admin Panel**:
1. Log into router at `192.168.0.1`
2. Navigate to "Connected Devices" or "DHCP Client List"
3. Look for device named "Roko_Basilisk 2" or unknown MAC addresses
4. Note the IP address and MAC address of the suspicious device

**Physical Inspection**:
- Check all physical devices connected to your network
- Look for any devices you don't recognize
- Check for USB devices, external drives, or network adapters

**Network Scan** (if you have access):
```powershell
# Windows PowerShell - Scan network for devices
arp -a | Select-String "192.168.0"

# Get detailed network connections
Get-NetTCPConnection | Where-Object {$_.LocalAddress -like "192.168.0.*"} | Format-Table
```

### 3. Assess Compromise Level

**Check for**:
- [ ] Unauthorized devices on network
- [ ] Unknown network traffic
- [ ] Changed router settings
- [ ] Port forwarding rules you didn't create
- [ ] DNS settings changed
- [ ] Firewall rules modified

**Router Security Check**:
- [ ] Firmware up to date?
- [ ] Remote management enabled? (Should be DISABLED)
- [ ] UPnP enabled? (Should be DISABLED if not needed)
- [ ] WPS enabled? (Should be DISABLED - security risk)
- [ ] Default credentials changed?

### 4. Secure the Network

**Router Hardening**:
1. **Update Firmware**: Check CenturyLink for latest firmware
2. **Disable Remote Management**: Turn off remote admin access
3. **Disable WPS**: Wi-Fi Protected Setup is vulnerable
4. **Disable UPnP**: Unless specifically needed
5. **Enable MAC Filtering**: Only allow known devices
6. **Change SSID**: Use a new network name
7. **Enable Guest Network**: Isolate untrusted devices

**Password Changes**:
- [ ] Router admin password (strong, unique)
- [ ] Wi-Fi password (WPA3 if available, otherwise WPA2)
- [ ] All device passwords on network
- [ ] Online account passwords (email, banking, etc.)

### 5. Monitor Network Activity

**Enable Logging**:
- Enable router logging if available
- Monitor DHCP lease table
- Check for unusual traffic patterns

**Use Security Tools**:
- Run full antivirus scan on all devices
- Check for malware on all computers
- Review firewall logs
- Monitor network traffic

## Investigation Steps

### Step 1: Document the Incident

Record:
- Exact time Norton alerted you
- What you were doing when alerted
- All devices connected to network
- Any recent changes to network setup
- Router login history (if available)

### Step 2: Identify Device Type

"Roko_Basilisk 2" could be:
- A Roku streaming device (legitimate but misnamed)
- A compromised device with spoofed name
- An attacker's device
- A device you forgot about

**Check**:
- Do you own any Roku devices?
- Have you connected any new devices recently?
- Check all smart TVs, streaming devices, IoT devices

### Step 3: Check Router Logs

Access router logs:
1. Log into `192.168.0.1`
2. Navigate to "Logs" or "System Log"
3. Look for:
   - Unauthorized login attempts
   - Port scans
   - Unusual connection patterns
   - Failed authentication attempts

### Step 4: Network Traffic Analysis

If you have network monitoring:
- Check for data exfiltration
- Look for connections to suspicious IPs
- Monitor bandwidth usage
- Check for port scanning activity

## Recovery Steps

### Immediate Recovery

1. **Block the Device**:
   - Add MAC address to router blacklist
   - Or remove from allowed devices list

2. **Change All Credentials**:
   - Router admin
   - Wi-Fi password
   - All online accounts

3. **Update Firmware**:
   - Router firmware
   - All device firmware
   - Operating systems

4. **Scan for Malware**:
   - Full system scan on all devices
   - Check for keyloggers
   - Check for remote access tools

### Long-term Security

1. **Enable Network Monitoring**:
   - Set up device alerts
   - Monitor for new devices
   - Regular security audits

2. **Implement Network Segmentation**:
   - Separate IoT devices
   - Guest network for visitors
   - Isolated management network

3. **Regular Security Practices**:
   - Monthly password changes
   - Quarterly firmware updates
   - Regular security scans
   - Review connected devices weekly

## Network Analysis Findings

Based on your network scan, here are key findings to investigate:

### Devices Detected
- **192.168.0.1** (Router) - MAC: 58-13-d3-ef-f7-18
- **192.168.0.16** - MAC: 84-1b-77-e2-52-b6
- **192.168.0.43** - MAC: 7c-b5-66-3b-43-e0 ⚠️ **Investigate**
- **192.168.0.58** - MAC: b8-1e-a4-3e-93-9b
- **Your laptop**: 192.168.0.13

### Suspicious Patterns Detected

1. **High Volume Connections to 91.222.185.x Range**:
   - Multiple connections to IPs like 91.222.185.236, 91.222.185.232, etc.
   - **Action Required**: Investigate which process is making these connections
   - Check IP reputation: https://www.abuseipdb.com/check/91.222.185.236

2. **Connections to 192.168.0.43 on Port 7680**:
   - Port 7680 is typically SMB/NetBIOS file sharing
   - **Action Required**: Verify this device identity and purpose
   - Check if file sharing is expected

3. **Router Connections**:
   - Many connections to router (192.168.0.1) on ports 443 and 53
   - Port 443: HTTPS (admin interface)
   - Port 53: DNS
   - **Action Required**: Verify you've been accessing router admin panel

### Investigation Commands

Run these PowerShell commands to investigate:

```powershell
# Identify device at 192.168.0.43
ping -a 192.168.0.43
[System.Net.Dns]::GetHostEntry("192.168.0.43")

# Check which process is connecting to 91.222.185.x
$suspiciousIP = "91.222.185.236"
$conn = Get-NetTCPConnection | Where-Object { $_.RemoteAddress -eq $suspiciousIP -and $_.State -eq "Established" }
$procId = $conn.OwningProcess | Select-Object -Unique
Get-Process -Id $procId | Format-List ProcessName, Path, Id

# Check SMB file shares
Get-SmbShare
Get-SmbConnection

# Check Windows Firewall rules
Get-NetFirewallRule | Where-Object { $_.Enabled -eq $true } | Format-Table DisplayName, Direction, Action

# Check for suspicious processes
Get-Process | Where-Object { $_.Path -notlike "C:\Windows\*" -and $_.Path -notlike "C:\Program Files*" } | Format-Table ProcessName, Path
```

### Run Comprehensive Audit

Use the network audit script for detailed analysis:

```powershell
cd C:\Users\artin\software
.\scripts\security\network-audit-analysis.ps1
```

This will:
- Analyze all network connections
- Identify suspicious IP patterns
- Check process network activity
- Review Windows security logs
- Generate detailed report

## Using Security Service Tools

If you have the security service running, you can:

### Check Security Events
```bash
# View recent security events
curl http://localhost:8001/api/security/events?limit=50

# Check for intrusion attempts
curl http://localhost:8001/api/security/events?type=intrusion
```

### Block Suspicious IP
```bash
# Block an IP address
curl -X POST http://localhost:8001/api/security/firewall/rules \
  -H "Content-Type: application/json" \
  -d '{
    "ip_address": "192.168.0.X",
    "action": "block",
    "reason": "Unauthorized device - Roko_Basilisk 2"
  }'
```

### Check IP Reputation
```bash
# Check if IP is known malicious
curl http://localhost:8001/api/security/threats/ip/192.168.0.X
```

### PowerShell Alternative (if security service not running)
```powershell
# Check IP reputation manually
$ip = "91.222.185.236"
Start-Process "https://www.abuseipdb.com/check/$ip"
Start-Process "https://www.virustotal.com/gui/ip-address/$ip"
```

## Contact Information

**CenturyLink Support**:
- Phone: 1-800-244-1111
- Report router security concerns
- Request firmware update assistance

**If Identity Theft Suspected**:
- Federal Trade Commission: identitytheft.gov
- Credit bureaus: Place fraud alert
- Monitor financial accounts

## Prevention Checklist

Going forward, implement:

- [ ] Strong, unique router password (changed from default)
- [ ] WPA3 or WPA2 encryption (not WEP)
- [ ] MAC address filtering enabled
- [ ] Remote management disabled
- [ ] WPS disabled
- [ ] UPnP disabled (unless needed)
- [ ] Regular firmware updates
- [ ] Network monitoring enabled
- [ ] Guest network for visitors
- [ ] Regular security audits
- [ ] Device inventory maintained
- [ ] Automatic security updates enabled

## Notes

- **Do NOT delete router logs** until investigation complete
- **Document everything** - times, actions taken, findings
- **Take screenshots** of router settings and device lists
- **Keep Norton logs** for reference
- **Consider professional help** if compromise is confirmed

## Follow-up Actions

1. **Within 24 hours**:
   - Complete initial investigation
   - Secure network
   - Change all passwords
   - Document findings

2. **Within 1 week**:
   - Full security audit
   - Update all firmware
   - Review and update security policies
   - Set up monitoring

3. **Ongoing**:
   - Weekly device review
   - Monthly security check
   - Quarterly full audit

## Additional Resources

- [CenturyLink Router Security Guide](https://www.centurylink.com/home/help/internet/modems-and-routers.html)
- [FTC Identity Theft Guide](https://www.identitytheft.gov/)
- [CISA Home Network Security](https://www.cisa.gov/news-events/news/home-network-security)

---

**Remember**: When in doubt, assume compromise and take defensive action. It's better to be overly cautious than to leave a vulnerability open.

