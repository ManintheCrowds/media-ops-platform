#!/bin/bash
# VLAN Setup Script
# This script helps configure VLAN interfaces on the host system
# for Docker macvlan networks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PARENT_INTERFACE="eth0"  # Change to your actual interface
VLANS=(10 20 30 40 50 60 70)

echo -e "${GREEN}VLAN Setup Script${NC}"
echo "This script will configure VLAN interfaces for Docker macvlan networks"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Check if vlan package is installed
if ! command -v vconfig &> /dev/null && ! command -v ip &> /dev/null; then
    echo -e "${YELLOW}Installing vlan package...${NC}"
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y vlan
    elif command -v yum &> /dev/null; then
        yum install -y vconfig
    else
        echo -e "${RED}Could not determine package manager. Please install vlan package manually.${NC}"
        exit 1
    fi
fi

# Load 8021q module
echo -e "${GREEN}Loading 802.1Q module...${NC}"
modprobe 8021q || echo -e "${YELLOW}Module may already be loaded${NC}"

# Create VLAN interfaces
for vlan in "${VLANS[@]}"; do
    vlan_interface="${PARENT_INTERFACE}.${vlan}"
    
    if ip link show "$vlan_interface" &> /dev/null; then
        echo -e "${YELLOW}VLAN $vlan interface already exists${NC}"
    else
        echo -e "${GREEN}Creating VLAN $vlan interface...${NC}"
        ip link add link "$PARENT_INTERFACE" name "$vlan_interface" type vlan id "$vlan"
        ip link set "$vlan_interface" up
        echo "Created $vlan_interface"
    fi
done

# Make VLANs persistent (add to /etc/network/interfaces or systemd-networkd)
echo -e "${GREEN}Configuring persistent VLAN interfaces...${NC}"

# Detect network configuration system
if [ -d "/etc/systemd/network" ]; then
    # systemd-networkd
    for vlan in "${VLANS[@]}"; do
        vlan_interface="${PARENT_INTERFACE}.${vlan}"
        config_file="/etc/systemd/network/${vlan_interface}.netdev"
        
        if [ ! -f "$config_file" ]; then
            cat > "$config_file" <<EOF
[NetDev]
Name=$vlan_interface
Kind=vlan

[VLAN]
Id=$vlan
EOF
            echo "Created systemd-networkd config for $vlan_interface"
        fi
    done
elif [ -f "/etc/network/interfaces" ]; then
    # Debian/Ubuntu networking
    for vlan in "${VLANS[@]}"; do
        vlan_interface="${PARENT_INTERFACE}.${vlan}"
        if ! grep -q "$vlan_interface" /etc/network/interfaces; then
            cat >> /etc/network/interfaces <<EOF

# VLAN $vlan
auto $vlan_interface
iface $vlan_interface inet manual
    vlan-raw-device $PARENT_INTERFACE
EOF
            echo "Added $vlan_interface to /etc/network/interfaces"
        fi
    fi
fi

echo -e "${GREEN}VLAN setup complete!${NC}"
echo ""
echo "VLAN interfaces created:"
for vlan in "${VLANS[@]}"; do
    vlan_interface="${PARENT_INTERFACE}.${vlan}"
    if ip link show "$vlan_interface" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $vlan_interface (VLAN $vlan)"
    else
        echo -e "  ${RED}✗${NC} $vlan_interface (VLAN $vlan) - Failed"
    fi
done

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Configure pfSense VLAN interfaces"
echo "2. Configure managed switch for VLAN tagging"
echo "3. Update docker-compose.vlans.yml with correct parent interface"
echo "4. Start Docker services with VLAN networks"
