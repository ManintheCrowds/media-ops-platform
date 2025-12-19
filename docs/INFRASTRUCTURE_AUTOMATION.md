# Infrastructure Automation and Management Guide

## Overview

This guide covers the complete infrastructure automation and management system for the self-hosted platform, including Ansible playbooks, deployment automation, monitoring, backup systems, and Raspberry Pi fleet management.

## Table of Contents

1. [Ansible Infrastructure](#ansible-infrastructure)
2. [Deployment Automation](#deployment-automation)
3. [Backup and Recovery](#backup-and-recovery)
4. [Monitoring and Alerting](#monitoring-and-alerting)
5. [Raspberry Pi Management](#raspberry-pi-management)
6. [CI/CD Pipelines](#cicd-pipelines)
7. [Version Management](#version-management)

## Ansible Infrastructure

### Directory Structure

```
ansible/
├── playbooks/          # Main playbooks
├── roles/              # Reusable roles
├── inventory/          # Host inventory
├── vars/               # Variable files
└── ansible.cfg         # Ansible configuration
```

### Quick Start

1. **Configure inventory:**
   ```bash
   cd ansible
   cp inventory/hosts.yml.example inventory/hosts.yml
   # Edit hosts.yml with your server IPs
   ```

2. **Run server setup:**
   ```bash
   ansible-playbook playbooks/server-setup.yml
   ```

3. **Deploy platform:**
   ```bash
   ansible-playbook playbooks/platform-deploy.yml
   ```

### Available Playbooks

- `server-setup.yml` - Initial server provisioning
- `docker-setup.yml` - Docker installation
- `platform-deploy.yml` - Platform deployment
- `monitoring-setup.yml` - Monitoring stack setup
- `pi-provision.yml` - Raspberry Pi provisioning

### Roles

- **common** - Common server setup (users, firewall, NTP, log rotation)
- **docker** - Docker and Docker Compose installation
- **platform** - Platform service deployment
- **monitoring** - Prometheus, Grafana, Alertmanager setup
- **pi-client** - Raspberry Pi client installation and configuration

## Deployment Automation

### Deployment Scripts

Located in `scripts/automation/`:

- **deploy.sh** - Main deployment script with validation and rollback
- **deploy-service.sh** - Individual service deployment

### Usage

```bash
# Deploy all services
./scripts/automation/deploy.sh

# Deploy specific service
./scripts/automation/deploy-service.sh platform

# Production deployment
./scripts/automation/deploy.sh --production
```

### Features

- Pre-deployment validation
- Automatic backup before deployment
- Health check verification
- Automatic rollback on failure
- Deployment logging

## Backup and Recovery

### Backup Scripts

- **backup.sh** - Create backups (database, volumes, config)
- **restore.sh** - Restore from backups
- **backup-scheduler.sh** - Automated backup scheduling

### Backup Types

1. **Database Backups** - Daily full backups, hourly incremental
2. **Volume Backups** - Weekly full backups
3. **Configuration Backups** - On every change

### Retention Policy

- Daily backups: 30 days
- Weekly backups: 12 weeks
- Monthly backups: 12 months

### Usage

```bash
# Create backup
./scripts/automation/backup.sh

# Quick backup (database and config only)
./scripts/automation/backup.sh --quick

# Restore database
./scripts/automation/restore.sh --type database --file backups/database/postgres-20240101-120000.sql.gz

# Schedule backups
./scripts/automation/backup-scheduler.sh setup
```

## Monitoring and Alerting

### Prometheus

Configuration: `prometheus/prometheus.yml`

**Exporters:**
- Node Exporter - System metrics
- cAdvisor - Container metrics
- PostgreSQL Exporter - Database metrics

### Grafana

**Dashboards:**
- Platform Overview
- Service-specific dashboards
- Infrastructure dashboards
- Pi device dashboards

**Provisioning:**
- Data sources configured automatically
- Dashboards provisioned from `monitoring/grafana/dashboards/`

### Alertmanager

Configuration: `monitoring/alertmanager/alertmanager.yml`

**Alert Rules:**
- Service availability
- Resource usage (CPU, memory, disk)
- Security events
- Pi device status
- Database performance

**Notification Channels:**
- Email (primary)
- Webhooks
- Escalation policies

## Raspberry Pi Management

### Provisioning

```bash
# Provision new Pi device
./scripts/pi/pi-provision.sh pi-001 "Classroom Display 1"
```

### Updates

```bash
# Update single device
./scripts/pi/pi-update.sh pi-001

# Fleet-wide update (staged)
./scripts/pi/pi-fleet-update.sh --batch-size 2 --staged
```

### Configuration Management

```bash
# Sync configuration
./scripts/pi/pi-config-sync.sh pi-001

# Fleet status
./scripts/pi/pi-fleet-status.sh

# Fleet management
./scripts/pi/pi-fleet-manager.sh status
./scripts/pi/pi-fleet-manager.sh restart
```

## CI/CD Pipelines

### Workflows

- **tests.yml** - Automated testing (lint, unit, integration, E2E)
- **deploy.yml** - General deployment workflow
- **deploy-staging.yml** - Staging environment deployment
- **deploy-production.yml** - Production deployment (with approval)
- **rollback.yml** - Rollback workflow
- **release.yml** - Release creation and tagging

### Deployment Process

1. Code pushed to repository
2. Tests run automatically
3. Staging deployment (on develop branch)
4. Production deployment (manual approval required)
5. Health checks verify deployment
6. Rollback available if issues detected

## Version Management

### Version Manager Script

```bash
# Create version tag
./scripts/automation/version-manager.sh tag 1.2.3 "Release notes"

# Create release
./scripts/automation/version-manager.sh release 1.2.3

# Generate changelog
./scripts/automation/version-manager.sh changelog v1.2.2 v1.2.3
```

### Rollback

```bash
# Rollback to specific version
./scripts/automation/rollback.sh --version v1.2.2

# Rollback to latest backup
./scripts/automation/rollback.sh --latest
```

## Update and Patch Management

### Update Script

```bash
# Update all (system, docker, application)
./scripts/automation/update.sh --type all

# Update only Docker images
./scripts/automation/update.sh --type docker

# Dry run
./scripts/automation/update.sh --type all --dry-run
```

### Patch Management

```bash
# Check for security patches
./scripts/automation/patch-management.sh

# Apply patches
./scripts/automation/patch-management.sh --apply

# Schedule automatic patches
./scripts/automation/patch-management.sh --schedule
```

## Health Monitoring

### Health Check Script

```bash
# Check all services
./scripts/automation/health-check.sh

# Check specific service
./scripts/automation/health-check.sh --service platform

# With alerts
./scripts/automation/health-check.sh --alert
```

### Continuous Monitoring

```bash
# Start continuous monitoring
./scripts/automation/health-monitor.sh
```

## Docker Compose Optimization

### Production Configuration

Use `docker-compose.prod.yml` for production:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Features:**
- Resource limits
- Production-optimized settings
- Security hardening
- Network isolation

## Security Considerations

1. **Ansible Vault** - Store secrets encrypted
   ```bash
   ansible-vault create group_vars/all/vault.yml
   ```

2. **SSH Keys** - Use key-based authentication
3. **Backup Encryption** - Encrypt sensitive backups
4. **Access Control** - Limit Ansible access
5. **Audit Logging** - Log all automation actions

## Troubleshooting

### Common Issues

1. **Ansible connection failures**
   - Check SSH access
   - Verify inventory configuration
   - Test with `ansible all -m ping`

2. **Deployment failures**
   - Check logs: `docker compose logs`
   - Verify health: `./scripts/automation/health-check.sh`
   - Review deployment log: `logs/deploy-*.log`

3. **Backup failures**
   - Check disk space
   - Verify backup directory permissions
   - Check database connectivity

4. **Pi device issues**
   - Check device connectivity: `ping pi-device-ip`
   - Verify SSH access
   - Check service status: `systemctl status pi-client`

## Best Practices

1. **Always backup before deployment**
2. **Test in staging first**
3. **Monitor health after changes**
4. **Keep documentation updated**
5. **Review logs regularly**
6. **Use version control for all configs**
7. **Schedule regular backups**
8. **Keep systems updated**

## Additional Resources

- [Ansible Documentation](ansible/README.md)
- [Script Documentation](scripts/automation/README.md)
- [Monitoring Guide](monitoring/README.md)
- [Pi Management Guide](scripts/pi/README.md)
