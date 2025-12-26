# Automation Scripts

This directory contains automation scripts for deployment, backup, updates, and health monitoring.

## Purpose and Scope

These scripts automate common platform operations:
- **Deployment**: Automated service deployment with validation
- **Backup Management**: Database and volume backups
- **Update Management**: System and application updates
- **Health Monitoring**: Service health checks and alerts

## Integration with Services

- **Platform Services**: Deploy and manage all platform services
- **Monitoring Stack**: Health checks integrate with Prometheus/Grafana
- **Database Services**: Backup and restore PostgreSQL databases
- **Docker**: Manage Docker containers and volumes

## Scripts Overview

### Deployment

- **deploy.sh** - Main deployment script with validation and rollback
- **deploy-service.sh** - Individual service deployment

### Backup

- **backup.sh** - Create backups (database, volumes, config)
- **restore.sh** - Restore from backups
- **backup-scheduler.sh** - Automated backup scheduling

### Updates

- **update.sh** - System and application updates
- **patch-management.sh** - Security patch management

### Health Monitoring

- **health-check.sh** - Service health checks
- **health-monitor.sh** - Continuous health monitoring

### Version Management

- **rollback.sh** - Rollback to previous version
- **version-manager.sh** - Version tagging and release management

## Usage Examples

### Deployment

```bash
# Deploy all services
./deploy.sh

# Deploy specific service
./deploy-service.sh platform

# Production deployment
./deploy.sh --production
```

### Backup

```bash
# Full backup
./backup.sh

# Quick backup
./backup.sh --quick

# Restore database
./restore.sh --type database --file backups/database/postgres-*.sql.gz
```

### Updates

```bash
# Update all
./update.sh --type all

# Update Docker only
./update.sh --type docker

# Dry run
./update.sh --type all --dry-run
```

### Health Checks

```bash
# Check all services
./health-check.sh

# Check specific service
./health-check.sh --service platform

# With alerts
./health-check.sh --alert
```

## Configuration

Scripts use environment variables and configuration files:

- `.env` - Environment configuration
- `docker-compose.yml` - Service configuration
- `backups/` - Backup storage directory
- `logs/` - Log files directory

## Logging

All scripts log to:
- Console output
- Log files in `logs/` directory
- Timestamped log files for each operation

## Error Handling

Scripts include:
- Pre-deployment validation
- Automatic rollback on failure
- Health check verification
- Error logging and reporting

## Best Practices

1. Always backup before deployment
2. Test in staging first
3. Monitor health after changes
4. Review logs regularly
5. Use version control
