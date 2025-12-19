#!/bin/bash
# Health check automation script
# Usage: ./health-check.sh [--service SERVICE] [--alert]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SERVICE_NAME=""
SEND_ALERT=false
HEALTH_STATUS=0

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[ERROR] $1" >&2
    HEALTH_STATUS=1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --alert)
            SEND_ALERT=true
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Check service health
check_service() {
    local service=$1
    local status=0
    
    case $service in
        platform)
            if curl -f -s http://localhost:8000/api/health > /dev/null 2>&1; then
                log "✓ Platform API is healthy"
            else
                error "✗ Platform API is unhealthy"
                status=1
            fi
            ;;
        postgres)
            if docker exec platform-postgres pg_isready -U platform > /dev/null 2>&1; then
                log "✓ PostgreSQL is healthy"
            else
                error "✗ PostgreSQL is unhealthy"
                status=1
            fi
            ;;
        prometheus)
            if curl -f -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
                log "✓ Prometheus is healthy"
            else
                error "✗ Prometheus is unhealthy"
                status=1
            fi
            ;;
        grafana)
            if curl -f -s http://localhost:3001/api/health > /dev/null 2>&1; then
                log "✓ Grafana is healthy"
            else
                error "✗ Grafana is unhealthy"
                status=1
            fi
            ;;
        redis)
            if docker exec platform-redis redis-cli ping > /dev/null 2>&1; then
                log "✓ Redis is healthy"
            else
                error "✗ Redis is unhealthy"
                status=1
            fi
            ;;
        *)
            # Generic check - container running
            if docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
                log "✓ $service container is running"
            else
                error "✗ $service container is not running"
                status=1
            fi
            ;;
    esac
    
    return $status
}

# Check database connectivity
check_database() {
    log "Checking database connectivity..."
    
    if docker exec platform-postgres psql -U platform -d platform -c "SELECT 1;" > /dev/null 2>&1; then
        log "✓ Database connectivity OK"
    else
        error "✗ Database connectivity failed"
        return 1
    fi
}

# Check API endpoints
check_api_endpoints() {
    log "Checking API endpoints..."
    
    local endpoints=(
        "http://localhost:8000/api/health"
        "http://localhost:8000/api/services"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "$endpoint" > /dev/null 2>&1; then
            log "✓ $endpoint is accessible"
        else
            error "✗ $endpoint is not accessible"
            return 1
        fi
    done
}

# Check resource usage
check_resources() {
    log "Checking resource usage..."
    
    # CPU usage
    local cpu_usage=$(docker stats --no-stream --format "{{.CPUPerc}}" platform-api | sed 's/%//')
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        warning "High CPU usage: ${cpu_usage}%"
    else
        log "✓ CPU usage: ${cpu_usage}%"
    fi
    
    # Memory usage
    local mem_usage=$(docker stats --no-stream --format "{{.MemPerc}}" platform-api | sed 's/%//')
    if (( $(echo "$mem_usage > 80" | bc -l) )); then
        warning "High memory usage: ${mem_usage}%"
    else
        log "✓ Memory usage: ${mem_usage}%"
    fi
}

# Send alert
send_alert() {
    local message=$1
    log "Sending alert: $message"
    # Implement alert sending (email, webhook, etc.)
}

# Main health check process
main() {
    log "Starting health check..."
    
    cd "$PROJECT_ROOT"
    
    if [ -n "$SERVICE_NAME" ]; then
        check_service "$SERVICE_NAME" || {
            if [ "$SEND_ALERT" = true ]; then
                send_alert "Service $SERVICE_NAME is unhealthy"
            fi
            exit 1
        }
    else
        # Check all services
        local services=(
            "platform"
            "postgres"
            "prometheus"
            "grafana"
            "redis"
        )
        
        for service in "${services[@]}"; do
            check_service "$service" || HEALTH_STATUS=1
        done
        
        check_database || HEALTH_STATUS=1
        check_api_endpoints || HEALTH_STATUS=1
        check_resources
    fi
    
    if [ $HEALTH_STATUS -eq 0 ]; then
        log "All health checks passed"
    else
        log "Some health checks failed"
        if [ "$SEND_ALERT" = true ]; then
            send_alert "Health check failed"
        fi
        exit 1
    fi
}

main "$@"
