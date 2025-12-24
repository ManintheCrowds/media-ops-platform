# IP Address Investigation Guide

## Suspicious IP Ranges Detected

### 91.222.185.x Range

**Observation**: High volume of connections to IPs in the 91.222.185.x range detected.

**Investigation Steps**:

1. **Check IP Ownership**:
   - Visit: https://www.whois.com/whois/91.222.185.0
   - Look up individual IPs: https://www.abuseipdb.com/check/91.222.185.236
   - Check VirusTotal: https://www.virustotal.com/gui/ip-address/91.222.185.236

2. **Reverse DNS Lookup**:
   ```powershell
   [System.Net.Dns]::GetHostEntry("91.222.185.236")
   ```

3. **Check for Known Threats**:
   - AbuseIPDB: https://www.abuseipdb.com/
   - VirusTotal: https://www.virustotal.com/
   - Talos Intelligence: https://talosintelligence.com/

4. **Network Traffic Analysis**:
   - Check what process is making these connections
   - Review connection timing patterns
   - Check for data exfiltration

## Internal Network Analysis

### Device: 192.168.0.43

**Observation**: Multiple connections to this device on port 7680 (SMB/NetBIOS).

**Investigation Steps**:

1. **Identify the Device**:
   ```powershell
   # Check ARP table
   arp -a | Select-String "192.168.0.43"
   
   # Try to ping and get hostname
   ping -a 192.168.0.43
   ```

2. **Verify Device Identity**:
   - Check router admin panel for device name
   - Verify MAC address matches known device
   - Check if device should be on network

3. **Check Connection Purpose**:
   - Port 7680 is often used for SMB/NetBIOS file sharing
   - Verify if file sharing is expected
   - Check what files/services are being accessed

4. **Review Windows File Sharing**:
   ```powershell
   # Check current file shares
   Get-SmbShare
   
   # Check SMB connections
   Get-SmbConnection
   ```

### Router: 192.168.0.1

**Observation**: Many connections to router on ports 443 (HTTPS) and 53 (DNS).

**Investigation Steps**:

1. **Verify Router Access**:
   - Check if you've been accessing router admin panel
   - Review router logs for unauthorized access
   - Check for failed login attempts

2. **DNS Verification**:
   - Verify DNS server settings haven't been changed
   - Check for DNS hijacking
   - Test DNS resolution

## Manual IP Reputation Checks

For each suspicious IP, check:

1. **AbuseIPDB**: https://www.abuseipdb.com/check/[IP]
2. **VirusTotal**: https://www.virustotal.com/gui/ip-address/[IP]
3. **Talos Intelligence**: https://talosintelligence.com/reputation_center/lookup?search=[IP]
4. **Shodan**: https://www.shodan.io/host/[IP] (if you have account)
5. **Whois**: https://www.whois.com/whois/[IP]

## Process Investigation

To identify which process is making suspicious connections:

```powershell
# Get process making connections to specific IP
$ip = "91.222.185.236"
$conn = Get-NetTCPConnection | Where-Object { $_.RemoteAddress -eq $ip -and $_.State -eq "Established" }
$procId = $conn.OwningProcess | Select-Object -Unique
Get-Process -Id $procId | Format-List *
```

## Network Monitoring Tools

### Built-in Windows Tools

1. **Resource Monitor**:
   - Open: `resmon.exe`
   - Check Network tab for active connections

2. **Event Viewer**:
   - Check Security log for failed logins
   - Check System log for network errors

3. **Windows Defender Firewall**:
   - Review firewall rules
   - Check for unauthorized rules

### Third-Party Tools (Optional)

1. **Wireshark**: Deep packet inspection
2. **Nmap**: Network scanning
3. **Netstat**: Connection monitoring (built-in)
4. **TCPView**: Process connection viewer (Sysinternals)

## Router Investigation

### Access Router Admin Panel

1. Open browser: `http://192.168.0.1`
2. Log in with credentials
3. Check the following:

**Device List**:
- Navigate to "Connected Devices" or "DHCP Client List"
- Verify all devices are known
- Note MAC addresses and IP addresses

**Router Logs**:
- Check "System Log" or "Event Log"
- Look for:
  - Failed login attempts
  - Port scans
  - Unauthorized access
  - Configuration changes

**Firewall Rules**:
- Review all firewall rules
- Check for unauthorized port forwarding
- Verify rules match your configuration

**DNS Settings**:
- Check DNS server configuration
- Should be: CenturyLink DNS or trusted DNS (1.1.1.1, 8.8.8.8)
- If changed to unknown servers: **SECURITY RISK**

**Port Forwarding**:
- Review all port forwarding rules
- Remove any you didn't create
- Only keep necessary rules

## Action Items

Based on findings:

1. **If 91.222.185.x is malicious**:
   - Block IP range in Windows Firewall
   - Block in router firewall if possible
   - Investigate which process is connecting
   - Scan for malware

2. **If 192.168.0.43 is suspicious**:
   - Identify the device
   - Verify it should be on network
   - Review file sharing permissions
   - Consider isolating device

3. **If router shows unauthorized access**:
   - Change router password immediately
   - Review all settings
   - Update firmware
   - Enable logging

4. **General Security**:
   - Enable MAC address filtering
   - Disable remote management
   - Update all firmware
   - Change all passwords
   - Enable network monitoring

## Documentation

Record all findings:

- [ ] IP addresses checked
- [ ] Reputation check results
- [ ] Device identities verified
- [ ] Router settings reviewed
- [ ] Actions taken
- [ ] Screenshots saved

