# Architecture Documentation

## Overview

The Self-Hosted Platform Integration is a unified gateway system that integrates multiple self-hosted services through a single FastAPI-based API. It provides unified authentication, service discovery, health monitoring, and a centralized dashboard.

## System Architecture

```mermaid
flowchart TB
    subgraph "Client Layer"
        Browser[Web Browser]
        API_Client[API Client]
    end
    
    subgraph "Platform Layer"
        Nginx[Nginx Reverse Proxy]
        FastAPI[FastAPI Application]
        DB[(PostgreSQL Database)]
    end
    
    subgraph "Service Layer"
        Seafile[Seafile]
        Jellyfin[Jellyfin]
        BookStack[BookStack]
        Gitea[Gitea]
        Prometheus[Prometheus]
        Grafana[Grafana]
        Vaultwarden[Vaultwarden]
    end
    
    Browser --> Nginx
    API_Client --> Nginx
    Nginx --> FastAPI
    FastAPI --> DB
    FastAPI --> Seafile
    FastAPI --> Jellyfin
    FastAPI --> BookStack
    FastAPI --> Gitea
    FastAPI --> Prometheus
    FastAPI --> Grafana
    FastAPI --> Vaultwarden
```

## Component Architecture

### 1. FastAPI Application (`app/`)

The main application layer providing:

- **Authentication Module** (`app/auth/`)
  - JWT token generation and validation
  - OAuth2 password flow
  - User management
  - Password hashing with bcrypt

- **API Routes** (`app/api/`)
  - `/api/auth` - Authentication endpoints
  - `/api/services` - Service registry management
  - `/api/health` - Health monitoring
  - `/api/gateway` - Service proxy endpoints

- **Models** (`app/models/`)
  - User model for authentication
  - Service model for service registry

- **Configuration** (`app/config.py`)
  - Environment-based configuration
  - Service URL configuration
  - Security settings

### 2. Service Clients (`services/`)

Modular service client implementations:

- **File Storage** (`services/file_storage/`)
  - SeafileClient for Seafile integration

- **Media Server** (`services/media_server/`)
  - JellyfinClient for Jellyfin integration

- **Productivity** (`services/productivity/`)
  - WikiClient for BookStack integration

- **Development Tools** (`services/dev_tools/`)
  - GiteaClient for Gitea integration

- **Monitoring** (`services/monitoring/`)
  - PrometheusClient for metrics
  - GrafanaClient for dashboards

- **Security** (`services/security/`)
  - VaultwardenClient for password manager

### 3. Database Schema

**Users Table:**
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email
- `hashed_password` - Bcrypt hashed password
- `is_active` - Account status
- `is_admin` - Admin privileges
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

**Services Table:**
- `id` - Primary key
- `name` - Unique service name
- `service_type` - Service category
- `base_url` - Service base URL
- `api_url` - Service API URL
- `health_check_url` - Health check endpoint
- `is_active` - Service status
- `requires_auth` - Authentication requirement
- `auth_token` - Service authentication token
- `health_status` - Current health status
- `last_health_check` - Last check timestamp
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

## Data Flow

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant DB
    participant JWT
    
    Client->>FastAPI: POST /api/auth/register
    FastAPI->>DB: Create user
    DB-->>FastAPI: User created
    FastAPI-->>Client: User response
    
    Client->>FastAPI: POST /api/auth/token
    FastAPI->>DB: Verify credentials
    DB-->>FastAPI: User data
    FastAPI->>JWT: Generate token
    JWT-->>FastAPI: Access token
    FastAPI-->>Client: Token response
    
    Client->>FastAPI: GET /api/* (with token)
    FastAPI->>JWT: Verify token
    JWT-->>FastAPI: Token payload
    FastAPI->>DB: Get user
    DB-->>FastAPI: User data
    FastAPI-->>Client: Protected resource
```

### Service Gateway Flow

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant ServiceRegistry
    participant ServiceClient
    participant ExternalService
    
    Client->>Gateway: GET /api/gateway/file-storage/libraries
    Gateway->>ServiceRegistry: Query service by type
    ServiceRegistry-->>Gateway: Service configuration
    Gateway->>ServiceClient: Initialize client
    ServiceClient->>ExternalService: HTTP request
    ExternalService-->>ServiceClient: Response
    ServiceClient-->>Gateway: Formatted data
    Gateway-->>Client: JSON response
```

### Health Check Flow

```mermaid
sequenceDiagram
    participant Scheduler
    participant HealthAPI
    participant ServiceRegistry
    participant ExternalService
    participant DB
    
    Scheduler->>HealthAPI: Trigger health check
    HealthAPI->>ServiceRegistry: Get all services
    ServiceRegistry-->>HealthAPI: Service list
    HealthAPI->>ExternalService: HTTP GET /health
    ExternalService-->>HealthAPI: Health status
    HealthAPI->>DB: Update service status
    DB-->>HealthAPI: Updated
    HealthAPI-->>Scheduler: Health report
```

## Service Integration Pattern

All service clients follow a consistent pattern:

1. **Configuration** - Load from environment or config file
2. **Context Manager** - Async context manager for HTTP session
3. **Ping Method** - Health check capability
4. **API Methods** - Service-specific operations
5. **Error Handling** - Graceful failure handling

## Security Architecture

### Authentication
- JWT tokens with configurable expiration
- Bcrypt password hashing with salt
- OAuth2 password flow
- Token-based API authentication

### Authorization
- Role-based access control (admin/user)
- Protected endpoints require authentication
- Admin-only operations enforced

### Data Protection
- Service auth tokens stored in database
- HTTPS recommended for production
- CORS configuration for API access

## Deployment Architecture

```mermaid
flowchart TB
    subgraph "Docker Network"
        subgraph "Platform Services"
            Platform[Platform API Container]
            Postgres[(PostgreSQL Container)]
        end
        
        subgraph "Integrated Services"
            Seafile[Seafile Container]
            Jellyfin[Jellyfin Container]
            BookStack[BookStack Container]
            Gitea[Gitea Container]
            Prometheus[Prometheus Container]
            Grafana[Grafana Container]
            Vaultwarden[Vaultwarden Container]
        end
        
        Nginx[Nginx Reverse Proxy]
    end
    
    Internet --> Nginx
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
```

## Scalability Considerations

- **Horizontal Scaling**: Stateless API allows multiple instances
- **Database**: PostgreSQL supports connection pooling
- **Service Clients**: Async HTTP clients for concurrent requests
- **Caching**: Can be added for frequently accessed data
- **Load Balancing**: Nginx can distribute load across API instances

## Monitoring and Observability

- **Health Checks**: Built-in health monitoring for all services
- **Prometheus Integration**: Metrics collection capability
- **Grafana Integration**: Dashboard visualization
- **Logging**: Application logs for debugging
- **Error Tracking**: HTTP error responses with details

## Detailed Component Architecture

### FastAPI Application Structure

```mermaid
flowchart TB
    subgraph "FastAPI Application"
        subgraph "Middleware Layer"
            CORS[CORS Middleware]
            Auth[Authentication Middleware]
        end
        
        subgraph "Route Handlers"
            AuthRouter["/api/auth<br/>- /token<br/>- /register<br/>- /me<br/>- /init-db"]
            ServicesRouter["/api/services<br/>- GET /<br/>- GET /{id}<br/>- POST /<br/>- PUT /{id}<br/>- DELETE /{id}"]
            HealthRouter["/api/health<br/>- GET /<br/>- GET /services<br/>- GET /services/{id}"]
            GatewayRouter["/api/gateway<br/>- /file-storage/*<br/>- /media-server/*<br/>- /productivity/*<br/>- /dev-tools/*<br/>- /monitoring/*<br/>- /security/*<br/>- /proxy/{service}/{path}"]
        end
        
        subgraph "Business Logic"
            AuthLogic[Authentication Logic<br/>- Password hashing<br/>- JWT generation<br/>- Token validation]
            ServiceLogic[Service Management<br/>- Service registry<br/>- Health checks<br/>- Service discovery]
            GatewayLogic[Gateway Logic<br/>- Request proxying<br/>- Service routing<br/>- Response transformation]
        end
        
        subgraph "Data Access"
            ORM[SQLAlchemy ORM]
            Models[Data Models<br/>- User<br/>- Service]
        end
    end
    
    CORS --> Auth
    Auth --> AuthRouter
    Auth --> ServicesRouter
    Auth --> HealthRouter
    Auth --> GatewayRouter
    
    AuthRouter --> AuthLogic
    ServicesRouter --> ServiceLogic
    HealthRouter --> ServiceLogic
    GatewayRouter --> GatewayLogic
    
    AuthLogic --> ORM
    ServiceLogic --> ORM
    GatewayLogic --> ServiceLogic
    
    ORM --> Models
    Models --> DB[(PostgreSQL)]
```

### Service Client Pattern

```mermaid
flowchart LR
    subgraph "Service Client Pattern"
        Config[Configuration<br/>- Base URL<br/>- API Token<br/>- Timeout]
        Client[Service Client<br/>- Async Context Manager<br/>- HTTP Client]
        Methods[API Methods<br/>- Service-specific operations<br/>- Error handling]
        Health[Health Check<br/>- Ping method<br/>- Status validation]
    end
    
    Gateway[Gateway Endpoint] --> Config
    Config --> Client
    Client --> Methods
    Client --> Health
    Methods --> ExternalService[External Service API]
    Health --> ExternalService
```

### Database Schema (ERD)

```mermaid
erDiagram
    USERS {
        int id PK
        string username UK
        string email UK
        string hashed_password
        boolean is_active
        boolean is_admin
        datetime created_at
        datetime updated_at
    }
    
    SERVICES {
        int id PK
        string name UK
        string service_type
        string base_url
        string api_url
        string health_check_url
        boolean is_active
        boolean requires_auth
        text auth_token
        text service_metadata
        string health_status
        datetime last_health_check
        datetime created_at
        datetime updated_at
    }
    
    USERS ||--o{ SERVICES : "manages (admin)"
```

### Security Architecture Layers

```mermaid
flowchart TB
    subgraph "Security Layers"
        subgraph "Network Security"
            Firewall[Firewall Rules]
            HTTPS[HTTPS/TLS]
            CORS_Config[CORS Configuration]
        end
        
        subgraph "Application Security"
            AuthLayer[Authentication Layer<br/>- JWT Tokens<br/>- OAuth2 Flow]
            AuthzLayer[Authorization Layer<br/>- Role-Based Access<br/>- Admin Checks]
            InputValidation[Input Validation<br/>- Pydantic Models<br/>- SQL Injection Prevention]
        end
        
        subgraph "Data Security"
            PasswordHash[Bcrypt Hashing]
            TokenStorage[Secure Token Storage]
            DBEncryption[Database Security]
        end
    end
    
    Firewall --> HTTPS
    HTTPS --> CORS_Config
    CORS_Config --> AuthLayer
    AuthLayer --> AuthzLayer
    AuthzLayer --> InputValidation
    InputValidation --> PasswordHash
    InputValidation --> TokenStorage
    TokenStorage --> DBEncryption
```

## Service Layer Architecture

### Service Integration Architecture

```mermaid
flowchart TB
    subgraph "Platform API"
        Gateway[API Gateway]
        ServiceRegistry[Service Registry<br/>Database]
    end
    
    subgraph "Service Clients"
        FileStorage[File Storage Client<br/>SeafileClient]
        MediaServer[Media Server Client<br/>JellyfinClient]
        Productivity[Productivity Client<br/>WikiClient]
        DevTools[Dev Tools Client<br/>GiteaClient]
        Monitoring[Monitoring Clients<br/>PrometheusClient<br/>GrafanaClient]
        Security[Security Client<br/>VaultwardenClient]
    end
    
    subgraph "External Services"
        Seafile[Seafile Service]
        Jellyfin[Jellyfin Service]
        BookStack[BookStack Service]
        Gitea[Gitea Service]
        Prometheus[Prometheus Service]
        Grafana[Grafana Service]
        Vaultwarden[Vaultwarden Service]
    end
    
    Gateway --> ServiceRegistry
    Gateway --> FileStorage
    Gateway --> MediaServer
    Gateway --> Productivity
    Gateway --> DevTools
    Gateway --> Monitoring
    Gateway --> Security
    
    FileStorage --> Seafile
    MediaServer --> Jellyfin
    Productivity --> BookStack
    DevTools --> Gitea
    Monitoring --> Prometheus
    Monitoring --> Grafana
    Security --> Vaultwarden
```

## Monitoring Architecture

### Observability Stack

```mermaid
flowchart TB
    subgraph "Application Layer"
        FastAPI[FastAPI Application]
        Logs[Application Logs]
    end
    
    subgraph "Monitoring Services"
        Prometheus[Prometheus<br/>Metrics Collection]
        Grafana[Grafana<br/>Visualization]
    end
    
    subgraph "Health Monitoring"
        HealthAPI[Health Check API]
        ServiceHealth[Service Health Checks]
        DBHealth[Database Health]
    end
    
    FastAPI --> Logs
    FastAPI --> HealthAPI
    HealthAPI --> ServiceHealth
    HealthAPI --> DBHealth
    ServiceHealth --> Prometheus
    DBHealth --> Prometheus
    Prometheus --> Grafana
```

## Scalability Architecture

### Horizontal Scaling Design

```mermaid
flowchart TB
    subgraph "Load Balancer"
        LB[Nginx/Traefik<br/>Load Balancer]
    end
    
    subgraph "API Instances"
        API1[Platform API<br/>Instance 1]
        API2[Platform API<br/>Instance 2]
        API3[Platform API<br/>Instance 3]
    end
    
    subgraph "Database"
        Postgres[(PostgreSQL<br/>with Connection Pooling)]
    end
    
    subgraph "Shared Resources"
        Services[External Services]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> Postgres
    API2 --> Postgres
    API3 --> Postgres
    
    API1 --> Services
    API2 --> Services
    API3 --> Services
```

### Caching Strategy (Future)

```mermaid
flowchart LR
    Client[Client Request] --> LB[Load Balancer]
    LB --> API[API Instance]
    API --> Cache{Cache Check}
    Cache -->|Hit| Response[Return Cached]
    Cache -->|Miss| DB[(Database)]
    DB --> Cache
    Cache --> Response
```

## Component Interaction Details

### Request Processing Flow

1. **Request Reception**: Nginx receives HTTP request
2. **Routing**: Nginx routes to appropriate upstream (Platform API or service)
3. **Authentication**: FastAPI middleware validates JWT token
4. **Authorization**: Check user permissions and roles
5. **Business Logic**: Execute route handler logic
6. **Data Access**: Query database via SQLAlchemy ORM
7. **Service Integration**: If gateway route, call service client
8. **Response**: Return JSON response to client

### Error Handling Architecture

```mermaid
flowchart TB
    Request[API Request] --> Validation{Input Validation}
    Validation -->|Invalid| Error400[400 Bad Request]
    Validation -->|Valid| Auth{Authentication}
    Auth -->|Invalid| Error401[401 Unauthorized]
    Auth -->|Valid| Authz{Authorization}
    Authz -->|Forbidden| Error403[403 Forbidden]
    Authz -->|Allowed| Process[Process Request]
    Process -->|Service Error| Error502[502 Bad Gateway]
    Process -->|Not Found| Error404[404 Not Found]
    Process -->|Success| Success[200 OK]
```

## Technology Stack

### Core Technologies

- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens), OAuth2
- **Password Hashing**: bcrypt
- **HTTP Client**: httpx (async)
- **Reverse Proxy**: Nginx
- **Containerization**: Docker, Docker Compose

### Service Technologies

- **File Storage**: Seafile
- **Media Server**: Jellyfin
- **Wiki**: BookStack
- **Git Service**: Gitea
- **Monitoring**: Prometheus, Grafana
- **Password Manager**: Vaultwarden

## Future Enhancements

- Service discovery automation
- Rate limiting implementation
- Caching layer (Redis)
- WebSocket support for real-time updates
- Service mesh integration
- Multi-tenant support
- Advanced analytics and reporting
- Token refresh mechanism
- Audit logging system
- Automated backup system
