# Platform Role

This role deploys the platform services using Docker Compose.

## Variables

- `platform_deploy_path`: Path to deploy platform (default: /opt/platform)
- `platform_data_path`: Path for platform data (default: /var/lib/platform)
- `platform_repo_url`: Git repository URL for platform code
- `platform_repo_branch`: Git branch to deploy (default: main)
- `platform_init_db`: Initialize database after deployment (default: true)
- `docker_compose_pull`: Pull Docker images before deployment (default: true)
- `platform_services`: List of services to deploy
- `postgres_user`: PostgreSQL username
- `postgres_password`: PostgreSQL password
- `postgres_database`: PostgreSQL database name

## Features

- Clones platform repository
- Creates environment file from template
- Deploys services using Docker Compose
- Initializes database
- Verifies platform health

## Secrets

Sensitive values should be stored in Ansible Vault:
```bash
ansible-vault create group_vars/all/vault.yml
```
