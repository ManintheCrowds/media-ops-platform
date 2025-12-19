#!/bin/bash
# pfSense API Setup Script
# This script helps configure pfSense API access for the security service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}pfSense API Setup Script${NC}"
echo "This script helps configure API access for the security service"
echo ""

# Configuration
PFSENSE_URL="${PFSENSE_URL:-https://10.0.10.1}"
SECURITY_SERVICE_IP="${SECURITY_SERVICE_IP:-10.0.30.30}"

echo "Configuration:"
echo "  pfSense URL: $PFSENSE_URL"
echo "  Security Service IP: $SECURITY_SERVICE_IP"
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}jq is not installed. Installing...${NC}"
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y jq
    elif command -v yum &> /dev/null; then
        yum install -y jq
    else
        echo -e "${RED}Could not determine package manager. Please install jq manually.${NC}"
        exit 1
    fi
fi

echo -e "${YELLOW}Manual Configuration Required:${NC}"
echo ""
echo "1. Enable API in pfSense:"
echo "   - Navigate to: System -> Advanced -> API"
echo "   - Enable API: Yes"
echo "   - Generate API Key"
echo ""
echo "2. Configure API Access:"
echo "   - Allowed IPs: $SECURITY_SERVICE_IP"
echo "   - Save configuration"
echo ""
echo "3. Update Security Service Configuration:"
echo "   - Set PFSENSE_URL=$PFSENSE_URL"
echo "   - Set PFSENSE_API_KEY=<your-api-key>"
echo "   - Update .env file or environment variables"
echo ""
echo "4. Test API Connection:"
echo "   curl -k -H \"X-API-Key: YOUR_API_KEY\" \\"
echo "        $PFSENSE_URL/api/v1/status/system"
echo ""

# Generate API key suggestion
echo -e "${GREEN}API Key Generation:${NC}"
echo "Generate a secure API key:"
echo "  openssl rand -base64 32"
echo ""

# Create example configuration
cat > .env.pfsense.example <<EOF
# pfSense API Configuration
PFSENSE_URL=$PFSENSE_URL
PFSENSE_API_KEY=your-api-key-here
PFSENSE_VERIFY_SSL=false
PFSENSE_TIMEOUT=30

# VLAN Mappings
VLAN_MANAGEMENT=10
VLAN_DMZ=20
VLAN_WEB=30
VLAN_DATABASE=40
VLAN_STORAGE=50
VLAN_IOT=60
VLAN_GUEST=70
EOF

echo -e "${GREEN}Created .env.pfsense.example${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Copy .env.pfsense.example to your .env file"
echo "2. Update PFSENSE_API_KEY with your actual API key"
echo "3. Restart security service"
echo "4. Verify API connectivity in security service logs"
