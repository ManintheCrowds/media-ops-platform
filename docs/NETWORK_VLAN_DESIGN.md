# Network VLAN Design Documentation

## Overview

This document provides detailed specifications for the VLAN-based network architecture designed for the self-hosted platform infrastructure. The design implements network segmentation for security, service isolation, and traffic management.

## Network Topology

### Physical Architecture

```
Internet (WAN)
    |
    v
[pfSense Firewall/Router]
    |
    +---> [Managed Switch] (802.1Q VLAN-capable)
            |
            +---> VLAN 10: Management (10.0.10.0/24)
            +---> VLAN 20: DMZ (10.0.20.0/24)
            +---> VLAN 30: Web Services (10.0.30.0/24)
            +---> VLAN 40: Database (10.0.40.0/24)
            +---> VLAN 50: Storage (10.0.50.0/24)
            +---> VLAN 60: IoT/Cameras (10.0.60.0/24)
            +---> VLAN 70: Guest Network (10.0.70.0/24)
            +---> VLAN 100: Infrastructure (10.0.100.0/24)
```

## VLAN Specifications

### VLAN 10 - Management Network

**Network**: 10.0.10.0/24  
**Gateway**: 10.0.10.1  
**VLAN ID**: 10  
**Purpose**: Network infrastructure management and monitoring

**IP Allocation**:
- 10.0.10.1 - pfSense gateway
- 10.0.10.10 - Prometheus
- 10.0.10.20 - Grafana
- 10.0.10.30-10.0.10.50 - Reserved for network equipment
- 10.0.10.100-10.0.10.200 - DHCP range (if needed)

**Services**:
- Prometheus (monitoring)
- Grafana (dashboards)
- Network management tools
- pfSense admin interface (restricted)

**Access Rules**:
- VPN users → Management: Full access (authenticated)
- Management → All VLANs: Monitoring/admin access
- All VLANs → Management: Blocked (except authorized)
- Management → Internet: Allowed (updates, external monitoring)

**Security**:
- Strictest access controls
- VPN authentication required
- Log all access attempts
- 2FA for admin access

### VLAN 20 - DMZ (Demilitarized Zone)

**Network**: 10.0.20.0/24  
**Gateway**: 10.0.20.1  
**VLAN ID**: 20  
**Purpose**: Public-facing services exposed to internet

**IP Allocation**:
- 10.0.20.1 - pfSense gateway
- 10.0.20.10 - Nginx reverse proxy
- 10.0.20.20-10.0.20.50 - Reserved for additional public services

**Services**:
- Nginx reverse proxy (public interface)
- Public service endpoints

**Access Rules**:
- Internet → DMZ: HTTP (80), HTTPS (443) only
- DMZ → VLAN 30 (Web Services): Ports 80, 443, 8000
- DMZ → Internet: Allowed (Let's Encrypt, updates)
- DMZ → All other VLANs: Blocked

**Security**:
- Minimal services exposed
- Regular security updates
- Intrusion detection enabled
- Rate limiting on public ports

### VLAN 30 - Web Services

**Network**: 10.0.30.0/24  
**Gateway**: 10.0.30.1  
**VLAN ID**: 30  
**Purpose**: Application services and platform API

**IP Allocation**:
- 10.0.30.1 - pfSense gateway
- 10.0.30.10 - Platform API
- 10.0.30.20 - Education Service
- 10.0.30.30 - Security Service
- 10.0.30.40 - Jellyfin
- 10.0.30.50 - Gitea
- 10.0.30.60 - BookStack
- 10.0.30.70 - Vaultwarden
- 10.0.30.80 - Redis
- 10.0.30.100-10.0.30.200 - DHCP range (if needed)

**Services**:
- Platform API
- Education Service
- Security Service
- Jellyfin (media server)
- Gitea (git service)
- BookStack (wiki)
- Vaultwarden (password manager)
- Redis (cache/rate limiting)

**Access Rules**:
- VLAN 20 (DMZ) → Web Services: Ports 80, 443, 8000
- Web Services → VLAN 40 (Database): Ports 5432, 3306
- Web Services → VLAN 50 (Storage): Ports 80, 8082, NFS/SMB
- Web Services → VLAN 10 (Management): Ports 9090, 3000 (monitoring)
- Web Services → Internet: Blocked (except updates via proxy)

**Security**:
- No direct internet access
- All traffic through DMZ
- Application-level security required
- Regular vulnerability scanning

### VLAN 40 - Database

**Network**: 10.0.40.0/24  
**Gateway**: 10.0.40.1  
**VLAN ID**: 40  
**Purpose**: Database servers only

**IP Allocation**:
- 10.0.40.1 - pfSense gateway
- 10.0.40.10 - PostgreSQL (main)
- 10.0.40.20 - Seafile DB (MariaDB)
- 10.0.40.30 - Gitea DB (PostgreSQL)
- 10.0.40.40 - BookStack DB (MariaDB)
- 10.0.40.50 - Education DB (PostgreSQL)
- 10.0.40.100-10.0.40.200 - Reserved for additional databases

**Services**:
- All database containers
- Database backup services

**Access Rules**:
- VLAN 30 (Web Services) → Database: Ports 5432, 3306
- VLAN 10 (Management) → Database: Monitoring/admin access
- Database → All VLANs: Blocked
- Database → Internet: Blocked

**Security**:
- Most restrictive access
- No internet connectivity
- Encrypted database connections
- Regular backups
- Access logging enabled

### VLAN 50 - Storage

**Network**: 10.0.50.0/24  
**Gateway**: 10.0.50.1  
**VLAN ID**: 50  
**Purpose**: File storage and NAS

**IP Allocation**:
- 10.0.50.1 - pfSense gateway
- 10.0.50.10 - Seafile
- 10.0.50.20 - Drobo NAS (physical)
- 10.0.50.30-10.0.50.50 - Reserved for additional storage

**Services**:
- Seafile (file storage service)
- Drobo NAS (physical storage)
- File sharing services

**Access Rules**:
- VLAN 30 (Web Services) → Storage: Storage ports (80, 8082, NFS, SMB)
- Storage → VLAN 40 (Database): Metadata operations
- VLAN 10 (Management) → Storage: Admin access
- Storage → Internet: Blocked

**Security**:
- Encrypted storage protocols
- Access control lists
- Regular integrity checks
- Backup verification

### VLAN 60 - IoT/Cameras

**Network**: 10.0.60.0/24  
**Gateway**: 10.0.60.1  
**VLAN ID**: 60  
**Purpose**: Isolated IoT devices and security cameras

**IP Allocation**:
- 10.0.60.1 - pfSense gateway
- 10.0.60.10-10.0.60.50 - Security cameras
- 10.0.60.100-10.0.60.200 - DHCP range for IoT devices

**Services**:
- Security cameras
- IoT sensors
- Smart home devices (if any)

**Access Rules**:
- IoT → Internet: Outbound only (NTP, updates)
- IoT → All internal VLANs: Blocked
- VLAN 10 (Management) → IoT: Monitoring only (read-only)

**Security**:
- Complete isolation from internal networks
- Outbound internet only
- Device authentication
- Traffic monitoring for anomalies

### VLAN 70 - Guest Network

**Network**: 10.0.70.0/24  
**Gateway**: 10.0.70.1  
**VLAN ID**: 70  
**Purpose**: Guest internet access

**IP Allocation**:
- 10.0.70.1 - pfSense gateway
- 10.0.70.100-10.0.70.200 - DHCP range

**Services**:
- None (internet access only)

**Access Rules**:
- Guest → Internet: Allowed (outbound only)
- Guest → All internal VLANs: Blocked
- All VLANs → Guest: Blocked

**Security**:
- Complete isolation
- Rate limiting enabled
- Bandwidth caps
- No access to internal resources
- Captive portal (optional)

### VLAN 100 - Infrastructure

**Network**: 10.0.100.0/24  
**Gateway**: 10.0.100.1  
**VLAN ID**: 100  
**Purpose**: Network infrastructure (optional, for advanced setups)

**IP Allocation**:
- 10.0.100.1 - pfSense gateway
- 10.0.100.10-10.0.100.50 - Network equipment

**Services**:
- Switch management
- Router management
- Network monitoring tools

**Access Rules**:
- Management network only
- Restricted access

## Inter-VLAN Communication Matrix

| Source VLAN | Destination VLAN | Allowed Ports | Purpose |
|-------------|------------------|---------------|---------|
| Internet | VLAN 20 (DMZ) | 80, 443 | Public web access |
| VLAN 20 (DMZ) | VLAN 30 (Web) | 80, 443, 8000 | Reverse proxy to services |
| VLAN 30 (Web) | VLAN 40 (DB) | 5432, 3306 | Database access |
| VLAN 30 (Web) | VLAN 50 (Storage) | 80, 8082, NFS, SMB | Storage access |
| VLAN 30 (Web) | VLAN 10 (Mgmt) | 9090, 3000 | Monitoring |
| VLAN 50 (Storage) | VLAN 40 (DB) | 5432, 3306 | Metadata operations |
| VLAN 10 (Mgmt) | All VLANs | Various | Admin/monitoring |
| VPN | VLAN 10 (Mgmt) | All | Admin access |
| VPN | VLAN 30 (Web) | 80, 443 | Service access |
| All others | All others | Blocked | Security isolation |

## Service Placement Matrix

| Service | Container Name | VLAN | IP Address | Ports |
|---------|---------------|------|------------|-------|
| Nginx | platform-nginx | VLAN 20 | 10.0.20.10 | 80, 443 |
| Platform API | platform-api | VLAN 30 | 10.0.30.10 | 8000 |
| Education Service | platform-education | VLAN 30 | 10.0.30.20 | 8000 |
| Security Service | platform-security | VLAN 30 | 10.0.30.30 | 8001 |
| Jellyfin | platform-jellyfin | VLAN 30 | 10.0.30.40 | 8096, 8920 |
| Gitea | platform-gitea | VLAN 30 | 10.0.30.50 | 3000, 22 |
| BookStack | platform-bookstack | VLAN 30 | 10.0.30.60 | 80 |
| Vaultwarden | platform-vaultwarden | VLAN 30 | 10.0.30.70 | 80, 3012 |
| Redis | platform-redis | VLAN 30 | 10.0.30.80 | 6379 |
| PostgreSQL | platform-postgres | VLAN 40 | 10.0.40.10 | 5432 |
| Seafile DB | platform-seafile-db | VLAN 40 | 10.0.40.20 | 3306 |
| Gitea DB | platform-gitea-db | VLAN 40 | 10.0.40.30 | 5432 |
| BookStack DB | platform-bookstack-db | VLAN 40 | 10.0.40.40 | 3306 |
| Education DB | platform-education-db | VLAN 40 | 10.0.40.50 | 5432 |
| Seafile | platform-seafile | VLAN 50 | 10.0.50.10 | 80, 8082 |
| Drobo NAS | Physical | VLAN 50 | 10.0.50.20 | NFS, SMB |
| Prometheus | platform-prometheus | VLAN 10 | 10.0.10.10 | 9090 |
| Grafana | platform-grafana | VLAN 10 | 10.0.10.20 | 3000 |

## DHCP Configuration

### VLAN 10 (Management)
- **Enabled**: Optional (static IPs recommended)
- **Range**: 10.0.10.100-10.0.10.200
- **Lease Time**: 24 hours
- **DNS**: 10.0.10.1 (pfSense)

### VLAN 20 (DMZ)
- **Enabled**: No (static IPs required)
- **Allocation**: Static only

### VLAN 30 (Web Services)
- **Enabled**: Optional
- **Range**: 10.0.30.100-10.0.30.200
- **Lease Time**: 12 hours
- **DNS**: 10.0.30.1 (pfSense)

### VLAN 40 (Database)
- **Enabled**: No (static IPs required)
- **Allocation**: Static only

### VLAN 50 (Storage)
- **Enabled**: No (static IPs required)
- **Allocation**: Static only

### VLAN 60 (IoT)
- **Enabled**: Yes
- **Range**: 10.0.60.100-10.0.60.200
- **Lease Time**: 24 hours
- **DNS**: 8.8.8.8, 1.1.1.1 (public DNS)

### VLAN 70 (Guest)
- **Enabled**: Yes
- **Range**: 10.0.70.100-10.0.70.200
- **Lease Time**: 4 hours
- **DNS**: 8.8.8.8, 1.1.1.1 (public DNS)

## DNS Configuration

### Internal DNS (pfSense Resolver)

**Host Overrides**:
- `platform.internal` → 10.0.30.10
- `seafile.internal` → 10.0.50.10
- `db.internal` → 10.0.40.10
- `monitoring.internal` → 10.0.10.10
- `grafana.internal` → 10.0.10.20
- `jellyfin.internal` → 10.0.30.40
- `gitea.internal` → 10.0.30.50
- `bookstack.internal` → 10.0.30.60
- `vaultwarden.internal` → 10.0.30.70

**Domain Override**:
- `.internal` → pfSense resolver

### External DNS

- Primary: 8.8.8.8 (Google)
- Secondary: 1.1.1.1 (Cloudflare)
- DNS over HTTPS (DoH): Enabled for security

## Network Security Policies

### General Principles

1. **Default Deny**: All traffic blocked by default
2. **Least Privilege**: Minimum access required
3. **Defense in Depth**: Multiple security layers
4. **Monitoring**: Log all network activity
5. **Regular Audits**: Review and update rules

### VLAN-Specific Policies

**Management VLAN (10)**:
- VPN authentication required
- 2FA for admin access
- Log all access attempts
- Regular security audits

**DMZ (20)**:
- Minimal services exposed
- Regular security updates
- Intrusion detection
- Rate limiting

**Web Services (30)**:
- No direct internet access
- Application-level security
- Regular vulnerability scanning
- Access logging

**Database (40)**:
- Most restrictive access
- Encrypted connections only
- No internet connectivity
- Regular backups

**Storage (50)**:
- Encrypted protocols
- Access control lists
- Integrity verification
- Backup verification

**IoT (60)**:
- Complete isolation
- Outbound internet only
- Device authentication
- Anomaly detection

**Guest (70)**:
- Complete isolation
- Rate limiting
- Bandwidth caps
- No internal access

## Implementation Notes

### Switch Configuration

- Enable 802.1Q VLAN tagging
- Configure trunk ports between switch and pfSense
- Set up access ports for each VLAN
- Enable port security where applicable

### pfSense Configuration

- Create VLAN interfaces for each network
- Assign IP addresses to gateways
- Configure DHCP servers (where needed)
- Set up firewall rules per VLAN
- Configure NAT and port forwarding

### Docker Integration

- Use macvlan networks for VLAN assignment
- Map Docker networks to VLAN interfaces
- Update service configurations with new IPs
- Test connectivity after migration

## Troubleshooting

### Common Issues

1. **VLAN Isolation Not Working**
   - Verify switch VLAN configuration
   - Check pfSense VLAN interfaces
   - Verify firewall rules

2. **Inter-VLAN Communication Failing**
   - Check firewall rules
   - Verify routing configuration
   - Test with ping/traceroute

3. **DHCP Not Working**
   - Verify DHCP server enabled
   - Check IP ranges
   - Verify gateway configuration

4. **DNS Resolution Issues**
   - Check DNS resolver configuration
   - Verify host overrides
   - Test with nslookup

## Maintenance

### Regular Tasks

- Review firewall logs weekly
- Monitor traffic patterns
- Update firewall rules as needed
- Review VLAN assignments
- Audit access controls

### Backup

- Backup pfSense configuration
- Document network changes
- Maintain network diagrams
- Keep IP allocation records

## Future Enhancements

1. **802.1X Authentication**: Network access control
2. **Dynamic VLAN Assignment**: Based on user/device
3. **SDN Integration**: Software-defined networking
4. **Zero Trust**: Implement zero-trust model
5. **Network Automation**: Automated rule management
