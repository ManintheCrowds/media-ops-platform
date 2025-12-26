# Network Configuration Scripts

Scripts for setting up VLAN-based network architecture.

## Purpose and Scope

These scripts configure the network infrastructure for the self-hosted platform:
- **VLAN Setup**: Configure VLAN interfaces for Docker macvlan networks
- **pfSense Integration**: Set up API access for security service firewall automation
- **Network Segmentation**: Support VLAN-based service isolation

## Integration with Services

- **Security Service**: Uses pfSense API for firewall automation
- **Docker Services**: All services use VLAN-based macvlan networks
- **Platform Services**: Services isolated by VLAN for security

## Scripts

### vlan-setup.sh

Configures VLAN interfaces on the host system for Docker macvlan networks.

**Usage**:
```bash
sudo ./scripts/network/vlan-setup.sh
```

**Requirements**:
- Root access
- VLAN package installed
- 802.1Q kernel module

**What it does**:
- Creates VLAN interfaces (eth0.10, eth0.20, etc.)
- Configures persistent VLAN setup
- Sets up for Docker macvlan networks

### pfsense-api-setup.sh

Helps configure pfSense API access for the security service.

**Usage**:
```bash
./scripts/network/pfsense-api-setup.sh
```

**What it does**:
- Provides instructions for enabling pfSense API
- Generates example configuration
- Creates .env.pfsense.example file

## Prerequisites

Before running scripts:

1. **Configure pfSense**: Set up VLAN interfaces in pfSense
2. **Configure Switch**: Set up 802.1Q VLAN tagging on managed switch
3. **Update Scripts**: Modify parent interface name if needed (default: eth0)

## Documentation

See [Network VLAN Design](../../docs/NETWORK_VLAN_DESIGN.md) for detailed architecture.
