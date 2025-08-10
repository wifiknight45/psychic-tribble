Psychic-Tribble 🔮📅
A secure, intuitive calendar and event management platform built for modern teams and individuals. Psychic-Tribble offers seamless scheduling, calendar synchronization, and a powerful API—all wrapped in a fast, scalable FastAPI backend.

⚠️ Proprietary Software Notice
This codebase is proprietary and confidential. Unauthorized use, copying, modification, or distribution is prohibited. For access or licensing inquiries, contact the development team.

🌟 Features

🔐 Secure Authentication - Email/password login with JWT token-based security
📋 Event Management - Create, view, edit, and delete events with an intuitive interface
📅 Interactive Calendar - Visual calendar view for easy event planning and overview
🔄 Calendar Sync - iCalendar feed integration for Google Calendar, Outlook, and other apps
⚡ High Performance - Built with FastAPI for speed and scalability
🛡️ Rate Limiting - Redis-powered API protection and request throttling
🌐 Cross-Platform Ready - Web interface foundation for future mobile apps

🏗️ Architecture
psychic-tribble/
├── app.py                 # Main FastAPI application
├── psychic_tribble/       # Core application modules
│   ├── db/               # Database models and schemas
│   ├── routes/           # API endpoint definitions
│   └── utils/            # Helper utilities and services
├── static/               # Web interface assets
│   ├── index.html        # Main web application
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript application logic
├── migrations/           # Database migration scripts
├── alembic.ini          # Database migration configuration
└── requirements.txt     # Python dependencies
🔧 Prerequisites

Python: 3.9 or higher
Redis: Local instance or cloud service
Database: SQLite (development) / PostgreSQL (production)

Core Dependencies
fastapi
sqlalchemy
alembic
passlib[bcrypt]
python-jose
slowapi
uvicorn
redis
🚀 Quick Start
For Authorized Collaborators

Clone and Setup
bashgit clone https://github.com/wifiknight45/psychic-tribble/
cd psychic-tribble

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

Environment Configuration
bashcp .env.example .env
Update your .env file:
envPYTT_ENV=development
DATABASE_URL=sqlite:///./development.db
SECRET_KEY=your_secret_key_here
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=["http://localhost:8000"]
RATE_LIMITS=["100/minute", "1000/day"]

Database Setup
bash# Run migrations (development only)
alembic upgrade head

Launch Application
bashuvicorn app:app --host 0.0.0.0 --port 8000 --reload

Access the Application

Web Interface: http://localhost:8000/static/index.html
API Documentation: http://localhost:8000/docs
Health Check: http://localhost:8000/health



💻 Using Psychic-Tribble
Web Interface
Navigate to the web interface and:

Login with your email and password
Manage Events in the Events section
View Calendar for visual event planning
Get Calendar Feed URL for external calendar sync

API Access

Authentication
bashPOST /token
{
  "email": "your-email@example.com",
  "password": "your-password"
}

Available Endpoints

/users - User management
/events - Event CRUD operations
/timeslots - Timeslot scheduling
/calendar - Calendar operations
/calendar/feed.ics - iCalendar feed download



Calendar Integration
Copy your personal iCalendar feed URL from the web interface and add it to:

Google Calendar
Outlook
Apple Calendar
Any iCalendar-compatible application

🛠️ Development
Development Mode
bash# Enable debug mode and auto-migrations
export PYTT_ENV=development
Security Features

Password Hashing: bcrypt for secure password storage
JWT Authentication: Stateless token-based authentication
Rate Limiting: Redis-backed request throttling

Testing
bash# Create tests directory and add pytest tests
mkdir tests
pip install pytest
pytest
🌍 Production Deployment
Environment Setup
envPYTT_ENV=production
DATABASE_URL=postgresql://user:password@localhost:5432/psychic_tribble
REDIS_URL=redis://your-redis-instance:6379/0
CORS_ORIGINS=["https://yourdomain.com"]
Deployment Options
Option 1: Uvicorn
bashuvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
Option 2: Gunicorn
bashgunicorn --worker-class uvicorn.workers.UvicornWorker --workers 4 app:app --bind 0.0.0.0:8000
Recommended Platforms

Render - Easy deployment with built-in PostgreSQL
Heroku - Quick setup with Redis add-ons
AWS - Full control with ECS/Lambda deployment
DigitalOcean - App Platform for simple deployment

📱 Roadmap
Psychic-Tribble is designed as a web-first platform with mobile expansion planned:

Phase 1: ✅ Web interface with FastAPI backend
Phase 2: 🔄 Docker containerization for cloud-native deployment
Phase 3: 📱 Android app (Kotlin) via Google Play
Phase 4: 🍎 iOS app (Swift) via App Store

📞 Contact & Support
Development Team

Crystal Andrews - andrews.crystal@gmail.com
Robert Hodgkiss - robert.hodgkiss@my.utsa.edu

For questions, bug reports, or feature requests, please reach out to the development team.

Psychic-Tribble - Seamless event planning for the modern world
Copyright © 2025 Psychic Tribble. All rights reserved.
This software is proprietary and confidential. Unauthorized use is prohibited without written permission from the authors.
