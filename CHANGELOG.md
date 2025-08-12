# Changelog

## 2025-08-12 04:57
updated workflow/file github.com/wifiknight45/psychic-tribble/.github/workflows/
Pre-test Docker checks: Added docker info and docker-compose version to confirm runner environment.

Robust container readiness:

Introduced healthcheck polling with fallback to manual delay.

Gracefully handles missing or unhealthy web container.

Detailed startup diagnostics: Injected docker-compose ps and selective logs after container launch.

Improved failure logging:

Captures service status and targeted web logs.

Includes fallback logging from all containers.

Cleanup improvements: Ensures removal of volumes and orphaned containers via docker-compose down --volumes --remove-orphans.

## 2025-08-11 18:00

new docker_test.yml updates:

a) HEALTH_TIMEOUT 
previously listed "180" as a string, new version lists 180 as an integer. Both versions are acceptable in bash but string quoting might be safer in YAML and more consistent with .env formats which are already in first stage of dev (before staging/testing).
b) Quoting of env vars
old vers "${WEB_SERVICE}" vs new ${WEB_SERVICE} wrapping in quotes avoids bash misinterpretation if value has spaces.
c) exit - re: conditions and container inspect logic
explicit update for true and if guards
d) comments trimmed for clarity 

structural parity between most recent docker_test.yml updates
i) Docker Compose v2 usage (docker compose, not docker-compose)

ii) Full service health checks with fallback if missing

iii) Per-service log capture and artifact upload

iv) Clean teardown with volume/orphan removal

v) Security-conscious job permissions (contents: read)


## 2025-08-11 07:03

- Added proper refresh-token support to match the frontend (webstack): `/token` now returns both `access_token` and `refresh_token`, and a new `/refresh` endpoint issues rotated tokens.
- Made the iCalendar feed accessible to calendar clients by supporting a `?token=` query parameter (so they don’t need Authorization headers). It accepts an access token for now.
- Prevented CORS misconfiguration: using `allow_credentials=True` with `*` is invalid. Now we auto-tune credentials based on origins, with friendly dev defaults.
- Made static mounting resilient when the `static/` directory doesn’t exist.
- Hardened rate-limiting initialization: if Redis isn’t available (common in dev), it falls back gracefully to in-memory.
- Safer datetime handling in ICS generation in case your DB holds naive datetimes.
- Production safety: guard against default `SECRET_KEY` in non-debug mode.
- Dev ergonomics: avoid `reload=True` with multiple workers.

These changes bring your backend in line with the updated frontend you shared and make the ICS feed usable by external calendar apps.

### How this aligns with the frontend
- `/register`: Your frontend’s `Auth.signup()` now has a real endpoint to call.
- `/token`: Returns `access_token` and `refresh_token` as expected by your JS.
- `/refresh`: Matches your frontend’s JSON POST to rotate tokens.
- ICS feed: Your frontend’s `updateIcsUrl()` builds `.../calendar/feed.ics?token=${access_token}`; this is now supported server-side.

If you want to step up ICS security later, we can add a dedicated, revocable `ics_token` per user (DB field + generator endpoint), and validate that in the feed instead of the access token.

## 2025-08-06 05:53

### Core (runtime) dependencies
- `fastapi[standard] >= 0.116.1`: Install FastAPI with interactive docs, JSON Schema, and performance extras.
- `uvicorn[standard] >= 0.35.0`: ASGI server with HTTP/1.1, HTTP/2, WebSockets, auto-reload, environment loading, and more.
- `sqlalchemy >= 2.0.0,<3.0`: Modern SQL toolkit and ORM; 2.x series is stable and aligned with latest features.
- `psycopg2-binary >= 2.9.0,<3.0`: Pre-compiled PostgreSQL adapter for rapid setup; consider `psycopg2` from source in production for binary upgradeability.
- `alembic >= 1.16.4`: Database migration tool by SQLAlchemy, latest 1.16.x release ensures compat with SQLAlchemy 2.x.
- `redis >= 4.6.0`: Python client for Redis, supports sync and async APIs (compatible with Redis 5/6/7).
- `httpx >= 0.28.1`: Next-generation HTTP client with sync & async support, HTTP/2, CLI integration.
- `jinja2 >= 3.1.6`: Fast, expressive templating engine with autoescaping, async support, i18n with Babel.
- `icalendar >= 6.3.1,<7.0`: RFC 5545–compliant parser/generator; defaults to modern zoneinfo for timezones.
- `python-dotenv >= 1.0.0`: Load environment variables from a `.env` file for clean configuration separation.
- `pydantic >= 1.10.0,<2.0`: Data validation and settings management core to FastAPI’s request/response models.

### Optional / Timezone
- `pytz >= 2025.2`: Legacy timezone support for Python < 3.9; new projects should prefer the standard `zoneinfo` module.

### Development & CI Tools
- `pytest >= 7.0.0,<8.0.0`: Mature test framework with rich assertion introspection and fixtures.
- `pytest-asyncio >= 1.1.0`: Asyncio support plugin, lets you `@pytest.mark.asyncio` on async def tests.
- `pytest-cov >= 6.2.1`: Coverage plugin that wraps `coverage.py`, supports subprocesses and parallel testing.
- `flake8 >= 7.3.0`: Style guide enforcement combining PyFlakes, pycodestyle, McCabe complexity checks.
- `ruff >= 0.12.7`: Ultra-fast linter/formatter in Rust, replaces flake8, black, isort, and more in a single tool.
- `pre-commit >= 2.20.0`: Framework for managing Git hooks across languages—lint, format, security checks on staged files.
- `tox >= 4.0.0`: Virtualenv management and test orchestrator across Python versions.
- `build >= 0.8.0`: PEP 517 frontend for building source and wheel distributions.
- `setuptools >= 61.0.0`: Packaging and distribution utilities, including PEP 517 support.
- `wheel >= 0.37.0`: Library for generating and installing wheel packages.
- `twine >= 6.1.0`: Secure uploading of source and wheel distributions to PyPI and other indexes.
- `bump2version >= 1.0.1`: Fork of bumpversion for automating semantic version bumps, commits, and tags.
- `click >= 8.2.1`: Decorator-based toolkit for building composable command-line interfaces.
- `ipython >= 9.4.0`: Enhanced interactive shell and Jupyter Python kernel for REPL-driven development.

## 2025-08-03 22:54

### Psychic Tribble Project Directory Structure

A well-organized Python project structure for the `psychic_tribble` application, designed for modularity and scalability. Below is the directory layout with descriptions for each component.

#### Root Directory
- `psychic_tribble/`: Main project directory (aka root or main) containing the core application code.
- `static/`: Stores static assets like CSS, JavaScript, and images (aka frontend or webstack)
- `templates/`: Contains HTML templates for the web interface. (these are for templates/jekyll pages I have yet to setup)
- `tests/`: Houses test files for unit and integration testing. (fuzzing, linting and other bullshit)
- `requirements.txt`: Lists Python dependencies for the project. (this will have to be updated before prod, a prod + dev file paths exist, .env files need to be added to a vault. 
- `Dockerfile`: Defines the Docker container setup for the application.
- `.env.example`: Sample environment variable configuration file.

#### Detailed Structure
- `psychic_tribble/`
  - Core application code organized into modules for different functionalities.
  - `__init__.py`: Marks the directory as a Python package.
  - `main.py`: Entry point for running the application.
  - `config/`
    - `__init__.py`: Marks the directory as a Python package.
    - `settings.py`: Contains application settings (e.g., database URLs, API keys).
  - `api/`
    - `v1/`
      - `__init__.py`: Marks the directory as a Python package.
      - `users.py`: Handles user-related API endpoints (e.g., CRUD operations for users).
      - `events.py`: Manages event-related API endpoints.
      - `timeslots.py`: Deals with timeslot-related API endpoints.
      - `calendar.py`: Provides calendar-related API endpoints.
  - `core/`
    - `__init__.py`: Marks the directory as a Python package.
    - `app.py`: Initializes the main application (e.g., Flask/FastAPI setup).
    - `utils.py`: Utility functions used across the application.
  - `services/`
    - `__init__.py`: Marks the directory as a Python package.
    - `user_service.py`: Logic for user management (e.g., authentication, user data processing).
    - `event_service.py`: Logic for event management.
    - `timeslot_service.py`: Logic for timeslot scheduling and management.
    - `calendar_service.py`: Logic for calendar operations.
  - `db/`
    - `__init__.py`: Marks the directory as a Python package.
    - `session.py`: Manages database sessions (e.g., SQLAlchemy session setup).
    - `models.py`: Defines database models (e.g., ORM models for users, events).
    - `migrations/`: Stores database migration scripts.
  - `schemas.py`: Defines data schemas (e.g., Pydantic models for API validation).

- `static/`
  - Static assets for the web interface.
  - `css/`
    - `style.css`: Main CSS file for styling the web interface.
  - `js/`
    - `app.js`: Main JavaScript file for client-side logic.
  - `images/`: Directory for storing images (currently empty).

- `templates/`
  - HTML templates for rendering the web interface.
  - `base.html`: Base HTML template for the application.

- `tests/`
  - Test suites for ensuring code quality and functionality.
  - `api/v1/`
    - `test_users.py`: Tests for user-related API endpoints.
    - `test_events.py`: Tests for event-related API endpoints.
    - `test_timeslots.py`: Tests for timeslot-related API endpoints.
    - `test_calendar.py`: Tests for calendar-related API endpoints.
  - `core/`
    - `test_utils.py`: Tests for utility functions in `core/utils.py`.
  - `services/`
    - `test_user_service.py`: Tests for user service logic.
  - `db/`
    - `test_models.py`: Tests for database models.
  - `conftest.py`: Pytest configuration file for shared test fixtures.

#### Additional Files
- `requirements.txt`: Specifies Python packages required to run the application.
- `Dockerfile`: Instructions for building a Docker image for the application.
- `.env.example`: Template for environment variables (e.g., database credentials, API keys).

## 2025-08-03 06:09

template for root directory/filepaths
psychic_tribble/
├── psychic_tribble/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── users.py
│   │       ├── events.py
│   │       ├── timeslots.py
│   │       └── calendar.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── utils.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── event_service.py
│   │   ├── timeslot_service.py
│   │   └── calendar_service.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   ├── models.py
│   │   └── migrations/
│   └── schemas.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── images/
├── templates/
│   └── base.html
├── tests/
│   ├── api/v1/
│   │   ├── test_users.py
│   │   ├── test_events.py
│   │   ├── test_timeslots.py
│   │   └── test_calendar.py
│   ├── core/
│   │   └── test_utils.py
│   ├── services/
│   │   └── test_user_service.py
│   ├── db/
│   │   └── test_models.py
│   └── conftest.py
├── requirements.txt
├── Dockerfile
└── .env.example
```
