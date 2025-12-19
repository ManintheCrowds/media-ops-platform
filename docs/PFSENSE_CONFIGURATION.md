# pfSense Configuration Guide

## Overview

This guide provides step-by-step instructions for configuring pfSense firewall/router for the self-hosted platform infrastructure, including VLAN setup, firewall rules, VPN configuration, and security hardening.

## Prerequisites

- pfSense installed on hardware or VM
- Managed switch with 802.1Q VLAN support
- Network cables and physical connections
- Admin access to pfSense web interface
- List of services and IP addresses

## Initial Setup

### 1. First Boot and Basic Configuration

1. **Boot pfSense**
   - Connect to console or use web interface
   - Default IP: 192.168.1.1
   - Default credentials: admin/pfsense

2. **Run Setup Wizard**
   - Navigate to: System → Setup Wizard
   - Follow prompts for:
     - Hostname: `pfsense` (or your choice)
     - Domain: `internal` (or your domain)
     - DNS servers: 8.8.8.8, 1.1.1.1
     - Timezone: Your timezone
     - WAN interface: Configure with ISP settings
     - LAN interface: Configure initial network (10.0.1.0/24)

3. **Change Admin Password**
   - System → User Manager → Admin
   - Set strong password
   - Enable 2FA (recommended)

4. **Update pfSense**
   - System → Update
   - Update to latest version
   - Reboot if required

### 2. WAN Interface Configuration

1. **Navigate to Interfaces → WAN**
2. **Configure Settings**:
   - **Type**: DHCP (or Static if ISP provides static IP)
   - **MAC Address**: Use default or clone if needed
   - **MTU**: 1500 (or as required by ISP)
   - **Block Private Networks**: Enabled
   - **Block Bogon Networks**: Enabled

3. **Advanced Settings**:
   - **Gateway Monitoring**: Enable
   - **Monitor IP**: 8.8.8.8 (or ISP gateway)

4. **Save and Apply**

### 3. Initial LAN Interface

1. **Navigate to Interfaces → LAN**
2. **Configure Settings**:
   - **IPv4 Configuration Type**: Static IPv4
   - **IPv4 Address**: 10.0.1.1/24 (temporary)
   - **Description**: Initial LAN

3. **Save and Apply**

## VLAN Configuration

### Step 1: Enable VLAN Support

1. **Navigate to Interfaces → Assignments → VLANs**
2. **Click "Add"** to create each VLAN

### Step 2: Create VLAN Interfaces

#### VLAN 10 - Management

1. **Create VLAN**:
   - **Parent Interface**: LAN
   - **VLAN Tag**: 10
   - **Description**: Management Network
   - **Save**

2. **Assign Interface**:
   - Go to Interfaces → Assignments
   - Add new interface: `opt1` (or next available)
   - Select: `VLAN 10 on LAN`
   - Enable interface
   - **IPv4 Configuration Type**: Static IPv4
   - **IPv4 Address**: 10.0.10.1/24
   - **Description**: Management
   - **Save**

#### VLAN 20 - DMZ

1. **Create VLAN**:
   - **Parent Interface**: LAN
   - **VLAN Tag**: 20
   - **Description**: DMZ Network
   - **Save**

2. **Assign Interface**:
   - Add new interface: `opt2`
   - Select: `VLAN 20 on LAN`
   - Enable interface
   - **IPv4 Configuration Type**: Static IPv4
   - **IPv4 Address**: 10.0.20.1/24
   - **Description**: DMZ
   - **Save**

#### VLAN 30 - Web Services

1. **Create VLAN**:
   - **Parent Interface**: LAN
   - **VLAN Tag**: 30
   - **Description**: Web Services Network
   - **Save**

2. **Assign Interface**:
   - Add new interface: `opt3`
   - Select: `VLAN 30 on LAN`
   - Enable interface
   - **IPv4 Configuration Type**: Static IPv4
   - **IPv4 Address**: 10.0.30.1/24
   - **Description**: Web Services
   - **Save**

#### VLAN 40 - Database

1. **Create VLAN**:
   - **Parent Interface**: LAN
   - **VLAN Tag**: 40
   - **Description**: Database Network
   - **Save**

2. **Assign Interface**:
   - Add new interface: `opt4`
   - Select: `VLAN 40 on LAN`
   - Enable interface
   - **IPv4 Configuration Type**: Static IPv4
   - **IPv4 Address**: 10.0.40.1/24
   - **Description**: Database
   - **Save**

#### VLAN 50 - Storage

1. **Create VLAN**:
   - **Parent Interface**: LAN
   - **VLAN Tag**: 50
   - **Description**: Storage Network
   - **Save**

2. **Assign Interface**:
   - Add new interface: `opt5`
   - Select: `VLAN 50 on LAN`
   - Enable interface
   - **IPv4 Configuration Type**: Static IPv4
   - **IPv4 Address**: 10.0.50.1/24
   - **Description**: Storage
   - **Save**

#### VLAN 60 - IoT/Cameras

1. **Create VLAN**:
   - **Parent Interface**: LAN
   - **VLAN Tag**: 60
   - **Description**: IoT Network
   - **Save**

2. **Assign Interface**:
   - Add new interface: `opt6`
   - Select: `VLAN 60 on LAN`
   - Enable interface
   - **IPv4 Configuration Type**: Static IPv4
   - **IPv4 Address**: 10.0.60.1/24
   - **Description**: IoT
   - **Save**

#### VLAN 70 - Guest

1. **Create VLAN**:
   - **Parent Interface**: LAN
   - **VLAN Tag**: 70
   - **Description**: Guest Network
   - **Save**

2. **Assign Interface**:
   - Add new interface: `opt7`
   - Select: `VLAN 70 on LAN`
   - Enable interface
   - **IPv4 Configuration Type**: Static IPv4
   - **IPv4 Address**: 10.0.70.1/24
   - **Description**: Guest
   - **Save**

### Step 3: Configure DHCP Servers (Optional)

For VLANs that need DHCP:

1. **Navigate to Services → DHCP Server**
2. **Select VLAN interface** (e.g., VLAN 30)
3. **Enable DHCP Server**
4. **Configure**:
   - **Range**: 10.0.30.100 - 10.0.30.200
   - **Gateway**: 10.0.30.1
   - **DNS Servers**: 10.0.30.1 (pfSense)
   - **Lease Time**: 12 hours
5. **Save**

Repeat for other VLANs as needed (IoT, Guest).

## Firewall Rules Configuration

### VLAN 20 (DMZ) - Inbound Rules

1. **Navigate to Firewall → Rules → DMZ**
2. **Create Rule**:
   - **Action**: Pass
   - **Interface**: DMZ
   - **Protocol**: TCP
   - **Source**: Any
   - **Destination**: DMZ address (10.0.20.10)
   - **Destination Port**: 80 (HTTP)
   - **Description**: Allow HTTP to Nginx
   - **Save**

3. **Create Rule**:
   - **Action**: Pass
   - **Interface**: DMZ
   - **Protocol**: TCP
   - **Source**: Any
   - **Destination**: DMZ address (10.0.20.10)
   - **Destination Port**: 443 (HTTPS)
   - **Description**: Allow HTTPS to Nginx
   - **Save**

4. **Create Default Deny Rule** (at bottom):
   - **Action**: Block
   - **Interface**: DMZ
   - **Protocol**: Any
   - **Source**: Any
   - **Destination**: Any
   - **Description**: Block all other inbound
   - **Save**

### VLAN 20 (DMZ) - Outbound Rules

1. **Create Rule**:
   - **Action**: Pass
   - **Interface**: DMZ
   - **Protocol**: TCP
   - **Source**: DMZ net
   - **Destination**: Web Services net (10.0.30.0/24)
   - **Destination Port**: 80, 443, 8000
   - **Description**: Allow DMZ to Web Services
   - **Save**

2. **Create Rule**:
   - **Action**: Pass
   - **Interface**: DMZ
   - **Protocol**: TCP/UDP
   - **Source**: DMZ net
   - **Destination**: Any
   - **Description**: Allow DMZ to Internet (updates)
   - **Save**

### VLAN 30 (Web Services) - Rules

1. **Navigate to Firewall → Rules → Web Services**
2. **Create Rule** (Allow from DMZ):
   - **Action**: Pass
   - **Interface**: Web Services
   - **Protocol**: TCP
   - **Source**: DMZ net
   - **Destination**: Web Services net
   - **Destination Port**: 80, 443, 8000
   - **Description**: Allow DMZ to Web Services
   - **Save**

3. **Create Rule** (Allow to Database):
   - **Action**: Pass
   - **Interface**: Web Services
   - **Protocol**: TCP
   - **Source**: Web Services net
   - **Destination**: Database net
   - **Destination Port**: 5432, 3306
   - **Description**: Allow Web Services to Database
   - **Save**

4. **Create Rule** (Allow to Storage):
   - **Action**: Pass
   - **Interface**: Web Services
   - **Protocol**: TCP
   - **Source**: Web Services net
   - **Destination**: Storage net
   - **Destination Port**: 80, 8082
   - **Description**: Allow Web Services to Storage
   - **Save**

5. **Create Rule** (Allow to Management):
   - **Action**: Pass
   - **Interface**: Web Services
   - **Protocol**: TCP
   - **Source**: Web Services net
   - **Destination**: Management net
   - **Destination Port**: 9090, 3000
   - **Description**: Allow Web Services to Management (monitoring)
   - **Save**

6. **Create Default Deny Rule**:
   - **Action**: Block
   - **Interface**: Web Services
   - **Protocol**: Any
   - **Source**: Any
   - **Destination**: Any
   - **Description**: Block all other traffic
   - **Save**

### VLAN 40 (Database) - Rules

1. **Navigate to Firewall → Rules → Database**
2. **Create Rule** (Allow from Web Services):
   - **Action**: Pass
   - **Interface**: Database
   - **Protocol**: TCP
   - **Source**: Web Services net
   - **Destination**: Database net
   - **Destination Port**: 5432, 3306
   - **Description**: Allow Web Services to Database
   - **Save**

3. **Create Rule** (Allow from Management):
   - **Action**: Pass
   - **Interface**: Database
   - **Protocol**: TCP
   - **Source**: Management net
   - **Destination**: Database net
   - **Destination Port**: 5432, 3306
   - **Description**: Allow Management to Database (admin)
   - **Save**

4. **Create Default Deny Rule**:
   - **Action**: Block
   - **Interface**: Database
   - **Protocol**: Any
   - **Source**: Any
   - **Destination**: Any
   - **Description**: Block all other traffic
   - **Save**

### VLAN 50 (Storage) - Rules

1. **Navigate to Firewall → Rules → Storage**
2. **Create Rule** (Allow from Web Services):
   - **Action**: Pass
   - **Interface**: Storage
   - **Protocol**: TCP
   - **Source**: Web Services net
   - **Destination**: Storage net
   - **Destination Port**: 80, 8082
   - **Description**: Allow Web Services to Storage
   - **Save**

3. **Create Rule** (Allow to Database):
   - **Action**: Pass
   - **Interface**: Storage
   - **Protocol**: TCP
   - **Source**: Storage net
   - **Destination**: Database net
   - **Destination Port**: 5432, 3306
   - **Description**: Allow Storage to Database (metadata)
   - **Save**

4. **Create Rule** (Allow from Management):
   - **Action**: Pass
   - **Interface**: Storage
   - **Protocol**: TCP
   - **Source**: Management net
   - **Destination**: Storage net
   - **Description**: Allow Management to Storage (admin)
   - **Save**

5. **Create Default Deny Rule**:
   - **Action**: Block
   - **Interface**: Storage
   - **Protocol**: Any
   - **Source**: Any
   - **Destination**: Any
   - **Description**: Block all other traffic
   - **Save**

### VLAN 60 (IoT) - Rules

1. **Navigate to Firewall → Rules → IoT**
2. **Create Rule** (Allow to Internet):
   - **Action**: Pass
   - **Interface**: IoT
   - **Protocol**: Any
   - **Source**: IoT net
   - **Destination**: Any
   - **Description**: Allow IoT to Internet (outbound only)
   - **Save**

3. **Create Rule** (Allow from Management):
   - **Action**: Pass
   - **Interface**: IoT
   - **Protocol**: TCP
   - **Source**: Management net
   - **Destination**: IoT net
   - **Destination Port**: 80, 443
   - **Description**: Allow Management to IoT (monitoring)
   - **Save**

4. **Create Default Deny Rule**:
   - **Action**: Block
   - **Interface**: IoT
   - **Protocol**: Any
   - **Source**: Any
   - **Destination**: Any
   - **Description**: Block all other traffic
   - **Save**

### VLAN 70 (Guest) - Rules

1. **Navigate to Firewall → Rules → Guest**
2. **Create Rule** (Allow to Internet):
   - **Action**: Pass
   - **Interface**: Guest
   - **Protocol**: Any
   - **Source**: Guest net
   - **Destination**: Any
   - **Description**: Allow Guest to Internet
   - **Save**

3. **Create Default Deny Rule**:
   - **Action**: Block
   - **Interface**: Guest
   - **Protocol**: Any
   - **Source**: Any
   - **Destination**: Any
   - **Description**: Block all other traffic
   - **Save**

### VLAN 10 (Management) - Rules

1. **Navigate to Firewall → Rules → Management**
2. **Create Rule** (Allow from VPN):
   - **Action**: Pass
   - **Interface**: Management
   - **Protocol**: Any
   - **Source**: VPN net (10.0.200.0/24)
   - **Destination**: Management net
   - **Description**: Allow VPN to Management
   - **Save**

3. **Create Rule** (Allow to All VLANs):
   - **Action**: Pass
   - **Interface**: Management
   - **Protocol**: Any
   - **Source**: Management net
   - **Destination**: Any
   - **Description**: Allow Management to all VLANs (admin)
   - **Save**

4. **Create Rule** (Allow to Internet):
   - **Action**: Pass
   - **Interface**: Management
   - **Protocol**: Any
   - **Source**: Management net
   - **Destination**: Any
   - **Description**: Allow Management to Internet
   - **Save**

## NAT Configuration

### Port Forwarding Rules

1. **Navigate to Firewall → NAT → Port Forward**
2. **Add Rule** (HTTP):
   - **Interface**: WAN
   - **Protocol**: TCP
   - **Destination Port**: 80
   - **Redirect Target IP**: 10.0.20.10 (Nginx)
   - **Redirect Target Port**: 80
   - **Description**: Forward HTTP to Nginx
   - **Save**

3. **Add Rule** (HTTPS):
   - **Interface**: WAN
   - **Protocol**: TCP
   - **Destination Port**: 443
   - **Redirect Target IP**: 10.0.20.10 (Nginx)
   - **Redirect Target Port**: 443
   - **Description**: Forward HTTPS to Nginx
   - **Save**

4. **Add Rule** (OpenVPN):
   - **Interface**: WAN
   - **Protocol**: UDP
   - **Destination Port**: 1194
   - **Redirect Target IP**: pfSense (127.0.0.1)
   - **Redirect Target Port**: 1194
   - **Description**: Forward OpenVPN
   - **Save**

### Outbound NAT

1. **Navigate to Firewall → NAT → Outbound**
2. **Mode**: Automatic Outbound NAT
3. **Save**

## DNS Configuration

### Internal DNS (Resolver)

1. **Navigate to Services → DNS Resolver**
2. **Enable DNS Resolver**
3. **General Settings**:
   - **Network Interfaces**: Select all VLAN interfaces
   - **Outgoing Network Interfaces**: WAN
   - **DNS Query Forwarding**: Enabled

4. **Host Overrides**:
   - Click "Add"
   - **Host**: platform
   - **Domain**: internal
   - **IP Address**: 10.0.30.10
   - **Description**: Platform API
   - **Save**

   Repeat for other services:
   - seafile.internal → 10.0.50.10
   - db.internal → 10.0.40.10
   - monitoring.internal → 10.0.10.10
   - grafana.internal → 10.0.10.20

5. **Domain Overrides**:
   - Click "Add"
   - **Domain**: internal
   - **IP Address**: 10.0.10.1 (pfSense)
   - **Save**

### External DNS

1. **Navigate to System → General Setup**
2. **DNS Servers**:
   - Primary: 8.8.8.8
   - Secondary: 1.1.1.1
3. **Save**

## OpenVPN Configuration

### Step 1: Install OpenVPN Package

1. **Navigate to System → Package Manager**
2. **Available Packages** → Search: "openvpn"
3. **Install**: OpenVPN Client Export Utility (if needed)

### Step 2: Create Certificate Authority

1. **Navigate to System → Certificate Manager → CAs**
2. **Add**:
   - **Descriptive Name**: OpenVPN CA
   - **Method**: Create an internal Certificate Authority
   - **Key Length**: 4096
   - **Lifetime**: 3650 days
   - **Save**

### Step 3: Create Server Certificate

1. **Navigate to System → Certificate Manager → Certificates**
2. **Add**:
   - **Method**: Create an internal Certificate
   - **Descriptive Name**: OpenVPN Server
   - **Certificate Authority**: OpenVPN CA
   - **Key Length**: 4096
   - **Lifetime**: 3650 days
   - **Certificate Type**: Server Certificate
   - **Save**

### Step 4: Configure OpenVPN Server

1. **Navigate to VPN → OpenVPN → Servers**
2. **Add**:
   - **Disable this server**: Unchecked
   - **Server Mode**: Peer to Peer (SSL/TLS)
   - **Protocol**: UDP on IPv4
   - **Interface**: WAN
   - **Local Port**: 1194
   - **Description**: OpenVPN Server
   - **TLS Authentication**: Enable
   - **Peer Certificate Authority**: OpenVPN CA
   - **Server Certificate**: OpenVPN Server
   - **Encryption Algorithm**: AES-256-CBC
   - **Auth Digest Algorithm**: SHA256
   - **Tunnel Network**: 10.0.200.0/24
   - **Redirect Gateway**: Unchecked
   - **Local Network**: 10.0.10.0/24, 10.0.30.0/24
   - **DNS Server**: 10.0.10.1
   - **Save**

### Step 5: Create Client Certificates

1. **Navigate to System → Certificate Manager → Certificates**
2. **Add** (for each client):
   - **Method**: Create an internal Certificate
   - **Descriptive Name**: OpenVPN Client - [Username]
   - **Certificate Authority**: OpenVPN CA
   - **Key Length**: 4096
   - **Lifetime**: 3650 days
   - **Certificate Type**: User Certificate
   - **Save**

### Step 6: Export Client Configuration

1. **Navigate to VPN → OpenVPN → Client Export**
2. **Select Client**: Choose client certificate
3. **Export**: Download .ovpn file
4. **Distribute**: Provide to authorized users

### Step 7: Configure VPN Access Rules

1. **Navigate to Firewall → Rules → OpenVPN**
2. **Create Rules** (as specified in VLAN design):
   - VPN → Management: Full access
   - VPN → Web Services: HTTP/HTTPS
   - VPN → Storage: Read-only (optional)
   - Block VPN from Database and IoT

## Security Hardening

### 1. Enable HTTPS for Web Interface

1. **Navigate to System → Advanced → Admin Access**
2. **Protocol**: HTTPS
3. **Port**: 443
4. **Save**

### 2. Configure Anti-Spoofing

1. **Navigate to Interfaces → [Each VLAN] → Advanced**
2. **Block Private Networks**: Enabled (for WAN)
3. **Block Bogon Networks**: Enabled (for WAN)

### 3. Enable SYN Flood Protection

1. **Navigate to System → Advanced → Firewall & NAT**
2. **SYN Flood Protection**: Enable
3. **Save**

### 4. Configure Logging

1. **Navigate to System → Advanced → Logging**
2. **Enable Firewall Logging**: Yes
3. **Log Packets**: Blocked packets
4. **Save**

### 5. Set Up Intrusion Detection (Optional)

1. **Navigate to System → Package Manager**
2. **Install**: Suricata or Snort
3. **Configure**: Enable on WAN interface
4. **Rules**: Download and enable rule sets

## Monitoring and Maintenance

### Traffic Monitoring

1. **Navigate to Status → Traffic Graph**
2. **Select Interface**: Choose VLAN to monitor
3. **View**: Real-time traffic statistics

### Firewall Logs

1. **Navigate to Status → System Logs → Firewall**
2. **View**: Blocked/allowed connections
3. **Filter**: By interface, IP, port

### Backup Configuration

1. **Navigate to Diagnostics → Backup & Restore**
2. **Download**: Configuration XML
3. **Store**: Secure location
4. **Schedule**: Regular backups

## Troubleshooting

### Common Issues

1. **VLAN Not Working**
   - Verify switch VLAN configuration
   - Check pfSense VLAN interface assignment
   - Test with ping

2. **Firewall Blocking Traffic**
   - Check firewall rules order
   - Verify rule matches
   - Review firewall logs

3. **VPN Not Connecting**
   - Verify certificates
   - Check firewall rules
   - Test port 1194 accessibility

4. **DNS Not Resolving**
   - Check DNS resolver configuration
   - Verify host overrides
   - Test with nslookup

## API Configuration (for Security Service)

### Enable API Access

1. **Navigate to System → Advanced → API**
2. **Enable API**: Yes
3. **API Key**: Generate secure key
4. **Allowed IPs**: Security service IP (10.0.30.30)
5. **Save**

### API Documentation

- **Base URL**: `https://10.0.10.1/api/v1`
- **Authentication**: API key in header
- **Endpoints**: See pfSense API documentation

## Next Steps

After completing this configuration:

1. Test all VLAN connectivity
2. Verify firewall rules
3. Test VPN connectivity
4. Configure monitoring
5. Document network topology
6. Set up regular backups
