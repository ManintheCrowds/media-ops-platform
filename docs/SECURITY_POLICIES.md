# Network Security Policies

## Overview

This document defines security policies for the VLAN-based network architecture, including Network Access Control (NAC), bandwidth management, intrusion detection, and access control policies.

## Network Access Control (NAC)

### Device Authentication

#### MAC Address Filtering

**Policy**: Critical devices must be registered by MAC address.

**Implementation**:
- Configure MAC address allowlist in pfSense
- Register devices in security service
- Block unregistered devices

**Devices Requiring Registration**:
- Servers (Dell PowerEdge)
- Network infrastructure
- Management workstations
- Raspberry Pi devices

**Procedure**:
1. Collect MAC addresses of authorized devices
2. Add to pfSense MAC address filter
3. Configure firewall rules to allow only registered MACs
4. Review and update quarterly

#### 802.1X Authentication (Future)

**Policy**: Implement 802.1X for network access control.

**Requirements**:
- RADIUS server
- Certificate-based authentication
- Per-user VLAN assignment
- Time-based access rules

### User Access Control

#### VPN Authentication

**Policy**: All remote access requires VPN authentication.

**Requirements**:
- OpenVPN certificate + password
- Strong password policy
- Certificate expiration monitoring
- Regular certificate rotation

#### Role-Based Access

**Policy**: Users have access only to VLANs required for their role.

**Roles and Access**:
- **Admin**: Full access to all VLANs
- **Developer**: Access to Web Services, Storage (read-only)
- **User**: Access to Web Services only
- **Guest**: Internet only (no internal access)

#### Time-Based Access

**Policy**: Optional time-based access restrictions.

**Implementation**:
- Schedule-based firewall rules
- Business hours access
- After-hours restrictions
- Emergency override procedures

## Bandwidth Management

### QoS Configuration

**Policy**: Prioritize critical services and limit non-essential traffic.

#### Priority Levels

1. **Critical** (Highest Priority):
   - Management network traffic
   - Database replication
   - Backup operations
   - VPN traffic

2. **High Priority**:
   - Web Services API traffic
   - User authentication
   - Monitoring traffic

3. **Normal Priority**:
   - General web traffic
   - File transfers
   - Media streaming

4. **Low Priority**:
   - Guest network
   - IoT device updates
   - Background sync

#### Bandwidth Limits

**Per-VLAN Limits**:
- **Management**: No limit (critical)
- **DMZ**: 100 Mbps
- **Web Services**: 500 Mbps
- **Database**: 1 Gbps (internal)
- **Storage**: 1 Gbps (internal)
- **IoT**: 10 Mbps per device
- **Guest**: 5 Mbps per device, 50 Mbps total

**Implementation**:
- Configure traffic shaper in pfSense
- Set up queues per VLAN
- Monitor and adjust as needed

### Rate Limiting

**Policy**: Implement rate limiting to prevent abuse.

**Rules**:
- **API Endpoints**: 100 requests/minute per IP
- **Authentication**: 5 attempts/minute per IP
- **File Uploads**: 10 MB/minute per user
- **Database Queries**: 1000 queries/minute per service

**Implementation**:
- Use security service rate limiting
- Configure pfSense rate limit rules
- Monitor and alert on violations

## Intrusion Detection and Prevention

### IDS/IPS Configuration

**Policy**: Monitor and block malicious traffic.

#### Suricata/Snort Setup

1. **Install IDS Package**:
   - System → Package Manager
   - Install: Suricata or Snort

2. **Configure Rules**:
   - Enable rule sets:
     - ET Open Rules
     - Emerging Threats
     - Custom rules
   - Update rules daily

3. **Interfaces**:
   - Monitor WAN interface
   - Monitor DMZ interface
   - Optional: Monitor internal VLANs

4. **Alerting**:
   - Email alerts for high-severity events
   - Security service integration
   - SIEM integration

#### Detection Rules

**High Priority Alerts**:
- Port scans
- Brute force attacks
- SQL injection attempts
- XSS attempts
- DDoS attacks
- Malware signatures

**Response Actions**:
- Automatic IP blocking for severe threats
- Alert security team
- Log all events
- Generate incident reports

### Anomaly Detection

**Policy**: Detect unusual network patterns.

**Monitored Patterns**:
- Unusual traffic volumes
- Uncommon port usage
- Suspicious connection patterns
- Geographic anomalies
- Time-based anomalies

**Implementation**:
- Security service anomaly detection
- Machine learning models
- Baseline comparison
- Alert on deviations

## Firewall Policies

### Default Deny

**Policy**: All traffic blocked by default.

**Implementation**:
- Default deny rule at end of each VLAN
- Explicit allow rules only
- Regular rule review
- Document all exceptions

### Stateful Inspection

**Policy**: Use stateful packet inspection.

**Configuration**:
- Enable stateful firewall
- Track connection states
- Timeout idle connections
- Limit state table size

### Anti-Spoofing

**Policy**: Prevent IP address spoofing.

**Configuration**:
- Enable anti-spoofing on all interfaces
- Block private networks on WAN
- Block bogon networks
- Verify source IP addresses

### SYN Flood Protection

**Policy**: Protect against SYN flood attacks.

**Configuration**:
- Enable SYN flood protection
- Set connection limits
- Configure timeouts
- Monitor for attacks

## Access Control Policies

### Management Network Access

**Policy**: Strict access control to management network.

**Rules**:
- VPN authentication required
- 2FA for admin access
- Log all access attempts
- Time-based restrictions
- IP allowlist (optional)

### Database Network Access

**Policy**: Database network completely isolated.

**Rules**:
- Only Web Services can access
- Management network for admin only
- No internet access
- Encrypted connections only
- Audit all access

### Storage Network Access

**Policy**: Controlled access to storage network.

**Rules**:
- Web Services can read/write
- Management network read-only
- Encrypted protocols only
- Access logging enabled
- Regular access reviews

### IoT Network Isolation

**Policy**: Complete isolation of IoT devices.

**Rules**:
- Outbound internet only
- No internal network access
- Device authentication
- Traffic monitoring
- Anomaly detection

### Guest Network Isolation

**Policy**: Complete isolation of guest network.

**Rules**:
- Internet access only
- No internal network access
- Rate limiting enabled
- Bandwidth caps
- Captive portal (optional)

## Security Monitoring

### Logging Requirements

**Policy**: Comprehensive logging of all network activity.

**Log Sources**:
- Firewall logs
- IDS/IPS alerts
- VPN connection logs
- Authentication logs
- Traffic statistics

**Retention**:
- Firewall logs: 90 days
- Security events: 1 year
- Audit logs: 1 year
- Traffic statistics: 30 days

### Alerting

**Policy**: Immediate alerts for security events.

**Alert Levels**:
- **Critical**: Immediate response required
- **High**: Response within 1 hour
- **Medium**: Response within 24 hours
- **Low**: Review during next audit

**Alert Channels**:
- Email
- Security service
- SIEM system
- PagerDuty (for critical)

### Incident Response

**Policy**: Defined procedures for security incidents.

**Procedures**:
1. Detect and identify incident
2. Contain threat
3. Eradicate threat
4. Recover systems
5. Post-incident review

**Automated Response**:
- Automatic IP blocking
- Rule updates
- Service isolation
- Alert escalation

## Compliance and Auditing

### Access Reviews

**Policy**: Regular review of network access.

**Schedule**:
- Monthly: Review firewall rules
- Quarterly: Review user access
- Annually: Full security audit

### Change Management

**Policy**: All network changes must be documented.

**Requirements**:
- Change request form
- Approval process
- Testing procedures
- Rollback plan
- Documentation update

### Audit Logging

**Policy**: Audit all administrative actions.

**Logged Actions**:
- Firewall rule changes
- User access changes
- Configuration changes
- Policy updates
- Security events

## Backup and Recovery

### Configuration Backup

**Policy**: Regular backup of network configuration.

**Schedule**:
- Daily: Automated backup
- Weekly: Manual verification
- Monthly: Off-site backup

**Backup Contents**:
- pfSense configuration
- Firewall rules
- VPN certificates
- Network topology
- Documentation

### Disaster Recovery

**Policy**: Maintain disaster recovery procedures.

**Requirements**:
- Recovery procedures documented
- Regular testing
- Off-site backups
- Recovery time objectives
- Recovery point objectives

## Policy Updates

### Review Schedule

- **Quarterly**: Review all policies
- **Annually**: Comprehensive policy review
- **As needed**: Update for new threats

### Change Process

1. Identify need for change
2. Document proposed change
3. Review and approve
4. Implement change
5. Test and verify
6. Update documentation

## Enforcement

### Violations

**Policy**: Violations of security policies are not tolerated.

**Consequences**:
- Immediate access revocation
- Incident investigation
- Disciplinary action
- Legal action if necessary

### Exceptions

**Policy**: Exceptions require approval.

**Process**:
1. Submit exception request
2. Risk assessment
3. Management approval
4. Document exception
5. Regular review

## References

- [Network VLAN Design](NETWORK_VLAN_DESIGN.md)
- [pfSense Configuration Guide](PFSENSE_CONFIGURATION.md)
- [Security Framework](SECURITY_FRAMEWORK.md)
- [Deployment Guide](DEPLOYMENT.md)
