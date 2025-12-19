# Docker Role

This role installs and configures Docker and Docker Compose.

## Variables

- `docker_version`: Docker version to install (default: "24.0")
- `docker_compose_version`: Docker Compose version (default: "2.23.0")
- `docker_users`: List of users to add to docker group
- `docker_compose_standalone`: Install standalone docker-compose binary (default: false)

## Features

- Installs Docker Engine and Docker Compose
- Configures Docker daemon with logging and storage options
- Adds users to docker group
- Enables and starts Docker service
