# Router Security Checklist - CenturyLink C550xk

## Immediate Actions (Do These NOW)

### 1. Access Router Admin Panel
- [ ] Open browser and go to: `http://192.168.0.1`
- [ ] Log in with current credentials
- [ ] **If you can't log in**: Router may be compromised - contact CenturyLink immediately

### 2. Identify Suspicious Device
- [ ] Navigate to "Connected Devices" or "DHCP Client List"
- [ ] Look for device named "Roko_Basilisk 2"
- [ ] Note the IP address: `_________________`
- [ ] Note the MAC address: `_________________`
- [ ] Take screenshot of device list

### 3. Change Router Password (CRITICAL)
- [ ] Go to "Administration" or "Settings"
- [ ] Change admin password to strong password (16+ characters, mixed case, numbers, symbols)
- [ ] Save changes
- [ ] Log out and log back in to verify

### 4. Change Wi-Fi Password
- [ ] Go to "Wireless" or "Wi-Fi Settings"
- [ ] Change Wi-Fi password (WPA2 or WPA3)
- [ ] Use strong password (different from admin password)
- [ ] Save changes
- [ ] Reconnect all devices with new password

### 5. Block Suspicious Device
- [ ] Find MAC address filtering or Access Control settings
- [ ] Add "Roko_Basilisk 2" MAC address to block list
- [ ] OR remove from allowed devices list
- [ ] Save changes

## Router Hardening (Complete Within 24 Hours)

### Security Settings
- [ ] **Disable Remote Management**
  - Location: Administration → Remote Management
  - Status: Should be OFF/Disabled
  
- [ ] **Disable WPS (Wi-Fi Protected Setup)**
  - Location: Wireless → WPS Settings
  - Status: Should be OFF/Disabled
  - **Why**: WPS has known security vulnerabilities

- [ ] **Disable UPnP (Universal Plug and Play)**
  - Location: Advanced → UPnP
  - Status: Should be OFF/Disabled (unless you specifically need it)
  - **Why**: Can allow unauthorized port forwarding

- [ ] **Enable MAC Address Filtering**
  - Location: Wireless → MAC Filtering or Access Control
  - Status: Enable and add only known devices
  - **Why**: Prevents unauthorized devices from connecting

- [ ] **Change SSID (Network Name)**
  - Location: Wireless → Basic Settings
  - Change from default name
  - **Why**: Hides router model from attackers

- [ ] **Enable Guest Network** (Optional but Recommended)
  - Location: Wireless → Guest Network
  - Create separate network for visitors
  - Use different password
  - Isolate from main network

### Firmware Update
- [ ] **Check Current Firmware Version**
  - Location: Administration → Firmware or System
  - Current version: `_________________`
  
- [ ] **Check for Updates**
  - Visit CenturyLink support site
  - Or check router admin panel for update option
  - Latest version: `_________________`
  
- [ ] **Update Firmware** (if available)
  - Follow manufacturer instructions
  - **Warning**: Don't interrupt update process
  - Router will restart after update

### Firewall Settings
- [ ] **Enable Firewall**
  - Location: Firewall or Security
  - Status: Should be ENABLED
  
- [ ] **Review Port Forwarding Rules**
  - Location: Firewall → Port Forwarding
  - Remove any rules you didn't create
  - Only keep rules you need
  
- [ ] **Review Firewall Rules**
  - Location: Firewall → Rules
  - Check for suspicious rules
  - Remove unauthorized rules

### DNS Settings
- [ ] **Check DNS Servers**
  - Location: Network → DNS Settings
  - Should be: CenturyLink DNS or trusted DNS (e.g., 1.1.1.1, 8.8.8.8)
  - If changed to unknown servers: **SECURITY RISK**
  - Change back to trusted DNS

## Network Monitoring Setup

### Enable Logging
- [ ] **Enable Router Logging**
  - Location: Administration → Logs or System Log
  - Enable logging
  - Set log level to "All" or "Security"
  
- [ ] **Review Logs**
  - Check for:
    - Failed login attempts
    - Unauthorized access
    - Port scans
    - Unusual activity

### Device Monitoring
- [ ] **Review Connected Devices Weekly**
  - Check device list regularly
  - Remove unknown devices immediately
  - Keep inventory of authorized devices

- [ ] **Set Up Device Alerts** (if available)
  - Enable notifications for new devices
  - Monitor for unauthorized connections

## Password Security

### Create Strong Passwords
- [ ] Router admin password: 16+ characters, unique
- [ ] Wi-Fi password: 16+ characters, unique
- [ ] Different from admin password
- [ ] Not used anywhere else
- [ ] Stored securely (password manager)

### Password Rotation Schedule
- [ ] Change router admin password: Every 3 months
- [ ] Change Wi-Fi password: Every 6 months
- [ ] Or immediately if compromise suspected

## Additional Security Measures

### Physical Security
- [ ] Router in secure location
- [ ] Reset button not easily accessible
- [ ] No unauthorized physical access

### Network Segmentation
- [ ] Guest network enabled (if available)
- [ ] IoT devices on separate network (if possible)
- [ ] Main devices on primary network

### Regular Maintenance
- [ ] Weekly: Review connected devices
- [ ] Monthly: Check for firmware updates
- [ ] Quarterly: Full security audit
- [ ] Annually: Consider router replacement if outdated

## Incident Documentation

### Record These Details
- [ ] Date/time Norton alerted: `_________________`
- [ ] Suspicious device name: `Roko_Basilisk 2`
- [ ] Device IP address: `_________________`
- [ ] Device MAC address: `_________________`
- [ ] Router model: `CenturyLink C550xk`
- [ ] Router IP: `192.168.0.1`
- [ ] Actions taken: `_________________`
- [ ] Screenshots saved: `_________________`

## Contact Information

### CenturyLink Support
- **Phone**: 1-800-244-1111
- **Online**: centurylink.com/support
- **Report**: Router security concerns

### If Identity Theft Suspected
- **FTC**: identitytheft.gov
- **Credit Bureaus**: Place fraud alert
- **Local Police**: File report if financial loss

## Verification Steps

After securing router, verify:

- [ ] Can still access internet from trusted devices
- [ ] Suspicious device is blocked/removed
- [ ] All trusted devices can reconnect
- [ ] Router admin panel accessible with new password
- [ ] No unauthorized devices in device list
- [ ] Firewall is active
- [ ] Logging is enabled

## Post-Incident Actions

### Within 24 Hours
- [ ] Complete all immediate actions
- [ ] Change all online account passwords
- [ ] Run antivirus scan on all devices
- [ ] Review router logs
- [ ] Document incident

### Within 1 Week
- [ ] Full security audit
- [ ] Update all device firmware
- [ ] Set up network monitoring
- [ ] Review security policies
- [ ] Consider professional security audit

### Ongoing
- [ ] Weekly device review
- [ ] Monthly security check
- [ ] Quarterly full audit
- [ ] Stay informed about router security updates

---

**Remember**: When in doubt, assume compromise and take defensive action. Security is better than convenience.

**Priority Order**:
1. Block suspicious device (IMMEDIATE)
2. Change router password (IMMEDIATE)
3. Change Wi-Fi password (IMMEDIATE)
4. Disable remote management (WITHIN 1 HOUR)
5. Update firmware (WITHIN 24 HOURS)
6. Enable MAC filtering (WITHIN 24 HOURS)
7. Review all settings (WITHIN 24 HOURS)

