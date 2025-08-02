# Psychic Tribble
An interactive calendar dashboard built with FastAPI and SQLAlchemy.

## Features
- User, Event, Timeslot, and Calendar Management via RESTful APIs
- Modular Routing for clean API structure (/users, /events, /timeslots, /calendar)
- Configurable Database (SQLite by default; override with DATABASE_URL)
- Robust Error Handling and health check endpoint
- CORS Support for easy frontend integration
- Environment-based settings (development/production)
- Ready for Docker deployment

see project_path for project structure etc

## Quickstart

1. Clone & Install
```sh
git clone https://github.com/wifiknight45/psychic-tribble.git
cd psychic-tribble
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure Environment
Copy .env.example to .env and edit as needed (e.g., database URL, environment).

3. Run Locally
```sh
uvicorn psychic_tribble.app:app --reload
```

4. API Endpoints
- Health Check: GET /health
- Users: GET/POST /users
- Events: GET/POST /events
- Timeslots: GET/POST /timeslots
- Calendar: GET/POST /calendar
See the OpenAPI docs at: http://localhost:8000/docs

## Docker
Build and run using Docker:
```sh
docker build -t psychic-tribble .
docker run -p 8000:8000 --env-file .env psychic-tribble
```

## Development Notes
- Database: Uses SQLite by default; override with a different database by setting DATABASE_URL in your environment.
- CORS: Open to all origins in development. Update in app.py for production.
- Logging: DEBUG in development, INFO in production.
- Routers: Modularized for scalability—add more as needed in routes/ and services/.

## Testing
```sh
pytest
```

## Credits
Built with FastAPI, SQLAlchemy, and Uvicorn.
