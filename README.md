Psychic Tribble
Note: This codebase is proprietary and confidential. Unauthorized use, copying, modification, or distribution is strictly prohibited. For authorized access and inquiries, contact andrews.crystal@gmail.com or robert.hodgkiss@my.utsa.edu.

Table of Contents
Description
Project Structure
Prerequisites
Setup Instructions
Usage
Development Notes
Production Deployment
Contact
About

Description
Psychic Tribble is a robust backend solution for web and mobile applications, providing secure user authentication, comprehensive event management, flexible timeslot scheduling, and integrated calendar functionality. Built with the high-performance FastAPI framework, it ensures efficient and scalable API endpoints with automatic API documentation, data validation via Pydantic, and asynchronous processing. SQLAlchemy manages database operations, while Redis enables rate limiting for enhanced security and performance.
This codebase is proprietary and confidential. Unauthorized use, copying, modification, or distribution is strictly prohibited.
Project Structure

app.py: Main application entry point, defining the FastAPI app, database setup, authentication, and core routers.
psychic_tribble/: Contains database models (db/), routes (routes/), and utilities (core/utils.py).
static/: Directory for static assets (e.g., HTML, CSS, JS).
alembic.ini: Configuration for database migrations (development only).
migrations/: Directory for Alembic migration scripts.

Prerequisites

Python 3.9+
Redis server (running locally or accessible via REDIS_URL)
Database (SQLite for development, PostgreSQL recommended for production)
Virtual environment (recommended)

Dependencies:

fastapi
sqlalchemy
alembic
passlib[bcrypt]
python-jose
slowapi
uvicorn
redis

Setup Instructions
For authorized collaborators only:

Clone the Repository:
git clone https://github.com/wifiknight45/psychic-tribble/
cd psychic-tribble


Set Up a Virtual Environment (recommended):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Dependencies:
pip install -r requirements.txt


Configure Environment:

Copy .env.example to .env.
Update the variables in .env:
PYTT_ENV: Set to 'development' or 'production'.
DATABASE_URL: Database connection string (e.g., 'sqlite:///./development.db' for development, or 'postgresql://user:password@localhost:5432/psychic_tribble' for production).
SECRET_KEY: A secure key for JWT authentication (generate using python -c "import os; print(os.urandom(32).hex())").
REDIS_URL: Redis connection string (e.g., 'redis://localhost:6379/0').
CORS_ORIGINS: Comma-separated list of allowed origins for CORS (e.g., ["http://localhost:3000","https://yourdomain.com"]).
RATE_LIMITS: API rate limits (e.g., ["100/minute","1000/day"]).




Run Migrations (development only):
alembic upgrade head


Start the Server:
uvicorn app:app --host 0.0.0.0 --port 8000 --reload



Usage
Authentication

Use the /token endpoint to obtain a JWT token via OAuth2 password flow (e.g., POST /token with username and password).

API Endpoints

/users: User management (requires authentication).
/events: Event creation and management.
/timeslots: Timeslot scheduling.
/calendar: Calendar operations.
/health: Health check endpoint.

API Documentation

Access automatic API documentation at:
/docs (Swagger UI)
/redoc (ReDoc)when the server is running.



Rate Limiting

Configured via RATE_LIMITS in .env (e.g., ["100/minute","1000/day"]).

Static Files

Serve front-end assets from /static.

Development Notes

Debug Mode: Enabled when PYTT_ENV=development, providing auto-migrations and detailed logging.
Security: Uses bcrypt for password hashing and JWT for authentication.
Database: Supports SQLite (development) and PostgreSQL (production).
Testing: Run tests using pytest (if tests are implemented).

Production Deployment
For production:

Set PYTT_ENV=production in .env to disable debug mode and auto-migrations.
Use a production-ready database like PostgreSQL.
Start the server with multiple workers for better performance:uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4


Alternatively, use Gunicorn with Uvicorn workers:gunicorn --worker-class uvicorn.workers.UvicornWorker --workers 4 app:app --bind 0.0.0.0:8000


Ensure Redis is configured for rate limiting.

Contact
For issues or inquiries, contact andrews.crystal@gmail.com or robert.hodgkiss@my.utsa.edu.
About
Interactive calendar dashboard
Copyright (c) 2025 [The App]. All rights reserved.
This software and its source code are proprietary and confidential. Unauthorized use, copying, modification, distribution, or reproduction in any form is prohibited without prior written permission from andrews.crystal@gmail.com or robert.hodgkiss@my.utsa.edu.
