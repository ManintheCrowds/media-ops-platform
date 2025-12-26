# Ansible Infrastructure Automation

## Overview

This directory contains Ansible playbooks and roles for automating infrastructure provisioning, deployment, and management.

## Structure

```
ansible/
├── playbooks/          # Main playbooks
│   ├── site.yml        # Master playbook
│   ├── server-setup.yml
│   ├── docker-setup.yml
│   ├── platform-deploy.yml
│   ├── monitoring-setup.yml
│   └── pi-provision.yml
├── roles/              # Reusable roles
│   ├── common/
│   ├── docker/
│   ├── platform/
│   ├── monitoring/
│   └── pi-client/
├── inventory/          # Host inventory
│   ├── hosts.yml
│   └── group_vars/
├── vars/               # Variable files
└── ansible.cfg         # Ansible configuration
```

## Prerequisites

- Ansible 2.9+
- Python 3.8+
- SSH access to target servers
- sudo privileges on target servers

## Quick Start

1. **Install Ansible:**
   ```bash
   pip install ansible
   ```

2. **Configure inventory:**
   Edit `inventory/hosts.yml` with your server IPs and credentials.

3. **Test connection:**
   ```bash
   ansible all -m ping
   ```

4. **Run playbook:**
   ```bash
   ansible-playbook playbooks/server-setup.yml
   ```

## Inventory Configuration

### Basic Inventory

Edit `inventory/hosts.yml`:

```yaml
all:
  children:
    servers:
      hosts:
        app-server:
          ansible_host: 192.168.1.10
          ansible_user: ansible
```

### Multi-Service Inventory

Example inventory for deploying multiple services:

```yaml
all:
  children:
    platform-servers:
      hosts:
        platform-01:
          ansible_host: 192.168.1.10
          ansible_user: ansible
          services:
            - platform-api
            - postgres
            - security-service
            - monitoring
    
    application-servers:
      hosts:
        app-01:
          ansible_host: 192.168.1.20
          ansible_user: ansible
          services:
            - education-service
            - job-automation-service
            - home-cyber-risk
    
    pi-devices:
      hosts:
        pi-001:
          ansible_host: 192.168.1.100
          ansible_user: pi
          pi_client_enabled: true
          education_service_url: http://app-01:8003
```

### Service Dependencies

When deploying services, dependencies are automatically handled:

- **Platform API** requires: PostgreSQL
- **Security Service** requires: PostgreSQL, Redis
- **Education Service** requires: PostgreSQL
- **Job Automation Service** requires: PostgreSQL
- **Home Cyber Risk** requires: SQLite or PostgreSQL (optional)
- **Monitoring Stack** requires: No dependencies (standalone)

## Variables

### Global Variables (`inventory/group_vars/all.yml`)

- `timezone` - System timezone
- `firewall_enabled` - Enable firewall
- `backup_enabled` - Enable backups
- `monitoring_enabled` - Enable monitoring

### Server Variables (`inventory/group_vars/servers.yml`)

- `docker_version` - Docker version
- `platform_services` - List of services
- `resource_limits` - Resource constraints

### Pi Device Variables (`inventory/group_vars/pi_devices.yml`)

- `pi_client_version` - Pi client version
- `pi_client_config` - Pi client configuration

## Secrets Management

Use Ansible Vault for sensitive data:

```bash
# Create vault file
ansible-vault create group_vars/all/vault.yml

# Edit vault file
ansible-vault edit group_vars/all/vault.yml

# Use in playbooks
ansible-playbook playbooks/platform-deploy.yml --ask-vault-pass
```

## Available Playbooks

### server-setup.yml

Initial server provisioning:
- System updates
- User creation
- Firewall configuration
- Time synchronization
- Log rotation

```bash
ansible-playbook playbooks/server-setup.yml
```

### docker-setup.yml

Docker installation:
- Docker Engine
- Docker Compose
- User group configuration

```bash
ansible-playbook playbooks/docker-setup.yml
```

### platform-deploy.yml

Platform deployment:
- Environment configuration
- Docker Compose deployment
- Database initialization
- Health verification

```bash
ansible-playbook playbooks/platform-deploy.yml
```

### Service-Specific Deployment

Deploy individual services:

**Security Service:**
```bash
ansible-playbook playbooks/platform-deploy.yml --tags security-service
```

**Education Service:**
```bash
ansible-playbook playbooks/platform-deploy.yml --tags education-service
```

**Job Automation Service:**
```bash
ansible-playbook playbooks/platform-deploy.yml --tags job-automation-service
```

**Home Cyber Risk:**
```bash
ansible-playbook playbooks/platform-deploy.yml --tags home-cyber-risk
```

### monitoring-setup.yml

Monitoring stack:
- Prometheus
- Grafana
- Alertmanager
- Exporters

```bash
ansible-playbook playbooks/monitoring-setup.yml
```

### pi-provision.yml

Raspberry Pi provisioning:
- OS preparation
- Pi client installation
- Certificate generation
- Device registration

```bash
ansible-playbook playbooks/pi-provision.yml -i pi-001,
```

## Roles

### common

Common server setup tasks.

**Tasks:**
- System updates
- User management
- Firewall configuration
- NTP setup
- Log rotation

### docker

Docker installation and configuration.

**Tasks:**
- Docker Engine installation
- Docker Compose installation
- Daemon configuration

### platform

Platform service deployment.

**Tasks:**
- Repository cloning
- Environment file creation
- Docker Compose deployment
- Database initialization

**Role Usage Examples:**

Deploy all platform services:
```bash
ansible-playbook playbooks/platform-deploy.yml
```

Deploy specific service:
```bash
ansible-playbook playbooks/platform-deploy.yml \
  --tags security-service \
  --limit platform-01
```

Deploy with custom variables:
```bash
ansible-playbook playbooks/platform-deploy.yml \
  -e "service_version=latest" \
  -e "database_backup_enabled=true"
```

### monitoring

Monitoring stack setup.

**Tasks:**
- Prometheus configuration
- Grafana setup
- Alertmanager configuration
- Exporter installation

### pi-client

Raspberry Pi client setup.

**Tasks:**
- Prerequisites installation
- Pi client installation
- Certificate generation
- Service configuration
- Device registration

## Best Practices

1. **Use roles** for reusable tasks
2. **Store secrets in vault**
3. **Test playbooks** in staging first
4. **Use tags** for selective execution
5. **Document variables** clearly
6. **Version control** all playbooks

## Troubleshooting

### Connection Issues

```bash
# Test SSH connection
ansible all -m ping

# Check SSH configuration
ansible all -m setup
```

### Permission Issues

```bash
# Use become
ansible-playbook playbook.yml --become

# Specify become user
ansible-playbook playbook.yml --become --become-user root
```

### Debugging

```bash
# Verbose output
ansible-playbook playbook.yml -v

# Very verbose
ansible-playbook playbook.yml -vvv

# Check syntax
ansible-playbook playbook.yml --syntax-check
```

## Service Deployment Examples

### Deploy Security Service

```bash
ansible-playbook playbooks/platform-deploy.yml \
  --tags security-service \
  -e "security_service_version=latest" \
  -e "abuseipdb_api_key=your-key" \
  -e "virustotal_api_key=your-key"
```

### Deploy Education Service with Pi Support

```bash
ansible-playbook playbooks/platform-deploy.yml \
  --tags education-service \
  -e "education_service_version=latest" \
  -e "pi_client_enabled=true"
```

### Deploy Monitoring Stack

```bash
ansible-playbook playbooks/monitoring-setup.yml \
  -e "grafana_admin_password=secure-password" \
  -e "alertmanager_email_enabled=true"
```

### Deploy All Services

```bash
# Deploy infrastructure first
ansible-playbook playbooks/server-setup.yml
ansible-playbook playbooks/docker-setup.yml

# Deploy platform services
ansible-playbook playbooks/platform-deploy.yml

# Deploy monitoring
ansible-playbook playbooks/monitoring-setup.yml

# Provision Pi devices
ansible-playbook playbooks/pi-provision.yml
```

## Related Services

- [Platform API](../README.md) - Main integration layer
- [Security Service](../security-service/README.md) - Security monitoring
- [Education Service](../education-service/README.md) - Educational platform
- [Job Automation Service](../job-automation-service/README.md) - Job search automation
- [Monitoring Stack](../monitoring/README.md) - Prometheus, Grafana

## Additional Resources

- [Ansible Documentation](https://docs.ansible.com/)
- [Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
