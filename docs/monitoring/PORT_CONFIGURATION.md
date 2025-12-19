# Port Configuration Reference

## Grafana Ports

Grafana uses different ports depending on the access context:

### External Access (From Host Machine)
- **URL**: `http://localhost:3001`
- **Port**: 3001 (host port)
- **Use case**: Accessing Grafana from your Windows machine, browser, or external tools

### Internal Access (Docker Network)
- **URL**: `http://grafana:3000`
- **Port**: 3000 (container port)
- **Use case**: Services within Docker network communicating with Grafana
- **Environment variable**: `GRAFANA_URL=http://grafana:3000`

## Port Mapping

The docker-compose.yml configuration maps:
```
Host Port 3001 → Container Port 3000
```

This means:
- Grafana runs on port **3000** inside its container
- Docker maps this to port **3001** on your host machine
- This avoids conflicts with Gitea (which uses host port 3000)

## Configuration Files

### docker-compose.yml
```yaml
grafana:
  ports:
    - "3001:3000"  # host:container
```

### .env.example
```bash
GRAFANA_URL=http://grafana:3000  # Internal Docker network URL
```

### Documentation References
- Monitoring README: Uses `http://localhost:3001` for external access
- Quick Start Guide: Uses `http://localhost:3001` for browser access
- Internal service configs: Use `http://grafana:3000` for service-to-service

## Summary

| Context | URL | Port | Configuration |
|---------|-----|------|---------------|
| Browser/Host Access | `http://localhost:3001` | 3001 | docker-compose.yml port mapping |
| Docker Service Access | `http://grafana:3000` | 3000 | .env GRAFANA_URL |
| Container Internal | `http://localhost:3000` | 3000 | Grafana default |

Both configurations are correct - they're just for different access contexts!
