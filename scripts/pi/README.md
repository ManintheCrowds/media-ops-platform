# Raspberry Pi Management Scripts

## Overview

Scripts for managing Raspberry Pi devices in the fleet, including provisioning, updates, configuration, and monitoring.

## Purpose and Scope

These scripts support the Pi Client integration with the Education Service:
- **Device Provisioning**: Set up new Pi devices for educational platform
- **Fleet Management**: Manage multiple Pi devices efficiently
- **Configuration Sync**: Keep device configurations in sync
- **Update Management**: Deploy updates safely across fleet

## Integration with Services

- **Education Service**: Pi devices connect to education service API
- **Platform API**: Device registration and authentication
- **Monitoring Stack**: Device health and status monitoring
- **Ansible**: Automated provisioning and configuration

## Scripts

### pi-provision.sh

Provision new Raspberry Pi device.

**Usage:**
```bash
./pi-provision.sh DEVICE_ID DEVICE_NAME [API_URL] [ORG_ID]
```

**Example:**
```bash
./pi-provision.sh pi-001 "Classroom Display 1" http://education.example.com 1
```

**Features:**
- OS preparation
- Pi client installation
- Certificate generation
- Device registration

### pi-update.sh

Update single Pi device.

**Usage:**
```bash
./pi-update.sh DEVICE_ID [--version VERSION] [--rollback]
```

**Example:**
```bash
./pi-update.sh pi-001
./pi-update.sh pi-001 --rollback
```

### pi-fleet-update.sh

Fleet-wide updates with staged rollout.

**Usage:**
```bash
./pi-fleet-update.sh [--batch-size SIZE] [--staged]
```

**Example:**
```bash
# Staged rollout (2 devices at a time)
./pi-fleet-update.sh --batch-size 2 --staged

# Update all at once
./pi-fleet-update.sh --staged false
```

### pi-config-sync.sh

Synchronize configuration for Pi device.

**Usage:**
```bash
./pi-config-sync.sh DEVICE_ID [--force]
```

**Example:**
```bash
./pi-config-sync.sh pi-001
./pi-config-sync.sh pi-001 --force
```

### pi-fleet-manager.sh

Fleet management operations.

**Usage:**
```bash
./pi-fleet-manager.sh [command] [options]
```

**Commands:**
- `status` - Show fleet status
- `restart` - Restart all devices
- `update` - Update all devices
- `config-sync` - Sync config for all devices
- `group` - Group devices

**Example:**
```bash
./pi-fleet-manager.sh status
./pi-fleet-manager.sh restart
```

### pi-fleet-status.sh

Fleet status overview.

**Usage:**
```bash
./pi-fleet-status.sh
```

**Output:**
- Fleet overview (total, online, offline)
- Device health summary
- Sync status
- Alerts

## Ansible Integration

Pi devices can also be managed via Ansible:

```bash
# Provision device
ansible-playbook ansible/playbooks/pi-provision.yml -i pi-001,

# Update configuration
ansible-playbook ansible/roles/pi-client/tasks/config.yml -i pi-001,
```

## Device Configuration

Configuration stored in `/etc/pi-client/config.yaml`:

```yaml
device:
  device_id: "pi-001"
  device_name: "Classroom Display 1"

api:
  base_url: "http://education.example.com"
  timeout: 30

cache:
  directory: /var/lib/pi-client/cache
  max_size_mb: 5000
  ttl_hours: 168

display:
  port: 8080
  rotation: landscape
  fullscreen: true
  mode: kiosk
```

## Certificate Management

Device certificates stored in `/etc/pi-client/certs/`:
- `device.pem` - Device certificate
- `device-key.pem` - Private key
- `ca.pem` - CA certificate

## Best Practices

1. **Use staged rollouts** for fleet updates
2. **Monitor device health** regularly
3. **Backup configurations** before changes
4. **Test updates** on single device first
5. **Document device groups** for easier management

## Troubleshooting

### Device not responding

- Check network connectivity
- Verify SSH access
- Check service status: `systemctl status pi-client`

### Update failures

- Check device logs
- Verify disk space
- Check network connectivity
- Review update logs

### Configuration sync issues

- Verify Ansible access
- Check configuration file syntax
- Review sync logs
