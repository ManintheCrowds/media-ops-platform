# Pi-hole DNS Setup Guide

This guide explains how to configure Pi-hole for DNS protection and visibility.

## Overview

Pi-hole blocks ads and malicious domains at the DNS level, providing network-wide protection. When enabled, it acts as your local DNS server.

## Prerequisites

- Pi-hole service enabled in docker-compose.yml
- Access to router or device network settings
- Understanding of DNS configuration

## Step 1: Enable Pi-hole

1. Edit `infra/docker-compose.yml`
2. Uncomment the Pi-hole service section
3. Set `PIHOLE_PASSWORD` in `.env` file
4. Start Pi-hole:
   ```bash
   cd infra
   docker-compose up -d pihole
   ```

## Step 2: Configure Router DNS

### Option A: Router Configuration (Recommended)

Point your router's DNS to Pi-hole:

1. Access router admin interface (usually 192.168.1.1 or 192.168.0.1)
2. Find DNS settings (usually under Network or Internet settings)
3. Set primary DNS to Pi-hole IP: `172.20.0.10` (or check actual IP with `docker inspect pihole`)
4. Set secondary DNS to a public DNS (8.8.8.8 or 1.1.1.1) as backup
5. Save and restart router

All devices on your network will now use Pi-hole for DNS.

### Option B: Device-Level Configuration

Configure individual devices:

**Windows:**
1. Open Network Settings
2. Change adapter options
3. Right-click your network adapter → Properties
4. Internet Protocol Version 4 (TCP/IPv4) → Properties
5. Use the following DNS server addresses: `172.20.0.10`

**Linux:**
Edit `/etc/resolv.conf`:
```
nameserver 172.20.0.10
```

**Mac:**
1. System Preferences → Network
2. Select your connection → Advanced → DNS
3. Add `172.20.0.10`

## Step 3: Verify Configuration

1. Access Pi-hole admin: http://172.20.0.10/admin (or check actual IP)
2. Login with password from `.env`
3. Check Statistics page - should show queries
4. Test blocking: Visit an ad-heavy website
5. Check Query Log in Pi-hole admin

## Step 4: Testing DNS Resolution

Test that DNS is working:

```bash
# Test DNS resolution
nslookup google.com 172.20.0.10

# Test blocked domain (should fail or return 0.0.0.0)
nslookup doubleclick.net 172.20.0.10
```

## Troubleshooting

### Pi-hole not accessible

- Check container is running: `docker-compose ps pihole`
- Verify IP address: `docker inspect pihole | grep IPAddress`
- Check firewall rules
- Ensure port 80 is accessible (if exposed)

### DNS not working

- Verify router DNS settings
- Check device DNS configuration
- Test with: `nslookup google.com`
- Check Pi-hole logs: `docker-compose logs pihole`

### Devices not using Pi-hole

- Verify router DNS is set correctly
- Restart devices after DNS change
- Check device DNS settings manually
- Some devices may cache DNS - flush cache

### Pi-hole blocking too much

- Access Pi-hole admin interface
- Whitelist domains that should not be blocked
- Adjust block lists in Settings → Blocklists
- Review Query Log to see what's being blocked

## Advanced Configuration

### Custom Block Lists

Add custom block lists in Pi-hole admin:
- Settings → Blocklists
- Add URLs of block list sources
- Update gravity (block list database)

### Local DNS Records

Add local DNS records in Pi-hole admin:
- Local DNS Records
- Add custom domain → IP mappings

### Query Logging

Pi-hole logs all DNS queries. Access in admin interface:
- Query Log shows all DNS requests
- Can filter by domain, client, type
- Useful for network visibility

## Security Notes

- Pi-hole admin interface should only be accessible on local network
- Change default password immediately
- Regularly update Pi-hole and block lists
- Monitor query log for suspicious activity
- Consider firewall rules to restrict access

## Integration with Breach Monitor

Currently, Pi-hole operates independently. Future integration could:
- Parse Pi-hole logs for suspicious domains
- Correlate DNS queries with breach data
- Alert on queries to known malicious domains

For now, Pi-hole provides DNS protection and visibility separately from breach monitoring.

## Maintenance

### Update Block Lists

Pi-hole automatically updates block lists, but you can force update:
- Admin interface → Tools → Update Gravity
- Or via command: `docker exec pihole pihole -g`

### Update Pi-hole

```bash
cd infra
docker-compose pull pihole
docker-compose up -d pihole
```

### Backup Configuration

Backup Pi-hole configuration:
```bash
docker exec pihole pihole -a -t
```

This creates a backup file in Pi-hole container.

## Resources

- Pi-hole documentation: https://docs.pi-hole.net/
- Block list sources: https://firebog.net/
- Community support: https://discourse.pi-hole.net/

