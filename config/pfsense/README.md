# pfSense Configuration Files

This directory contains configuration templates and reference files for pfSense firewall/router setup.

## Files

- **vlan-config.xml** - VLAN interface configuration template
- **firewall-rules.xml** - Firewall rules configuration template
- **openvpn-server.conf** - OpenVPN server configuration template
- **monitoring-config.md** - Monitoring and Prometheus integration guide

## Usage

These files are reference templates. For actual configuration:

1. **VLAN Configuration**: Use the pfSense web interface to create VLANs (see [PFSENSE_CONFIGURATION.md](../../docs/PFSENSE_CONFIGURATION.md))
2. **Firewall Rules**: Configure rules via the web interface for best compatibility
3. **OpenVPN**: Use the web interface to set up OpenVPN server
4. **Monitoring**: Follow the monitoring-config.md guide

## Documentation

For detailed setup instructions, see:
- [Network VLAN Design](../../docs/NETWORK_VLAN_DESIGN.md)
- [pfSense Configuration Guide](../../docs/PFSENSE_CONFIGURATION.md)
- [Security Policies](../../docs/SECURITY_POLICIES.md)

## Scripts

Network setup scripts are in `../../scripts/network/`:
- `vlan-setup.sh` - Configure VLAN interfaces on host
- `pfsense-api-setup.sh` - Configure pfSense API access
