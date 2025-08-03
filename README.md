Psychic Tribble 

Psychic Tribble is the core backend logic for a web and mobile application, providing user authentication, event management, timeslot scheduling, and calendar functionality. Built with FastAPI, SQLAlchemy, and Redis, it ensures secure, scalable, and rate-limited API endpoints for seamless integration with front-end clients.
This codebase is proprietary and confidential. Unauthorized use, copying, modification, or distribution is strictly prohibited.
Copyright
Copyright (c) 2025 [The App]. All rights reserved.
This software and its source code are proprietary and confidential. Unauthorized use, copying, modification, distribution, or reproduction in any form is prohibited without prior written permission from andrews.crystal@gmail.com or robert.hodgkiss@my.utsa.edu. 

Project Structure
app.py: Main application entry point, defining the FastAPI app, database setup, authentication, and core routers.
psychic_tribble/: Contains database models, routes, and utilities.
static/: Directory for static assets (e.g., HTML, CSS, JS).
alembic.ini: Configuration for database migrations (development only).

Prerequisites

Python 3.9+
Redis server
Database (SQLite for development, PostgreSQL recommended for production)
Dependencies: fastapi, sqlalchemy, alembic, passlib[bcrypt], python-jose, slowapi, uvicorn, redis

Setup Instructions
For authorized collaborators only:

Clone the Repository:git clone <https://github.com/wifiknight45/psychic-tribble/>
cd psychic-tribble


Install Dependencies:pip install -r requirements.txt


Configure Environment:
Copy .env.example to .env and update variables:
PYTT_ENV: Set to development or production.
DATABASE_URL: Database connection string (e.g., sqlite:///./development.db or PostgreSQL URL).
SECRET_KEY: Secure key for JWT authentication.
REDIS_URL: Redis connection string (e.g., redis://localhost:6379/0).
CORS_ORIGINS: Allowed origins for CORS (e.g., ["https://yourdomain.com"]).
RATE_LIMITS: API rate limits (e.g., ["100/minute"]).




Run Migrations (development only):alembic upgrade head


Start the Server:uvicorn app:app --host 0.0.0.0 --port 8000 --reload



Usage

Authentication: Use the /token endpoint to obtain a JWT token via OAuth2 password flow.
API Endpoints:
/users: User management (requires authentication).
/events: Event creation and management.
/timeslots: Timeslot scheduling.
/calendar: Calendar operations.
/health: Health check endpoint.


Rate Limiting: Configurable via RATE_LIMITS in .env.
Static Files: Serve front-end assets from /static.

Development Notes

Debug Mode: Enabled when PYTT_ENV=development. Includes auto-migrations and detailed logging.
Security: Uses bcrypt for password hashing and JWT for authentication.
Database: Supports SQLite (development) and PostgreSQL (production).

Contact
For issues or inquiries, contact andrews.crystal@gmail.com or robert.hodgkiss@my.utsa.edu.
