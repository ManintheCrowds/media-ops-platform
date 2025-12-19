# Data Flow Documentation

## Overview

This document describes the detailed data flows and request processing sequences for the self-hosted platform integration system. It covers authentication, service requests, health checks, error handling, and gateway operations.

## Authentication Flow

### User Registration Flow

```mermaid
sequenceDiagram
    participant Client
    participant Nginx
    participant FastAPI
    participant AuthModule
    participant Database
    participant Bcrypt
    
    Client->>Nginx: POST /api/auth/register<br/>{username, email, password}
    Nginx->>FastAPI: Proxy request
    FastAPI->>AuthModule: Register endpoint
    AuthModule->>Database: Check if username exists
    Database-->>AuthModule: User not found
    AuthModule->>Database: Check if email exists
    Database-->>AuthModule: Email not found
    AuthModule->>Bcrypt: Hash password
    Bcrypt-->>AuthModule: Hashed password
    AuthModule->>Database: Create user record
    Database-->>AuthModule: User created (id, username, email)
    AuthModule->>FastAPI: UserResponse
    FastAPI->>Nginx: HTTP 200 + User data
    Nginx-->>Client: User registration successful
```

### User Login and Token Generation Flow

```mermaid
sequenceDiagram
    participant Client
    participant Nginx
    participant FastAPI
    participant AuthModule
    participant Database
    participant Bcrypt
    participant JWT
    
    Client->>Nginx: POST /api/auth/token<br/>(username, password)
    Nginx->>FastAPI: Proxy request
    FastAPI->>AuthModule: Login endpoint
    AuthModule->>Database: Query user by username
    Database-->>AuthModule: User record
    AuthModule->>Bcrypt: Verify password
    Bcrypt-->>AuthModule: Password valid
    AuthModule->>Database: Check is_active
    Database-->>AuthModule: User is active
    AuthModule->>JWT: Create access token<br/>{sub: username, email, is_admin}
    JWT-->>AuthModule: JWT token
    AuthModule->>FastAPI: TokenResponse
    FastAPI->>Nginx: HTTP 200 + {access_token, token_type}
    Nginx-->>Client: Authentication successful
```

### Authenticated Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant Nginx
    participant FastAPI
    participant AuthMiddleware
    participant JWT
    participant Database
    participant RouteHandler
    
    Client->>Nginx: GET /api/services<br/>Authorization: Bearer <token>
    Nginx->>FastAPI: Proxy request with headers
    FastAPI->>AuthMiddleware: Extract token from header
    AuthMiddleware->>JWT: Verify token signature
    JWT-->>AuthMiddleware: Token valid + payload
    AuthMiddleware->>Database: Query user by username
    Database-->>AuthMiddleware: User record
    AuthMiddleware->>RouteHandler: Inject current_user
    RouteHandler->>Database: Query services
    Database-->>RouteHandler: Service list
    RouteHandler->>FastAPI: ServiceResponse[]
    FastAPI->>Nginx: HTTP 200 + JSON
    Nginx-->>Client: Services list
```

## Service Gateway Flow

### Service Request via Gateway

```mermaid
sequenceDiagram
    participant Client
    participant Nginx
    participant FastAPI
    participant GatewayRouter
    participant ServiceRegistry
    participant Database
    participant ServiceClient
    participant ExternalService
    
    Client->>Nginx: GET /api/gateway/file-storage/libraries<br/>Authorization: Bearer <token>
    Nginx->>FastAPI: Proxy request
    FastAPI->>GatewayRouter: Route to gateway handler
    GatewayRouter->>AuthMiddleware: Validate token
    AuthMiddleware-->>GatewayRouter: User authenticated
    GatewayRouter->>ServiceRegistry: Query service by type="file_storage"
    ServiceRegistry->>Database: SELECT * FROM services WHERE service_type='file_storage'
    Database-->>ServiceRegistry: Service record
    ServiceRegistry-->>GatewayRouter: Service configuration
    GatewayRouter->>ServiceClient: Initialize SeafileClient
    ServiceClient->>ExternalService: GET http://seafile:80/api2/repos/
    ExternalService-->>ServiceClient: Libraries JSON
    ServiceClient-->>GatewayRouter: Formatted libraries data
    GatewayRouter->>FastAPI: {libraries: [...]}
    FastAPI->>Nginx: HTTP 200 + JSON
    Nginx-->>Client: Libraries response
```

### Generic Proxy Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant GatewayRouter
    participant ServiceRegistry
    participant Database
    participant ProxyFunction
    participant ExternalService
    
    Client->>FastAPI: GET /api/gateway/proxy/seafile/api2/repos/<br/>Authorization: Bearer <token>
    FastAPI->>GatewayRouter: Route to proxy handler
    GatewayRouter->>AuthMiddleware: Validate token
    AuthMiddleware-->>GatewayRouter: User authenticated
    GatewayRouter->>ServiceRegistry: Query service by name="seafile"
    ServiceRegistry->>Database: SELECT * FROM services WHERE name='seafile'
    Database-->>ServiceRegistry: Service record
    ServiceRegistry-->>GatewayRouter: Service configuration
    GatewayRouter->>ProxyFunction: proxy_request(service, path)
    ProxyFunction->>ExternalService: GET http://seafile:80/api2/repos/<br/>Authorization: Bearer <service_token>
    ExternalService-->>ProxyFunction: Response (status, headers, body)
    ProxyFunction-->>GatewayRouter: Response object
    GatewayRouter->>FastAPI: Response
    FastAPI-->>Client: Proxied response
```

## Health Check Flow

### Service Health Check Flow

```mermaid
sequenceDiagram
    participant Scheduler
    participant HealthAPI
    participant ServiceRegistry
    participant Database
    participant HTTPClient
    participant ExternalService
    participant Database
    
    Scheduler->>HealthAPI: GET /api/health/services<br/>Authorization: Bearer <token>
    HealthAPI->>ServiceRegistry: Get all active services
    ServiceRegistry->>Database: SELECT * FROM services WHERE is_active=true
    Database-->>ServiceRegistry: Service list
    ServiceRegistry-->>HealthAPI: Services array
    
    loop For each service
        HealthAPI->>HTTPClient: GET <health_check_url>
        HTTPClient->>ExternalService: HTTP GET request
        ExternalService-->>HTTPClient: Response (status, time)
        HTTPClient-->>HealthAPI: Health status
        HealthAPI->>Database: UPDATE services SET health_status=?, last_health_check=?
        Database-->>HealthAPI: Updated
    end
    
    HealthAPI->>Scheduler: {timestamp, services: {...}}
```

### Individual Service Health Check

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant HealthAPI
    participant ServiceRegistry
    participant Database
    participant HTTPClient
    participant ExternalService
    
    Client->>FastAPI: GET /api/health/services/1<br/>Authorization: Bearer <token>
    FastAPI->>HealthAPI: Route to health check handler
    HealthAPI->>ServiceRegistry: Get service by ID=1
    ServiceRegistry->>Database: SELECT * FROM services WHERE id=1
    Database-->>ServiceRegistry: Service record
    ServiceRegistry-->>HealthAPI: Service configuration
    HealthAPI->>HTTPClient: GET <service.health_check_url>
    HTTPClient->>ExternalService: HTTP GET request
    ExternalService-->>HTTPClient: Response (200 OK, 45ms)
    HTTPClient-->>HealthAPI: Health status
    HealthAPI->>Database: UPDATE services SET health_status='healthy', last_health_check=NOW()
    Database-->>HealthAPI: Updated
    HealthAPI->>FastAPI: {service, status, status_code, response_time_ms, timestamp}
    FastAPI-->>Client: Health check result
```

## Service Registration Flow

### Admin Service Registration

```mermaid
sequenceDiagram
    participant Admin
    participant FastAPI
    participant ServicesAPI
    participant AuthMiddleware
    participant ServiceRegistry
    participant Database
    
    Admin->>FastAPI: POST /api/services<br/>Authorization: Bearer <admin_token><br/>{name, service_type, base_url, ...}
    FastAPI->>ServicesAPI: Route to create service
    ServicesAPI->>AuthMiddleware: Validate token
    AuthMiddleware-->>ServicesAPI: User authenticated
    ServicesAPI->>AuthMiddleware: Check is_admin
    AuthMiddleware-->>ServicesAPI: User is admin
    ServicesAPI->>ServiceRegistry: Check if name exists
    ServiceRegistry->>Database: SELECT * FROM services WHERE name=?
    Database-->>ServiceRegistry: Not found
    ServiceRegistry-->>ServicesAPI: Name available
    ServicesAPI->>ServiceRegistry: Create service
    ServiceRegistry->>Database: INSERT INTO services (...)
    Database-->>ServiceRegistry: Service created (id)
    ServiceRegistry-->>ServicesAPI: ServiceResponse
    ServicesAPI->>FastAPI: HTTP 201 + Service data
    FastAPI-->>Admin: Service registered
```

## Error Handling Flow

### Authentication Error Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant AuthMiddleware
    participant JWT
    
    Client->>FastAPI: GET /api/services<br/>Authorization: Bearer <invalid_token>
    FastAPI->>AuthMiddleware: Extract token
    AuthMiddleware->>JWT: Verify token
    JWT-->>AuthMiddleware: Token invalid/expired
    AuthMiddleware->>FastAPI: HTTPException 401
    FastAPI-->>Client: 401 Unauthorized<br/>{detail: "Could not validate credentials"}
```

### Service Not Found Error Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant GatewayRouter
    participant ServiceRegistry
    participant Database
    
    Client->>FastAPI: GET /api/gateway/file-storage/libraries<br/>Authorization: Bearer <token>
    FastAPI->>GatewayRouter: Route handler
    GatewayRouter->>ServiceRegistry: Query service by type="file_storage"
    ServiceRegistry->>Database: SELECT * FROM services WHERE service_type='file_storage'
    Database-->>ServiceRegistry: No results
    ServiceRegistry-->>GatewayRouter: Service not found
    GatewayRouter->>FastAPI: HTTPException 404
    FastAPI-->>Client: 404 Not Found<br/>{detail: "File storage service not found"}
```

### Service Unavailable Error Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant GatewayRouter
    participant ServiceClient
    participant ExternalService
    
    Client->>FastAPI: GET /api/gateway/file-storage/libraries<br/>Authorization: Bearer <token>
    FastAPI->>GatewayRouter: Route handler
    GatewayRouter->>ServiceClient: Initialize client
    ServiceClient->>ExternalService: GET http://seafile:80/api2/repos/
    ExternalService-->>ServiceClient: Connection timeout/error
    ServiceClient-->>GatewayRouter: Service unavailable
    GatewayRouter->>FastAPI: HTTPException 502
    FastAPI-->>Client: 502 Bad Gateway<br/>{detail: "Service unavailable: Connection timeout"}
```

### Authorization Error Flow

```mermaid
sequenceDiagram
    participant User
    participant FastAPI
    participant ServicesAPI
    participant AuthMiddleware
    
    User->>FastAPI: POST /api/services<br/>Authorization: Bearer <user_token><br/>{service_data}
    FastAPI->>ServicesAPI: Route handler
    ServicesAPI->>AuthMiddleware: Validate token
    AuthMiddleware-->>ServicesAPI: User authenticated
    ServicesAPI->>AuthMiddleware: Check is_admin
    AuthMiddleware-->>ServicesAPI: User is not admin
    ServicesAPI->>FastAPI: HTTPException 403
    FastAPI-->>User: 403 Forbidden<br/>{detail: "Only admins can register services"}
```

## Data Flow Patterns

### Read Operation Flow

1. **Request Reception**: Client sends HTTP GET request
2. **Authentication**: Token validated, user loaded
3. **Authorization**: Permissions checked
4. **Data Retrieval**: Query database or external service
5. **Response Formatting**: Data formatted as JSON
6. **Response**: HTTP 200 with JSON body

### Write Operation Flow

1. **Request Reception**: Client sends HTTP POST/PUT request
2. **Authentication**: Token validated, user loaded
3. **Authorization**: Permissions checked (admin for writes)
4. **Input Validation**: Pydantic model validation
5. **Business Logic**: Process request
6. **Data Persistence**: Write to database
7. **Response**: HTTP 201/200 with created/updated data

### Delete Operation Flow

1. **Request Reception**: Client sends HTTP DELETE request
2. **Authentication**: Token validated, user loaded
3. **Authorization**: Admin check
4. **Existence Check**: Verify resource exists
5. **Deletion**: Remove from database
6. **Response**: HTTP 204 No Content

## Request/Response Transformation

### Request Transformation

```mermaid
graph LR
    ClientRequest[Client Request<br/>JSON] --> Validation[Pydantic Validation]
    Validation --> BusinessLogic[Business Logic]
    BusinessLogic --> DBQuery[Database Query]
    BusinessLogic --> ServiceCall[Service API Call]
```

### Response Transformation

```mermaid
graph LR
    DBResult[Database Result<br/>SQLAlchemy Model] --> Serialization[Pydantic Serialization]
    ServiceResponse[Service Response<br/>Raw JSON] --> Transformation[Data Transformation]
    Serialization --> JSONResponse[JSON Response]
    Transformation --> JSONResponse
```

## Caching Flow (Future)

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Cache
    participant Database
    
    Client->>FastAPI: GET /api/services
    FastAPI->>Cache: Check cache key="services:list"
    
    alt Cache Hit
        Cache-->>FastAPI: Cached data
        FastAPI-->>Client: Response from cache
    else Cache Miss
        FastAPI->>Database: Query services
        Database-->>FastAPI: Service data
        FastAPI->>Cache: Store in cache (TTL: 60s)
        FastAPI-->>Client: Response from database
    end
```

## Batch Operations Flow

### Bulk Health Check

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant HealthAPI
    participant ServiceRegistry
    participant HTTPClient
    participant Services
    
    Client->>FastAPI: GET /api/health/services
    FastAPI->>HealthAPI: Route handler
    HealthAPI->>ServiceRegistry: Get all services
    ServiceRegistry-->>HealthAPI: Services list
    
    par Parallel Health Checks
        HealthAPI->>HTTPClient: Check service 1
        HTTPClient->>Services: GET /health
        Services-->>HTTPClient: Response
        HTTPClient-->>HealthAPI: Status 1
    and
        HealthAPI->>HTTPClient: Check service 2
        HTTPClient->>Services: GET /health
        Services-->>HTTPClient: Response
        HTTPClient-->>HealthAPI: Status 2
    and
        HealthAPI->>HTTPClient: Check service 3
        HTTPClient->>Services: GET /health
        Services-->>HTTPClient: Response
        HTTPClient-->>HealthAPI: Status 3
    end
    
    HealthAPI->>FastAPI: Aggregated results
    FastAPI-->>Client: All service statuses
```

## See Also

- [Architecture Documentation](ARCHITECTURE.md) - System architecture overview
- [Service Integration Guide](SERVICE_INTEGRATION.md) - Service integration patterns
- [API Documentation](API.md) - API endpoint reference
