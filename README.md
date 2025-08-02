Overview
This repository contains the backend application for the Psychic Tribble scheduling and calendar service. It’s built with FastAPI and SQLAlchemy, with automated database migrations, hardened security settings, rate limiting, and CI/CD pipelines for quality checks.

Features
Automatic Alembic migrations on startup

Centralized environment-driven configuration

Hardened CORS settings with allowed origins, methods, and headers

Rate limiting via SlowAPI to prevent abuse

Request-size limiting to protect against oversized payloads

Structured logging and comprehensive exception handling

Modular routers for Users, Events, Timeslots, and Calendar

GitHub Actions CI/CD pipelines for linting, testing, and security scans

Prerequisites
Python 3.9 or newer

A SQLAlchemy-compatible database (SQLite by default)

git, pip (or poetry)

Installation
Clone the repository

bash
git clone https://github.com/your-org/psychic-tribble.git
cd psychic-tribble
Create and activate a virtual environment

bash
python -m venv .venv
source .venv/bin/activate
Install dependencies

bash
pip install -r requirements.txt
Configuration
Configuration is managed via environment variables (or a .env file). Defaults are shown in parentheses:

PYTT_ENV (development)

DATABASE_URL (sqlite:///./development.db)

ALEMBIC_INI (alembic.ini)

HOST (0.0.0.0)

PORT (8000)

CORS_ORIGINS (comma-separated; defaults to your production domain)

RATE_LIMITS (e.g. 100/minute)

MAX_BODY_SIZE (10485760 bytes = 10 MB)

Database Migrations
Alembic is configured to run on application startup. Make sure your alembic.ini and env.py are properly set:

bash
# on startup, FastAPI will automatically execute:
alembic upgrade head
To generate a new migration after model changes:

bash
alembic revision --autogenerate -m "Your migration message"
alembic upgrade head
CI/CD Pipelines
A GitHub Actions workflow is included under .github/workflows/ci.yml. It runs:

flake8 for linting

pytest for unit and integration tests

bandit or safety for security vulnerability scanning

Push to main or open a pull request to trigger the pipeline.

Running the Application
Start the server locally with hot-reload:

bash
uvicorn app:app \
  --host ${HOST:-0.0.0.0} \
  --port ${PORT:-8000} \
  --reload
API Endpoints
Health & Root
GET /health Returns service status:

json
{ "status": "ok" }
GET / (hidden) Returns welcome message and current version.

Users
Prefix: /users Tags: Users Database session injected via dependency.

Events
Prefix: /events Tags: Events

Timeslots
Prefix: /timeslots Tags: Timeslots

Calendar
Prefix: /calendar Tags: Calendar

Error Handling
422 Request validation errors return a structured list of field errors.

404 Resource not found returns { "detail": "Resource not found" }.

429 Rate limit exceeded returns { "detail": "Too Many Requests" }.

500 Internal errors return { "detail": "Internal server error", "error_id": "<id>" }.
