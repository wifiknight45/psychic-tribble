# Main.py Refactoring Guide

## Overview

The main.py file has been comprehensively refactored to implement modern FastAPI best practices, enhanced security, improved scalability, and better code organization. This guide explains the key changes and how to use the new features.

## Key Improvements

### 1. API Versioning 🔄

**Before**: All endpoints at root level (e.g., `/users`, `/events`)
**After**: All endpoints under versioned prefix (e.g., `/v1/users`, `/v1/events`)

```python
# New API structure
GET /v1/users          # List users
POST /v1/users         # Create user
GET /v1/events         # List events
GET /v1/calendar       # Get calendar data
```

**Benefits**:
- Backward compatibility support
- Future version management (v2, v3, etc.)
- Clear API evolution path

### 2. Request ID Middleware 🔍

**New Feature**: Unique correlation IDs for every request

```http
# Example request/response
GET /v1/users
X-Request-ID: 123e4567-e89b-12d3-a456-426614174000

{
  "data": [...],
  "request_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Benefits**:
- Distributed tracing
- Enhanced debugging
- Request correlation across services
- Better log analysis

### 3. Database Connection Pooling 🏊

**Before**: Basic database connections
**After**: Optimized connection pooling

```python
# Configuration in settings
DATABASE_POOL_SIZE = 20        # Base connections
DATABASE_MAX_OVERFLOW = 30     # Additional connections
DATABASE_POOL_TIMEOUT = 30     # Connection timeout
```

**Benefits**:
- Better performance under load
- Resource optimization
- Connection health monitoring
- Automatic connection recovery

### 4. Secrets Management 🔐

**New Feature**: Multi-provider secrets management

```python
# Environment variables (development)
await get_secret("DATABASE_PASSWORD")

# HashiCorp Vault (production)
init_secrets_manager("vault", 
    vault_url="https://vault.company.com",
    vault_token="vault-token"
)

# AWS Secrets Manager (production)
init_secrets_manager("aws", aws_region="us-east-1")
```

**Benefits**:
- Production-ready secrets handling
- Multiple provider support
- Secure credential management
- Easy migration path

### 5. Enhanced Security Headers 🛡️

**New Feature**: Comprehensive security headers

```http
# Response headers include:
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'...
Strict-Transport-Security: max-age=31536000
Permissions-Policy: geolocation=()...
```

**Benefits**:
- Protection against common attacks
- Browser security enforcement
- Compliance with security standards
- Defense in depth

### 6. Environment-Based Configuration 🌍

**Before**: Fixed API documentation
**After**: Environment-aware configuration

```python
# Development: API docs enabled
GET /docs     # ✅ Available
GET /redoc    # ✅ Available

# Production: API docs disabled
GET /docs     # ❌ Not available (security)
GET /redoc    # ❌ Not available (security)
```

**Benefits**:
- Production security
- Environment-specific behavior
- Configurable documentation exposure

### 7. Structured Logging 📊

**Before**: Simple text logs
**After**: Structured JSON logging

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "psychic_tribble.api.users",
  "message": "User created successfully",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": 42,
  "module": "users"
}
```

**Benefits**:
- Better log analysis
- Request correlation
- Structured data extraction
- Integration with log aggregation systems

### 8. Comprehensive Monitoring 📈

**New Features**: Enhanced monitoring endpoints

```http
GET /health    # Detailed health check
GET /metrics   # Application metrics
GET /ready     # Kubernetes readiness probe
GET /live      # Kubernetes liveness probe
```

**Response Example**:
```json
{
  "status": "healthy",
  "service": "psychic-tribble-api",
  "version": "1.0.0",
  "environment": "production",
  "request_id": "...",
  "uptime": {"hours": 24, "seconds": 86400},
  "checks": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

## Migration Guide

### For Existing Clients

**URL Updates Required**:
```bash
# Old URLs (still work but deprecated)
GET /users
POST /events

# New URLs (recommended)
GET /v1/users
POST /v1/events
```

### Environment Variables

**New Configuration Options**:
```bash
# Database pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30

# Secrets management
SECRETS_PROVIDER=vault  # or 'aws' or 'environment'
VAULT_URL=https://vault.company.com
VAULT_TOKEN=your-vault-token

# Security
ENABLE_HTTPS_REDIRECT=true
AUTH_RATE_LIMIT=5/minute

# Monitoring
ENABLE_METRICS=true
ENABLE_STRUCTURED_LOGGING=true
```

### Production Deployment

**Recommended Settings**:
```bash
ENV=production
DEBUG=false
SECRETS_PROVIDER=vault
ENABLE_HTTPS_REDIRECT=true
ENABLE_STRUCTURED_LOGGING=true
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100
```

## File Structure

### New Modular Organization

```
src/psychic_tribble/
├── app/
│   └── main.py              # Main application (refactored)
├── api/
│   ├── v1/
│   │   └── __init__.py      # API v1 router
│   └── routers/             # Individual route modules
├── middleware/
│   ├── request_id.py        # Request correlation
│   └── security_headers.py  # Security headers
├── core/
│   ├── database.py          # Database pooling
│   ├── secrets.py           # Secrets management
│   ├── logging_setup.py     # Structured logging
│   └── monitoring.py        # Metrics & monitoring
├── dependencies/
│   └── exception_handlers.py # Error handling
└── config.py                # Enhanced configuration
```

## Testing the Changes

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/

# Detailed health check
curl http://localhost:8000/health

# API version info
curl http://localhost:8000/v1/
```

### Request ID Tracking
```bash
# Check response headers
curl -I http://localhost:8000/v1/users
# Look for: X-Request-ID header
```

### Monitoring
```bash
# Application metrics
curl http://localhost:8000/metrics

# Readiness check
curl http://localhost:8000/ready
```

## Benefits Summary

### Security Improvements
- ✅ Environment-based API documentation
- ✅ Comprehensive security headers
- ✅ Secrets management preparation
- ✅ Enhanced input validation
- ✅ Proper middleware ordering

### Scalability Improvements
- ✅ Database connection pooling
- ✅ Request correlation tracking
- ✅ Structured logging for analysis
- ✅ Performance monitoring
- ✅ Resource optimization

### Maintainability Improvements
- ✅ Modular code organization
- ✅ Clear separation of concerns
- ✅ Comprehensive error handling
- ✅ Type hints throughout
- ✅ Extensive documentation

### Operational Improvements
- ✅ API versioning for evolution
- ✅ Health check endpoints
- ✅ Metrics collection
- ✅ Environment-aware configuration
- ✅ Production-ready deployment

## Next Steps

1. **Test thoroughly** in development environment
2. **Update client applications** to use `/v1/` prefix
3. **Configure secrets management** for production
4. **Set up monitoring** dashboards
5. **Deploy with confidence** 🚀

The refactored main.py provides a solid foundation for scaling the Psychic Tribble API while maintaining security and performance best practices.