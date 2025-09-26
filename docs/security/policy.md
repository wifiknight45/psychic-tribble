# Security Policies for Psychic-Tribble Development

## Table of Contents

1. [Overview](#overview)
2. [Coding Standards](#coding-standards)
3. [Secret Management](#secret-management)
4. [Dependency Management](#dependency-management)
5. [Code Review Process](#code-review-process)
6. [Authentication and Authorization](#authentication-and-authorization)
7. [Data Protection](#data-protection)
8. [Infrastructure Security](#infrastructure-security)
9. [Incident Response](#incident-response)
10. [Compliance and Monitoring](#compliance-and-monitoring)

## 1. Overview

### 1.1 Purpose

This document establishes security policies and procedures for the development, deployment, and maintenance of the Psychic-Tribble calendar and task management platform. These policies ensure the confidentiality, integrity, and availability of user data and system resources.

### 1.2 Scope

These policies apply to:
- All developers and contributors to the Psychic-Tribble project
- Development, staging, and production environments
- Third-party integrations and dependencies
- CI/CD pipelines and deployment processes
- Data handling and storage procedures

### 1.3 Responsibilities

- **Development Team**: Implement secure coding practices, follow review processes
- **DevOps Team**: Secure infrastructure configuration, monitoring, and incident response
- **Security Team**: Policy enforcement, security reviews, and compliance oversight
- **Project Maintainers**: Overall security governance and decision-making

## 2. Coding Standards

### 2.1 Secure Coding Principles

#### 2.1.1 Input Validation
```python
# REQUIRED: Validate all user inputs
from pydantic import BaseModel, validator, Field
from typing import Optional

class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    
    @validator('title')
    def validate_title(cls, v):
        # Sanitize and validate title
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
```

#### 2.1.2 Output Encoding
```python
# REQUIRED: Properly encode outputs to prevent XSS
import html
from markupsafe import Markup

def safe_render_description(description: str) -> str:
    """Safely render user-provided description content."""
    return html.escape(description)
```

#### 2.1.3 Error Handling
```python
# REQUIRED: Secure error handling
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

try:
    # Database operation
    result = await database_operation()
except DatabaseError as e:
    # Log detailed error for debugging
    logger.error(f"Database error in user operation: {e}", extra={"user_id": user.id})
    # Return generic error to user
    raise HTTPException(status_code=500, detail="Internal server error")
```

### 2.2 Authentication Implementation

#### 2.2.1 Password Handling
```python
# REQUIRED: Secure password hashing
import bcrypt
from typing import str

def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)  # Minimum 12 rounds
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

#### 2.2.2 JWT Token Management
```python
# REQUIRED: Secure JWT implementation
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

def create_access_token(data: Dict[Any, Any], expires_delta: timedelta = None) -> str:
    """Create JWT access token with expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Short-lived tokens
    
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```

### 2.3 Database Security

#### 2.3.1 SQL Injection Prevention
```python
# REQUIRED: Use parameterized queries via SQLAlchemy ORM
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_events(db: AsyncSession, user_id: int, title_filter: str = None):
    """Safely retrieve user events with optional filtering."""
    query = select(Event).where(Event.user_id == user_id)
    
    if title_filter:
        # Safe parameterized query - SQLAlchemy handles escaping
        query = query.where(Event.title.contains(title_filter))
    
    result = await db.execute(query)
    return result.scalars().all()

# PROHIBITED: Raw SQL with string formatting
# NEVER DO THIS:
# query = f"SELECT * FROM events WHERE user_id = {user_id} AND title LIKE '%{title}%'"
```

### 2.4 API Security

#### 2.4.1 Rate Limiting
```python
# REQUIRED: Implement rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")  # Limit login attempts
async def login(request: Request, credentials: UserLogin):
    # Login implementation
    pass
```

## 3. Secret Management

### 3.1 Environment Variables

#### 3.1.1 Required Practices
- **MANDATORY**: All secrets must be stored in environment variables
- **PROHIBITED**: Hardcoded secrets, passwords, or API keys in source code
- **REQUIRED**: Use `.env.example` template for documentation

#### 3.1.2 Environment Variable Naming
```bash
# REQUIRED: Consistent naming convention
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-jwt-secret-here
API_KEY_EXTERNAL_SERVICE=your-api-key

# PROHIBITED: Exposing secrets in variable names
PASSWORD_FOR_JOHN=secret123  # DON'T DO THIS
```

### 3.2 Secret Validation

#### 3.2.1 Startup Validation
```python
# REQUIRED: Validate secrets on application startup
import os
import sys
from typing import List

def validate_required_secrets() -> List[str]:
    """Validate all required environment variables are present."""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL', 
        'JWT_SECRET_KEY',
        'REDIS_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif var == 'SECRET_KEY' and len(value) < 64:
            missing_vars.append(f"{var} (too short, minimum 64 characters)")
    
    return missing_vars

# Check secrets on startup
missing_secrets = validate_required_secrets()
if missing_secrets:
    print(f"Missing required environment variables: {missing_secrets}")
    sys.exit(1)
```

### 3.3 Development vs Production

#### 3.3.1 Development Environment
```bash
# .env.development
ENV=development
SECRET_KEY=dev-secret-key-at-least-64-characters-long-for-development-only
DATABASE_URL=sqlite+aiosqlite:///./psychic_tribble_dev.db
REDIS_URL=redis://localhost:6379/0
DEBUG=true
LOG_LEVEL=DEBUG
```

#### 3.3.2 Production Environment
```bash
# .env.production (example - actual values must be different)
ENV=production
SECRET_KEY=<STRONG-RANDOM-64-CHAR-SECRET>
DATABASE_URL=postgresql+asyncpg://user:strong_password@prod-db:5432/psychic_tribble
REDIS_URL=redis://prod-redis:6379/0
DEBUG=false
LOG_LEVEL=INFO
SENTRY_DSN=<SENTRY-DSN>
```

## 4. Dependency Management

### 4.1 Dependency Security Policies

#### 4.1.1 Approved Dependencies
- **REQUIRED**: All dependencies must be specified in `requirements.txt` or `requirements-dev.txt`
- **REQUIRED**: Pin exact versions for production dependencies
- **RECOMMENDED**: Use version ranges for development dependencies

#### 4.1.2 Version Pinning Strategy
```text
# requirements.txt - REQUIRED: Pin exact versions for production
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.13.0
pydantic==2.5.0
redis==5.0.1

# requirements-dev.txt - ALLOWED: Use compatible version ranges
pytest>=7.4.0,<8.0.0
black>=23.0.0,<24.0.0
ruff>=0.1.0,<0.2.0
```

### 4.2 Vulnerability Management

#### 4.2.1 Automated Scanning
- **REQUIRED**: Dependabot alerts enabled for all repositories
- **REQUIRED**: Safety checks in CI pipeline for every commit
- **REQUIRED**: Weekly automated dependency updates via Dependabot

#### 4.2.2 Vulnerability Response
```yaml
# REQUIRED: Response times for vulnerability severity levels
Critical: 24 hours
High: 72 hours  
Medium: 1 week
Low: 1 month
```

### 4.3 Dependency Review Process

#### 4.3.1 New Dependencies
Before adding any new dependency, ensure:
- [ ] Dependency is actively maintained (commits within last 6 months)
- [ ] No known critical vulnerabilities
- [ ] Compatible license (MIT, Apache 2.0, BSD)
- [ ] Minimal necessary permissions
- [ ] Alternatives evaluated

#### 4.3.2 Prohibited Dependencies
- Packages with known unpatched critical vulnerabilities
- Packages from untrusted sources or maintainers
- Packages that require excessive system permissions
- Packages with restrictive or incompatible licenses

## 5. Code Review Process

### 5.1 Security Review Requirements

#### 5.1.1 Mandatory Security Review
All pull requests touching the following areas require security review:
- Authentication and authorization logic
- Database queries and data access
- User input handling and validation
- Cryptographic operations
- Configuration and environment variables
- Third-party integrations

#### 5.1.2 Security Review Checklist
```markdown
## Security Review Checklist

### Authentication & Authorization
- [ ] Proper authentication checks on protected endpoints
- [ ] Authorization rules correctly implemented
- [ ] No privilege escalation vulnerabilities
- [ ] JWT tokens properly validated

### Input Validation
- [ ] All user inputs validated using Pydantic models
- [ ] SQL injection prevention via ORM usage
- [ ] XSS prevention through output encoding
- [ ] File upload restrictions and validation

### Data Protection
- [ ] Sensitive data properly encrypted or hashed
- [ ] No secrets exposed in logs or error messages
- [ ] Database queries follow least privilege principle
- [ ] Personal data handled according to privacy policies

### Configuration Security
- [ ] No hardcoded secrets or credentials
- [ ] Environment variables properly used
- [ ] Production configuration secure
- [ ] Debug modes disabled in production
```

### 5.2 Branch Protection Rules

#### 5.2.1 Main Branch Protection
```yaml
# REQUIRED: GitHub branch protection settings
required_status_checks:
  strict: true
  contexts:
    - "Security Checks"
    - "Tests"
    - "Linting"
    - "Dependency Scan"

enforce_admins: true
required_pull_request_reviews:
  required_approving_review_count: 2
  dismiss_stale_reviews: true
  require_code_owner_reviews: true

restrictions:
  users: []
  teams: ["security-team", "senior-developers"]
```

## 6. Authentication and Authorization

### 6.1 Password Policy

#### 6.1.1 Requirements
- Minimum 12 characters length
- Must contain at least 3 of: uppercase, lowercase, numbers, special characters
- Cannot be common passwords (check against common password lists)
- Cannot contain username or email
- Must be different from last 5 passwords

#### 6.1.2 Implementation
```python
# REQUIRED: Password strength validation
import re
from typing import List

def validate_password_strength(password: str, username: str = None, email: str = None) -> List[str]:
    """Validate password meets security requirements."""
    errors = []
    
    if len(password) < 12:
        errors.append("Password must be at least 12 characters long")
    
    # Check character requirements
    checks = [
        (r'[a-z]', "lowercase letter"),
        (r'[A-Z]', "uppercase letter"), 
        (r'[0-9]', "number"),
        (r'[!@#$%^&*(),.?":{}|<>]', "special character")
    ]
    
    met_requirements = sum(1 for pattern, _ in checks if re.search(pattern, password))
    if met_requirements < 3:
        errors.append("Password must contain at least 3 different character types")
    
    # Check against username/email
    if username and username.lower() in password.lower():
        errors.append("Password cannot contain username")
    if email and email.split('@')[0].lower() in password.lower():
        errors.append("Password cannot contain email")
    
    return errors
```

### 6.2 Session Management

#### 6.2.1 JWT Configuration
```python
# REQUIRED: Secure JWT settings
JWT_SETTINGS = {
    'ACCESS_TOKEN_EXPIRE_MINUTES': 15,      # Short-lived access tokens
    'REFRESH_TOKEN_EXPIRE_DAYS': 7,         # Refresh tokens for convenience
    'ALGORITHM': 'HS256',                   # Secure algorithm
    'ISSUER': 'psychic-tribble',            # Token issuer
    'AUDIENCE': 'psychic-tribble-users',    # Token audience
}
```

#### 6.2.2 Session Security
- Access tokens expire within 15 minutes
- Refresh tokens expire within 7 days
- Token rotation on each refresh
- Secure token storage (httpOnly cookies recommended for web clients)
- Token revocation capability for logout

### 6.3 Role-Based Access Control

#### 6.3.1 Role Definitions
```python
# REQUIRED: Role-based permissions
from enum import Enum
from typing import Set

class Role(Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class Permission(Enum):
    READ_OWN_EVENTS = "read:own_events"
    WRITE_OWN_EVENTS = "write:own_events"
    READ_ALL_EVENTS = "read:all_events"
    WRITE_ALL_EVENTS = "write:all_events"
    MANAGE_USERS = "manage:users"
    SYSTEM_CONFIG = "system:config"

ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.USER: {
        Permission.READ_OWN_EVENTS,
        Permission.WRITE_OWN_EVENTS,
    },
    Role.MODERATOR: {
        Permission.READ_OWN_EVENTS,
        Permission.WRITE_OWN_EVENTS,
        Permission.READ_ALL_EVENTS,
    },
    Role.ADMIN: {
        Permission.READ_OWN_EVENTS,
        Permission.WRITE_OWN_EVENTS,
        Permission.READ_ALL_EVENTS,
        Permission.WRITE_ALL_EVENTS,
        Permission.MANAGE_USERS,
        Permission.SYSTEM_CONFIG,
    }
}
```

## 7. Data Protection

### 7.1 Encryption Requirements

#### 7.1.1 Data at Rest
- Database connections must use TLS
- Sensitive fields encrypted using application-level encryption
- Backups encrypted with separate keys
- File storage encrypted (if applicable)

#### 7.1.2 Data in Transit
- All external communications over HTTPS/TLS 1.3
- Internal service communications over HTTPS
- Database connections encrypted
- Redis connections authenticated and encrypted

### 7.2 Data Classification

#### 7.2.1 Sensitivity Levels
```python
# REQUIRED: Data classification
from enum import Enum

class DataSensitivity(Enum):
    PUBLIC = "public"           # No restrictions
    INTERNAL = "internal"       # Organization only
    CONFIDENTIAL = "confidential"  # Restricted access
    RESTRICTED = "restricted"   # Highest protection

# Data classification mapping
DATA_CLASSIFICATION = {
    'user_email': DataSensitivity.CONFIDENTIAL,
    'user_password_hash': DataSensitivity.RESTRICTED,
    'calendar_events': DataSensitivity.CONFIDENTIAL,
    'task_lists': DataSensitivity.CONFIDENTIAL,
    'system_logs': DataSensitivity.INTERNAL,
    'api_documentation': DataSensitivity.PUBLIC,
}
```

### 7.3 Privacy Protection

#### 7.3.1 Personal Data Handling
- Minimize data collection to necessary information only
- Obtain explicit consent for data processing
- Provide data export capabilities
- Implement data deletion upon request
- Regular data retention review and cleanup

## 8. Infrastructure Security

### 8.1 Container Security

#### 8.1.1 Docker Security Requirements
```dockerfile
# REQUIRED: Secure Dockerfile practices
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory and ownership
WORKDIR /app
COPY --chown=appuser:appuser . .

# Use non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### 8.2 Network Security

#### 8.2.1 Network Controls
- Implement network segmentation
- Use firewall rules to restrict access
- Enable logging for network access
- Regular network security assessments

### 8.3 Monitoring and Logging

#### 8.3.1 Security Logging Requirements
```python
# REQUIRED: Security event logging
import logging
from datetime import datetime
from typing import Optional

security_logger = logging.getLogger('security')

def log_security_event(
    event_type: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None
):
    """Log security events for monitoring and incident response."""
    security_logger.info(
        f"SECURITY_EVENT: {event_type}",
        extra={
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'details': details or {}
        }
    )

# Example usage
log_security_event(
    event_type='LOGIN_FAILED',
    user_id=None,
    ip_address='192.168.1.100',
    details={'username': 'john@example.com', 'attempts': 3}
)
```

## 9. Incident Response

### 9.1 Incident Classification

#### 9.1.1 Severity Levels
- **Critical**: Data breach, system compromise, service unavailable
- **High**: Privilege escalation, unauthorized access, significant vulnerabilities
- **Medium**: Failed attacks, suspicious activity, minor vulnerabilities
- **Low**: Policy violations, unsuccessful attacks, informational events

### 9.2 Response Procedures

#### 9.2.1 Immediate Response (0-1 hour)
1. Identify and classify the incident
2. Contain the threat to prevent further damage
3. Notify security team and stakeholders
4. Begin evidence collection and preservation

#### 9.2.2 Investigation Phase (1-24 hours)
1. Detailed analysis of the incident
2. Determine scope and impact
3. Identify root cause and attack vectors
4. Develop remediation plan

#### 9.2.3 Recovery Phase (24-72 hours)
1. Implement fixes and patches
2. Restore affected systems and data
3. Monitor for recurring issues
4. Update security controls

#### 9.2.4 Post-Incident (1 week)
1. Document lessons learned
2. Update policies and procedures
3. Conduct post-incident review
4. Implement preventive measures

## 10. Compliance and Monitoring

### 10.1 Compliance Requirements

#### 10.1.1 Security Audits
- Quarterly internal security reviews
- Annual external security assessments
- Continuous vulnerability scanning
- Regular penetration testing

### 10.2 Policy Enforcement

#### 10.2.1 Automated Enforcement
- Pre-commit hooks for secret scanning
- CI/CD pipeline security checks
- Automated dependency vulnerability scanning
- Code quality and security linting

#### 10.2.2 Manual Reviews
- Security code reviews for critical changes
- Architecture reviews for new features
- Access reviews for user permissions
- Configuration reviews for infrastructure changes

### 10.3 Training and Awareness

#### 10.3.1 Required Training
- Secure coding practices for all developers
- Security awareness training for all team members
- Incident response procedures for security team
- Regular updates on emerging threats and vulnerabilities

## Document Information

- **Version**: 1.0
- **Effective Date**: 2024-01-15
- **Review Cycle**: Quarterly
- **Owner**: Security Team
- **Approved By**: Project Leadership

## Policy Exceptions

Any exceptions to these policies must be:
1. Documented with business justification
2. Approved by security team and project leadership
3. Time-bound with regular review
4. Compensating controls implemented where possible

---

*This document contains sensitive security information and should be handled according to information classification policies.*
