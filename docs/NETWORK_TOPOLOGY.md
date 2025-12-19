# Network Topology Documentation

## Overview

This document describes the network architecture, port mappings, and service communication patterns for the self-hosted platform integration system.

## Docker Network Architecture

The platform uses a single Docker bridge network (`platform-network`) that connects all services, enabling secure internal communication while maintaining isolation from external networks.

```mermaid
graph TB
    subgraph "Docker Network: platform-network"
        subgraph "Platform Services"
            Platform[Platform API<br/>platform-api<br/>8000]
            Postgres[(PostgreSQL<br/>platform-postgres<br/>5432)]
        end
        
        subgraph "File Storage"
            Seafile[Seafile<br/>platform-seafile<br/>80, 8082]
            SeafileDB[(Seafile DB<br/>platform-seafile-db<br/>3306)]
        end
        
        subgraph "Media Server"
            Jellyfin[Jellyfin<br/>platform-jellyfin<br/>8096, 8920]
        end
        
        subgraph "Productivity"
            BookStack[BookStack<br/>platform-bookstack<br/>80]
            BookStackDB[(BookStack DB<br/>platform-bookstack-db<br/>3306)]
        end
        
        subgraph "Development Tools"
            Gitea[Gitea<br/>platform-gitea<br/>3000, 22]
            GiteaDB[(Gitea DB<br/>platform-gitea-db<br/>5432)]
        end
        
        subgraph "Monitoring"
            Prometheus[Prometheus<br/>platform-prometheus<br/>9090]
            Grafana[Grafana<br/>platform-grafana<br/>3000]
        end
        
        subgraph "Security"
            Vaultwarden[Vaultwarden<br/>platform-vaultwarden<br/>80, 3012]
        end
        
        subgraph "Reverse Proxy"
            Nginx[Nginx<br/>platform-nginx<br/>80, 443]
        end
    end
    
    Internet[Internet] --> Nginx
    Nginx --> Platform
    Nginx --> Seafile
    Nginx --> Jellyfin
    Nginx --> BookStack
    Nginx --> Gitea
    Nginx --> Grafana
    Nginx --> Vaultwarden
    
    Platform --> Postgres
    Platform --> Seafile
    Platform --> Jellyfin
    Platform --> BookStack
    Platform --> Gitea
    Platform --> Prometheus
    Platform --> Grafana
    Platform --> Vaultwarden
    
    Seafile --> SeafileDB
    BookStack --> BookStackDB
    Gitea --> GiteaDB
    Grafana --> Prometheus
```

## Port Mapping Reference

### External Ports (Exposed to Host)

| Service | Container Port | Host Port | Protocol | Purpose |
|---------|---------------|-----------|----------|---------|
| Nginx | 80 | 80 | HTTP | Web access |
| Nginx | 443 | 443 | HTTPS | Secure web access |
| Platform API | 8000 | 8000 | HTTP | Direct API access (optional) |
| Seafile | 80 | 8001 | HTTP | Direct Seafile access (optional) |
| Seafile | 8082 | 8082 | HTTP | Seafile file server (optional) |
| Jellyfin | 8096 | 8096 | HTTP | Direct Jellyfin access (optional) |
| Jellyfin | 8920 | 8920 | HTTPS | Jellyfin secure access (optional) |
| Gitea | 3000 | 3000 | HTTP | Direct Gitea access (optional) |
| Gitea | 22 | 2222 | SSH | Git SSH access (optional) |
| Grafana | 3000 | 3001 | HTTP | Direct Grafana access (optional) |
| Prometheus | 9090 | 9090 | HTTP | Direct Prometheus access (optional) |
| Vaultwarden | 80 | 8080 | HTTP | Direct Vaultwarden access (optional) |
| Vaultwarden | 3012 | 3012 | WebSocket | Vaultwarden WebSocket (optional) |
| BookStack | 80 | 8002 | HTTP | Direct BookStack access (optional) |
| PostgreSQL | 5432 | 5432 | TCP | Direct DB access (optional, not recommended) |

**Note**: Direct service access ports are optional and can be removed for security. All services should be accessed through Nginx reverse proxy in production.

### Internal Ports (Docker Network Only)

| Service | Internal Port | Protocol | Purpose |
|---------|--------------|----------|---------|
| PostgreSQL | 5432 | TCP | Database connections |
| Seafile DB (MariaDB) | 3306 | TCP | Seafile database |
| BookStack DB (MariaDB) | 3306 | TCP | BookStack database |
| Gitea DB (PostgreSQL) | 5432 | TCP | Gitea database |

## Service Communication Matrix

### Internal Service Communication

```mermaid
graph LR
    subgraph "Platform API Communication"
        Platform[Platform API] -->|HTTP| Seafile[Seafile]
        Platform -->|HTTP| Jellyfin[Jellyfin]
        Platform -->|HTTP| BookStack[BookStack]
        Platform -->|HTTP| Gitea[Gitea]
        Platform -->|HTTP| Prometheus[Prometheus]
        Platform -->|HTTP| Grafana[Grafana]
        Platform -->|HTTP| Vaultwarden[Vaultwarden]
        Platform -->|SQL| Postgres[(PostgreSQL)]
    end
    
    subgraph "Service Dependencies"
        Seafile -->|SQL| SeafileDB[(Seafile DB)]
        BookStack -->|SQL| BookStackDB[(BookStack DB)]
        Gitea -->|SQL| GiteaDB[(Gitea DB)]
        Grafana -->|HTTP| Prometheus
    end
```

### Communication Patterns

1. **Platform API to Services**: HTTP requests using service container names as hostnames
   - Example: `http://seafile:80/api2/ping/`
   - Example: `http://jellyfin:8096/System/Info`

2. **Platform API to Database**: PostgreSQL connection using SQLAlchemy
   - Connection string: `postgresql://platform:platform@postgres:5432/platform`

3. **Service to Service**: Direct HTTP communication within Docker network
   - Grafana queries Prometheus: `http://prometheus:9090/api/v1/query`

4. **Client to Platform**: All external traffic goes through Nginx
   - External: `http://yourdomain.com/api/...`
   - Internal routing: Nginx proxies to `http://platform:8000/api/...`

## Network Security Zones

### Security Boundaries

```mermaid
graph TB
    subgraph "External Zone"
        Internet[Internet]
    end
    
    subgraph "DMZ Zone"
        Nginx[Nginx Reverse Proxy]
    end
    
    subgraph "Application Zone"
        Platform[Platform API]
        Services[External Services]
    end
    
    subgraph "Data Zone"
        Databases[(Databases)]
    end
    
    Internet -->|HTTPS/HTTP| Nginx
    Nginx -->|HTTP| Platform
    Nginx -->|HTTP| Services
    Platform -->|SQL| Databases
    Services -->|SQL| Databases
```

### Security Rules

1. **External Access**
   - Only ports 80 (HTTP) and 443 (HTTPS) exposed to internet
   - All traffic must go through Nginx reverse proxy
   - Firewall should block direct access to service ports

2. **Internal Communication**
   - Services communicate using Docker network hostnames
   - No external network access required for service-to-service communication
   - Database ports not exposed externally (or restricted)

3. **Service Isolation**
   - Each service runs in isolated container
   - Shared Docker network for communication
   - No direct file system access between services

## Service Discovery

### Internal Service Discovery

Services are discovered using Docker DNS within the `platform-network`:

- **Container Name Resolution**: Each container can resolve other containers by name
  - `platform-api` resolves to Platform API container
  - `seafile` resolves to Seafile container
  - `postgres` resolves to PostgreSQL container

- **Service Registration**: Services are registered in PostgreSQL database
  - Service registry stores service metadata
  - Health checks use registered service URLs
  - Gateway routes use service registry for routing

### Service URLs

All internal service URLs use container names:

```yaml
Service URLs (Internal):
  - Seafile: http://seafile:80
  - Jellyfin: http://jellyfin:8096
  - BookStack: http://bookstack:80
  - Gitea: http://gitea:3000
  - Prometheus: http://prometheus:9090
  - Grafana: http://grafana:3000
  - Vaultwarden: http://vaultwarden:80
  - PostgreSQL: postgres:5432
```

## Nginx Routing Configuration

### Request Routing Flow

```mermaid
sequenceDiagram
    participant Client
    participant Nginx
    participant Platform
    participant Service
    
    Client->>Nginx: HTTP Request
    Nginx->>Nginx: Route Decision
    
    alt API Request
        Nginx->>Platform: Proxy to platform:8000
        Platform->>Platform: Process Request
        Platform-->>Nginx: Response
    else Service Request
        Nginx->>Service: Proxy to service
        Service-->>Nginx: Response
    end
    
    Nginx-->>Client: HTTP Response
```

### Routing Rules

| Path Pattern | Upstream | Purpose |
|-------------|----------|---------|
| `/` | `platform:8000` | Dashboard |
| `/api/*` | `platform:8000` | Platform API |
| `/dashboard` | `platform:8000` | Dashboard UI |
| `/seafile/*` | `seafile:80` | Seafile service |
| `/jellyfin/*` | `jellyfin:8096` | Jellyfin service |
| `/gitea/*` | `gitea:3000` | Gitea service |
| `/grafana/*` | `grafana:3000` | Grafana service |
| `/vaultwarden/*` | `vaultwarden:80` | Vaultwarden service |
| `/bookstack/*` | `bookstack:80` | BookStack service |
| `/health` | Nginx | Health check (bypass) |

## Network Performance Considerations

### Connection Pooling

- **Database Connections**: SQLAlchemy connection pooling
  - Default pool size: 5 connections
  - Max overflow: 10 connections
  - Connection timeout: 30 seconds

- **HTTP Connections**: httpx async client
  - Connection reuse for service clients
  - Timeout: 30 seconds per request
  - Connection limits per service

### Network Optimization

1. **Keep-Alive Connections**: Enabled for HTTP connections
2. **Compression**: Gzip compression enabled in Nginx
3. **Caching**: Static assets cached by Nginx
4. **Load Balancing**: Nginx can distribute load (future: multiple API instances)

## Troubleshooting Network Issues

### Common Issues

1. **Service Not Reachable**
   - Check if service is on same Docker network: `docker network inspect platform-network`
   - Verify container name resolution: `docker exec platform-api ping seafile`
   - Check service logs: `docker logs platform-seafile`

2. **Port Conflicts**
   - Check if port is in use: `netstat -tulpn | grep :8000`
   - Modify port mapping in `docker-compose.yml`
   - Restart services: `docker-compose restart`

3. **Database Connection Issues**
   - Verify database is running: `docker ps | grep postgres`
   - Check connection string in `.env`
   - Test connection: `docker exec platform-api python -c "from app.config import settings; print(settings.database_url)"`

4. **Nginx Routing Problems**
   - Check Nginx config: `docker exec platform-nginx nginx -t`
   - View Nginx logs: `docker logs platform-nginx`
   - Reload Nginx: `docker exec platform-nginx nginx -s reload`

### Network Diagnostics Commands

```bash
# List all containers on network
docker network inspect platform-network

# Test DNS resolution
docker exec platform-api nslookup seafile

# Test HTTP connectivity
docker exec platform-api curl http://seafile:80/api2/ping/

# Check port mappings
docker port platform-api

# View network traffic (requires tcpdump)
docker exec platform-api tcpdump -i eth0
```

## Network Security Best Practices

1. **Firewall Configuration**
   - Only expose ports 80 and 443 to internet
   - Block all other ports at firewall level
   - Use fail2ban for brute force protection

2. **Internal Network Security**
   - Use Docker network isolation
   - Don't expose database ports externally
   - Use strong passwords for all services

3. **TLS/SSL Configuration**
   - Use HTTPS in production
   - Configure SSL certificates in Nginx
   - Enable HSTS headers
   - Use Let's Encrypt for certificates

4. **Network Monitoring**
   - Monitor network traffic
   - Log all connections
   - Set up alerts for unusual activity
   - Regular security audits

## VLAN Architecture (Advanced Configuration)

For enhanced security and network segmentation, the platform supports VLAN-based network architecture using pfSense firewall/router. This provides:

- **Network Segmentation**: Services isolated into security zones
- **Traffic Control**: Granular firewall rules per VLAN
- **Security Isolation**: Database and storage networks completely isolated
- **Scalability**: Easy to add new services to appropriate VLANs

### VLAN Network Topology

```mermaid
graph TB
    subgraph "Internet"
        WAN[WAN Connection]
    end
    
    subgraph "pfSense Firewall"
        PFSense[pfSense Router/Firewall]
    end
    
    subgraph "VLAN 20 - DMZ"
        Nginx[Nginx<br/>10.0.20.10]
    end
    
    subgraph "VLAN 30 - Web Services"
        Platform[Platform API<br/>10.0.30.10]
        Education[Education Service<br/>10.0.30.20]
        Security[Security Service<br/>10.0.30.30]
        Jellyfin[Jellyfin<br/>10.0.30.40]
        Gitea[Gitea<br/>10.0.30.50]
        BookStack[BookStack<br/>10.0.30.60]
        Vaultwarden[Vaultwarden<br/>10.0.30.70]
        Redis[Redis<br/>10.0.30.80]
    end
    
    subgraph "VLAN 40 - Database"
        Postgres[(PostgreSQL<br/>10.0.40.10)]
        SeafileDB[(Seafile DB<br/>10.0.40.20)]
        GiteaDB[(Gitea DB<br/>10.0.40.30)]
        BookStackDB[(BookStack DB<br/>10.0.40.40)]
        EducationDB[(Education DB<br/>10.0.40.50)]
    end
    
    subgraph "VLAN 50 - Storage"
        Seafile[Seafile<br/>10.0.50.10]
        Drobo[Drobo NAS<br/>10.0.50.20]
    end
    
    subgraph "VLAN 10 - Management"
        Prometheus[Prometheus<br/>10.0.10.10]
        Grafana[Grafana<br/>10.0.10.20]
    end
    
    WAN --> PFSense
    PFSense --> Nginx
    Nginx --> Platform
    Nginx --> Education
    Nginx --> Jellyfin
    Nginx --> Gitea
    Nginx --> BookStack
    Nginx --> Vaultwarden
    
    Platform --> Postgres
    Platform --> Seafile
    Education --> EducationDB
    Jellyfin --> Postgres
    Gitea --> GiteaDB
    BookStack --> BookStackDB
    Seafile --> SeafileDB
    Seafile --> Drobo
    
    Platform --> Prometheus
    Grafana --> Prometheus
```

### VLAN Configuration

| VLAN | Network | Gateway | Purpose | Services |
|------|---------|---------|---------|----------|
| 10 | 10.0.10.0/24 | 10.0.10.1 | Management | Prometheus, Grafana |
| 20 | 10.0.20.0/24 | 10.0.20.1 | DMZ | Nginx |
| 30 | 10.0.30.0/24 | 10.0.30.1 | Web Services | Platform API, Applications |
| 40 | 10.0.40.0/24 | 10.0.40.1 | Database | All databases |
| 50 | 10.0.50.0/24 | 10.0.50.1 | Storage | Seafile, NAS |
| 60 | 10.0.60.0/24 | 10.0.60.1 | IoT/Cameras | IoT devices |
| 70 | 10.0.70.0/24 | 10.0.70.1 | Guest | Guest network |

### Service Placement by VLAN

**VLAN 20 (DMZ)**:
- Nginx reverse proxy (10.0.20.10)

**VLAN 30 (Web Services)**:
- Platform API (10.0.30.10)
- Education Service (10.0.30.20)
- Security Service (10.0.30.30)
- Jellyfin (10.0.30.40)
- Gitea (10.0.30.50)
- BookStack (10.0.30.60)
- Vaultwarden (10.0.30.70)
- Redis (10.0.30.80)

**VLAN 40 (Database)**:
- PostgreSQL main (10.0.40.10)
- Seafile DB (10.0.40.20)
- Gitea DB (10.0.40.30)
- BookStack DB (10.0.40.40)
- Education DB (10.0.40.50)

**VLAN 50 (Storage)**:
- Seafile (10.0.50.10)
- Drobo NAS (10.0.50.20)

**VLAN 10 (Management)**:
- Prometheus (10.0.10.10)
- Grafana (10.0.10.20)

### Inter-VLAN Communication Rules

- **Internet → DMZ**: HTTP (80), HTTPS (443) only
- **DMZ → Web Services**: Ports 80, 443, 8000
- **Web Services → Database**: Ports 5432, 3306
- **Web Services → Storage**: Ports 80, 8082, NFS, SMB
- **Web Services → Management**: Ports 9090, 3000 (monitoring)
- **Storage → Database**: Ports 5432, 3306 (metadata)
- **Management → All**: Full access (admin/monitoring)
- **All others**: Blocked (security isolation)

### VLAN Deployment

To deploy with VLAN architecture:

1. **Configure pfSense**: See [pfSense Configuration Guide](PFSENSE_CONFIGURATION.md)
2. **Set up VLANs**: Use `scripts/network/vlan-setup.sh`
3. **Use VLAN Compose**: Use `docker-compose.vlans.yml` instead of `docker-compose.yml`
4. **Configure Firewall**: Set up firewall rules in pfSense
5. **Test Connectivity**: Verify inter-VLAN communication

For detailed VLAN design, see [Network VLAN Design](NETWORK_VLAN_DESIGN.md).

## See Also

- [Architecture Documentation](ARCHITECTURE.md) - System architecture overview
- [Deployment Guide](DEPLOYMENT.md) - Deployment and configuration
- [Security Guide](SECURITY.md) - Security best practices
- [Network VLAN Design](NETWORK_VLAN_DESIGN.md) - Detailed VLAN architecture
- [pfSense Configuration Guide](PFSENSE_CONFIGURATION.md) - pfSense setup and configuration