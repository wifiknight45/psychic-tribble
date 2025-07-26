# psychic-tribble

Scheduling API Backend (MVP)
A minimal Flask-based backend for creating users, events, timeslots, and signing users up for those timeslots. This MVP is designed to run in any Python environment—local Debian/ParrotOS, Google Colab (with optional ngrok tunneling), or Docker—and serves as the foundation for a future mobile app and desktop/web interface.

Table of Contents

I. Overview

II. Architecture & Data Model

III. Prerequisites

IV. Installation

V. Running the Application

VI. API Endpoints

VII. Create User

VIII. Create Event

IX. Add Timeslot

X. Assign User to Timeslot

XI. View Calendar

XII. Detailed Workflow

XIII. Sample Requests & Responses

XIV. Scaling & Next Steps

I. Overview
This Flask application provides a simple RESTful API for scheduling purposes:

users can be created

events can be defined

time windows (timeslots) can be added to events

users can sign up for a specific timeslot

a consolidated calendar view returns all events, timeslots, and sign-ups

All data is stored in memory for this MVP, making it easy to understand the core logic before integrating a persistent database or authentication system.

II. Architecture & Data Model
The application uses three in-memory Python dictionaries:

USERS

key: user_id (UUID string)

value: { "name": string }

EVENTS

key: event_id (UUID string)

value: { "name": string, "timeslots": { ts_id: {...} } }

ASSIGNMENTS

key: ts_id (UUID string of a timeslot)

value: set(user_id, ...)

Each timeslot object under EVENTS[event_id]["timeslots"] contains:

json
{
  "day": "Monday",
  "start": "09:00",
  "end": "10:00"
}
The ASSIGNMENTS map tracks which user IDs have signed up for each timeslot.

III. Prerequisites
Python 3.7 or higher

pip (Python package installer)

(Optional for Colab) flask-ngrok for public tunneling

IV. Installation
Clone this repo or copy app.py into your project directory.

Create a virtual environment (recommended):

bash
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows
Install Flask (and ngrok if needed):

bash
pip install flask
# Optional for Google Colab
pip install flask-ngrok

V. Running the Application
Local / Live-USB Debian (ParrotOS)
bash
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000 --debug
Or simply:

bash
python psychic-tribble.py
Google Colab
In a notebook cell, install dependencies:

bash
!pip install flask flask-ngrok
Upload psychic-tribble.py to Colab, then run:

bash
!python psychic-tribble.py
If flask-ngrok is installed, the script will automatically open a public URL.

VI. API Endpoints
All endpoints consume and return JSON. The base URL defaults to http://localhost:5000 (or the ngrok URL in Colab).

VII. Create User
URL: POST /users

Body:

json
{ "name": "Alice" }
Success Response:

Code: 201 Created

Body:

json
{ "user_id": "550e8400-e29b-41d4-a716-446655440000" }
Create Event
URL: POST /events

Body:

json
{ "name": "Team Sync" }
Success Response:

Code: 201 Created

Body:

json
{ "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479" }
Add Timeslot
URL: POST /events/<event_id>/timeslots

Body:

json
{
  "day": "Monday",
  "start": "09:00",
  "end": "10:00"
}
Success Response:

Code: 201 Created

Body:

json
{ "timeslot_id": "a6f8abe2-1f45-4ae4-b4e6-1234567890ab" }
Assign User to Timeslot
URL: POST /timeslots/<timeslot_id>/assign

Body:

json
{ "user_id": "550e8400-e29b-41d4-a716-446655440000" }
Success Response:

Code: 200 OK

Body:

json
{ "message": "Assigned successfully" }
View Calendar
URL: GET /calendar

Success Response:

Code: 200 OK

Body:

json
[
  {
    "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Team Sync",
    "timeslots": [
      {
        "timeslot_id": "a6f8abe2-1f45-4ae4-b4e6-1234567890ab",
        "day": "Monday",
        "start": "09:00",
        "end": "10:00",
        "assigned_users": [
          { "user_id": "550e8400-e29b-41d4-a716-446655440000", "name": "Alice" }
        ]
      }
    ]
  }
]

Detailed Workflow

VII. Create a user

POST to /users

Server validates name field, generates UUID, stores in USERS.

VIII. Create an event

POST to /events

Server validates name, generates UUID, stores event skeleton in EVENTS.

IX. Add timeslot

POST to /events/<event_id>/timeslots

Validate existence of event and required fields (day, start, end).

Convert start/end strings to Python datetime.time objects via parse_time().

Enforce start < end.

Generate a timeslot UUID, save under the event, initialize empty assignment set.

X. Assign user to timeslot

POST to /timeslots/<ts_id>/assign

Validate timeslot and user existence.

Add user ID into ASSIGNMENTS[ts_id].

XI. View calendar

XII. Detailed Workflow
GET /calendar

Iterate all events, timeslots, and assignments.

Build a JSON structure combining event details with assigned user names.

XIII. Sample Requests & Responses
Below is a quick curl walkthrough:

bash
# 1. New User
curl -X POST localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice"}'

# 2. New Event
curl -X POST localhost:5000/events \
  -H "Content-Type: application/json" \
  -d '{"name":"Team Sync"}'

# 3. Add Timeslot
curl -X POST localhost:5000/events/<EVENT_ID>/timeslots \
  -H "Content-Type: application/json" \
  -d '{"day":"Monday","start":"09:00","end":"10:00"}'

# 4. Assign User
curl -X POST localhost:5000/timeslots/<TS_ID>/assign \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<USER_ID>"}'

# 5. View Calendar
curl localhost:5000/calendar
Replace <EVENT_ID>, <TS_ID>, <USER_ID> with the UUIDs returned by earlier calls.

XIV. Scaling & Next Steps
a) Persistent Storage

b) Migrate from in-memory dicts to a relational database (PostgreSQL/MySQL) or NoSQL (MongoDB).

c) Use SQLAlchemy or a similar ORM for data modeling and migrations.

d) Authentication & Authorization

e) Integrate JWT or OAuth2 for user sign-up/login.

f) Protect endpoints so only authenticated clients can create/assign.

Web & Mobile Frontend

a) Build a React/Next.js or Vue.js web dashboard for interactive scheduling.

b) Use React Native or Flutter for mobile apps.

Deployment & Scaling

a) Containerize with Docker.

b) Orchestrate with Kubernetes for high availability.

c) Use a WSGI server (Gunicorn/uWSGI) behind NGINX.

Real-time Updates

a) Add WebSocket support (e.g., Flask-SocketIO) for live calendar pushes.

b) Implement notifications (email, SMS, push) on new assignments.

This README was designed to capture the Minimum Viable Product (aka MVP) logic, API contract, and next-step blueprint for growing the app (codenamed "psychic-tribble" aka "psychic-tribble.py") into a full-featured scheduling platform across mobile, desktop, and web interfaces etc. 
