# Psychic-Tribble Repository - Copilot Coding Agent Instructions

## Repository Overview

**Psychic-Tribble** is a secure, scalable calendar and event management platform built with FastAPI. It provides seamless scheduling, calendar synchronization, and a powerful API backend. The project follows modern Python practices with comprehensive security features, monitoring, and enterprise-grade architecture.

### High-Level Repository Information

- **Project Type**: FastAPI-based web application with API backend
- **Primary Language**: Python 3.8+ (developed/tested on Python 3.12)
- **Architecture**: Modular FastAPI application with async/await patterns
- **Database**: SQLAlchemy with async support (SQLite for development, PostgreSQL for production)
- **Key Frameworks**: FastAPI, SQLAlchemy, Alembic, Redis, Pydantic
- **Target Runtime**: Production deployment via Docker, Uvicorn/Gunicorn
- **Repository Size**: Medium-complexity project with ~50+ source files
- **Code Organization**: Standard Python src/ layout with comprehensive test coverage

## Build and Validation Instructions

### Environment Setup - CRITICAL REQUIREMENTS

**Always run these steps before any development work:**

1. **Python Version**: Requires Python 3.8+ (3.12 recommended)
2. **Virtual Environment**: Always create and activate a virtual environment
3. **Environment Variables**: Copy `.env.example` to `.env` and configure

```bash
# Essential setup sequence - run in this exact order
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
```

### Dependency Installation - SEQUENTIAL APPROACH REQUIRED

**IMPORTANT**: Install dependencies in this specific order due to package conflicts:

```bash
# Step 1: Install core runtime dependencies first
pip install -r requirements.txt

# Step 2: Install development dependencies
pip install -r requirements-dev.txt

# Step 3: Install package in editable mode
pip install -e .
```

**Known Issues**: 
- Network timeouts may occur during pip install - retry if needed
- `python-jose` version conflicts exist - requirements.txt has been fixed
- Some packages require compilation (psycopg2-binary) - may need build tools

### Environment Configuration - MANDATORY

**Always copy and configure environment variables:**

```bash
cp .env.example .env
# Edit .env file with appropriate values for your environment
```

**Critical Environment Variables:**
- `SECRET_KEY`: Must be changed in production (minimum 64 characters)
- `DATABASE_URL`: SQLite for development, PostgreSQL for production
- `ENV`: Set to "development", "testing", "staging", or "production"
- `REDIS_URL`: Required for rate limiting and caching

### Database Setup and Migrations

**Database migrations using Alembic:**

```bash
# Initialize database (development)
alembic upgrade head

# For testing with specific database
DATABASE_URL=sqlite+aiosqlite:///./test.db alembic upgrade head
```

**Migration files location**: `tools/migrations/`
**Configuration**: `tools/migrations/alembic.ini`

### Running the Application

**Development Server:**
```bash
# Standard development server with auto-reload
uvicorn src.psychic_tribble.app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative entry point (if main app is in root)
uvicorn psychic_tribble.main:app --reload --host 0.0.0.0 --port 8000
```

**Production Server:**
```bash
# Using Gunicorn with Uvicorn workers
gunicorn src.psychic_tribble.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Application Endpoints:**
- API Base: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc` 
- Health Check: `http://localhost:8000/health`
- API v1 Routes: `http://localhost:8000/v1/*`

### Testing - COMPREHENSIVE APPROACH

**Test Execution Order:**

```bash
# 1. Run unit tests with coverage
pytest tests/ --cov=src/psychic_tribble --cov-report=xml -v

# 2. Run specific test files
pytest tests/api/v1/test_events.py -v

# 3. Run tests with database services (requires Docker/services)
pytest tests/ --cov=psychic_tribble --cov-report=xml --maxfail=1 -v --disable-warnings
```

**Test Configuration:**
- Test config: `tests/conftest.py`
- Test database: In-memory SQLite
- Test environment: `ENV=testing`
- Coverage reports: Generated in `coverage.xml`

**Required Services for Integration Tests:**
- Redis (localhost:6379)
- PostgreSQL (localhost:5432) for full CI tests

### Linting and Code Quality

**Primary Linter: Ruff (replaces flake8, black, isort)**

```bash
# Run Ruff linter
ruff check src/ tests/

# Run Ruff formatter
ruff format src/ tests/
```

**Legacy Linting (GitHub CI uses this):**
```bash
# Critical lint checks (exits on error)
flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,__pycache__

# Full lint checks (warnings only)
flake8 src tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=venv,__pycache__
```

**Pre-commit Hooks:**
```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files
```

### Docker Build and Deployment

**Development Docker Build:**
```bash
# Build Docker image
docker build -t psychic-tribble .

# Run container
docker run -p 8000:8000 --env-file .env psychic-tribble
```

**CI/CD Docker Build:**
```bash
# Production build with build metadata
docker build -f dockerfile.cicd -t psychic-tribble:latest --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') .
```

**Docker Compose (if available):**
```bash
cd psychic_tribble/
docker-compose up -d
```

### Build Validation - COMPLETE WORKFLOW

**Execute this sequence to validate your environment:**

```bash
# 1. Clean environment setup
rm -rf venv/ *.db
python3 -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .

# 3. Configure environment
cp .env.example .env

# 4. Database setup
alembic upgrade head

# 5. Run tests
pytest tests/ -v

# 6. Run linting
ruff check src/ tests/

# 7. Start development server (test in another terminal)
uvicorn src.psychic_tribble.app.main:app --reload --port 8000

# 8. Validate endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

**Expected build time**: 2-5 minutes depending on network speed
**Expected test time**: 30-60 seconds for full test suite

## Project Layout and Architecture

### Directory Structure

```
psychic-tribble/                 # Root directory
├── src/psychic_tribble/         # Main source code (NEW architecture)
│   ├── app/main.py             # FastAPI application entry point
│   ├── api/routers/            # API route definitions (v1 versioning)
│   ├── core/                   # Core business logic and utilities
│   ├── domain/models.py        # SQLAlchemy data models
│   ├── domain/schemas/         # Pydantic schemas for validation
│   ├── services/               # Business logic services
│   ├── nlp/                    # Natural language processing modules
│   └── config.py               # Enhanced configuration management
├── core/routers/               # Legacy route definitions
├── tests/                      # Comprehensive test suite
│   ├── api/v1/                 # API endpoint tests
│   ├── core/                   # Core functionality tests
│   ├── db/                     # Database model tests
│   └── conftest.py             # Test configuration
├── docs/                       # Documentation and static assets
├── scripts/                    # Utility scripts
├── tools/migrations/           # Alembic database migrations
├── .github/workflows/          # CI/CD pipeline definitions
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml             # Python project configuration
├── .env.example               # Environment variable template
└── dockerfile                 # Production Docker configuration
```

### Key Architectural Components

**Main Application**: `src/psychic_tribble/app/main.py`
- FastAPI application factory
- Middleware configuration (CORS, security headers, rate limiting)
- API versioning with `/v1/` prefix
- Request ID correlation for distributed tracing
- Environment-based configuration

**Configuration**: `src/psychic_tribble/config.py`
- Environment-specific settings (development, testing, staging, production)
- Secrets management integration (Vault, AWS Secrets Manager)
- Validation for production security requirements
- Database connection pooling configuration

**Database Models**: `src/psychic_tribble/domain/models.py`
- SQLAlchemy async models
- Migration support via Alembic

**API Routes**: `src/psychic_tribble/api/routers/`
- Versioned API endpoints (`/v1/`)
- Modular route organization
- Authentication and authorization decorators

### CI/CD and Validation Pipeline

**GitHub Actions Workflows** (`.github/workflows/`):

1. **build-test.yml**: Main CI pipeline
   - Lint checking with flake8
   - Unit and integration tests with pytest
   - PostgreSQL and Redis service containers
   - Coverage reporting
   - Package building
   - Template rendering tests

2. **docker_test.yml**: Docker build validation
3. **static.yml**: Static site generation  
4. **jekyll-gh-pages.yml**: Documentation publishing

**Pre-commit Configuration**: `.github/workflows/.pre-commit-config.yaml`
- Code formatting (Black, isort)
- Linting (flake8, ruff)
- Security scanning (bandit, detect-secrets)
- Type checking (mypy)

### Security and Dependencies

**Security Features**:
- JWT authentication with configurable expiration
- Rate limiting with Redis backend
- CORS protection with configurable origins
- Security headers middleware
- HTTPS redirect capability
- Secrets management for production

**Critical Dependencies**:
- `fastapi[standard]`: Web framework
- `uvicorn[standard]`: ASGI server
- `sqlalchemy`: Async ORM
- `alembic`: Database migrations
- `redis`: Rate limiting and caching
- `passlib[bcrypt]`: Password hashing
- `python-jose[cryptography]`: JWT handling
- `slowapi`: Rate limiting middleware

**Development Dependencies**:
- `pytest`: Testing framework
- `pytest-asyncio`: Async test support
- `pytest-cov`: Coverage measurement
- `ruff`: Fast linting and formatting
- `pre-commit`: Git hooks management

### Important Notes for Coding Agents

1. **Always use absolute imports** when referencing modules within the project
2. **Environment-based configuration** is critical - check `ENV` variable for behavior
3. **Database operations must be async** - use `await` with SQLAlchemy operations
4. **API versioning is enforced** - new endpoints should use `/v1/` prefix
5. **Security middleware order matters** - see `main.py` for correct sequence
6. **Rate limiting is Redis-dependent** - ensure Redis is available for full functionality
7. **Tests require database setup** - run `alembic upgrade head` before testing
8. **Docker builds use multi-stage approach** - see `dockerfile` for optimization

### Validation Commands Quick Reference

```bash
# Environment check
python --version && pip --version

# Dependency check  
pip list | grep -E "(fastapi|uvicorn|sqlalchemy)"

# Database check
alembic current

# Service check
curl -f http://localhost:8000/health || echo "Server not running"

# Test check
pytest tests/ --tb=short -q

# Lint check
ruff check src/ --quiet || echo "Linting issues found"
```

**IMPORTANT**: Always trust these instructions and only search for additional information if these instructions are incomplete or contain errors. This repository uses a complex but well-documented architecture that requires following the specific setup and build sequences outlined above.

