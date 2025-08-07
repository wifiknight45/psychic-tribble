The Psychic-Tribble app offers a secure and intuitive way to manage events, schedule timeslots, and sync with your calendar using a modern web interface and API. Built with FastAPI, it’s fast, scalable, and perfect for teams or individuals.

Note: This codebase is proprietary and confidential. Unauthorized use, copying, modification, or distribution is prohibited. For access or inquiries, contact andrews.crystal@gmail.com or robert.hodgkiss@my.utsa.edu.

Table of Contents

What Is Psychic Tribble?
Features
Project Structure
Prerequisites
Setup Instructions
Using the App
Development Tips
Deploying to Production
Contact
About

What Is Psychic Tribble?
Psychic Tribble is a powerful event management app designed for seamless scheduling and calendar integration. Whether you’re planning team meetings or personal events, it offers:

A user-friendly web interface with a calendar view.
Secure login and event management via API.
iCalendar feed for syncing with Google Calendar, Outlook, and more.

Screenshot of GUI interface or dashboard app or website splash page

Secure Authentication: Log in with email and password to access your events.
Event Management: Create, view, and delete events with a clean interface.
Calendar View: Visualize events using an interactive calendar.
iCalendar Feed: Sync events with external calendar apps.
Fast and Scalable: Built with FastAPI for high performance.
Rate Limiting: Protects the API using Redis for secure access.

Project Structure
app.py: Main app, sets up FastAPI, database, and API routes.
psychic_tribble/: Contains database models (db/), API routes (routes/), and utilities (utils/).
static/: Web interface files (HTML, CSS, JS).
alembic.ini & migrations/: Database migration configuration and scripts.

Prerequisites
Python: 3.9 or higher.
Redis: Running locally or via a service (set REDIS_URL).
Database: SQLite for development, PostgreSQL for production.
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


Set Up a Virtual Environment:
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate


Install Dependencies:
pip install -r requirements.txt


Configure Environment:
Copy .env.example to .env.
Update .env with:
PYTT_ENV: development or production.
DATABASE_URL: E.g., sqlite:///./development.db or postgresql://user:password@localhost:5432/psychic_tribble.
SECRET_KEY: Generate with python -c "import os; print(os.urandom(32).hex())".
REDIS_URL: E.g., redis://localhost:6379/0.
CORS_ORIGINS: E.g., ["http://localhost:8000", "https://yourdomain.com"].
RATE_LIMITS: E.g., ["100/minute", "1000/day"].


Run Database Migrations (development only):
alembic upgrade head

Start the Server:
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

Visit http://localhost:8000/static/index.html to see the web interface.

Using the App

Web Interface:
Open http://localhost:8000/static/index.html (INPUT DEPLOYED URL HERE).
Log in with your email and password.
Create, view, or delete events in the “Events” or “Calendar” sections.
Copy the iCalendar feed URL from the “Calendar Feed” section to sync with Google Calendar or Outlook.

API Access:
Log in via POST /token with email and password to get a JWT token.
Use the token to access:
/users: Manage user accounts.
/events: Create, view, or delete events.
/timeslots: Schedule timeslots.
/calendar: Calendar operations.
/calendar/feed.ics: Download your iCalendar feed.

Explore API docs at /docs (Swagger UI) or /redoc.

Health Check: Visit /health to confirm the server is running.

Development Tips
Debug Mode: Set PYTT_ENV=development for auto-migrations and detailed logs.
Security: Uses bcrypt for passwords and JWT for authentication.
Database: SQLite for development; switch to PostgreSQL for production.
Testing: Add tests with pytest (create a tests/ folder if needed).
Static Files: Customize the web interface in static/ (e.g., index.html, css/style.css, js/app.js).

Deploying to Production
Set PYTT_ENV=production in .env to disable debug mode and auto-migrations.
Use a PostgreSQL database and update DATABASE_URL.
Ensure Redis is running and REDIS_URL is set.
Deploy with:uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4

Or 
use Gunicorn:gunicorn --worker-class uvicorn.workers.UvicornWorker --workers 4 app:app --bind 0.0.0.0:8000

Host on a platform like Render, Heroku, or AWS.
Update CORS_ORIGINS for your production domain.
Test the web interface at https://yourdomain.com/static/index.html.

Contact
For questions or issues, reach out to:
andrews.crystal@gmail.com
robert.hodgkiss@my.utsa.edu

About
Psychic Tribble is an interactive calendar dashboard for seamless event planning. Copyright © 2025 Psychic Tribble. All rights reserved.This software is proprietary and confidential. Unauthorized use is prohibited without written permission from the authors.
