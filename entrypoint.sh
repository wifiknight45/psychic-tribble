#!/bin/bash
set -e

# Entrypoint script for psychic-tribble application
# Handles database migrations and starts the FastAPI application with proper signal handling

echo "Starting psychic-tribble application..."

# Function to handle shutdown signals
shutdown() {
    echo "Received shutdown signal, stopping application gracefully..."
    kill -TERM "$child" 2>/dev/null || true
    wait "$child"
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Run database migrations if alembic is configured and migrations directory exists
if [ -f "/app/tools/migrations/alembic.ini" ] && [ -d "/app/tools/migrations/migrations" ]; then
    echo "Running database migrations..."
    cd /app/tools/migrations && alembic upgrade head
elif [ -f "/app/tools/migrations/alembic.ini" ]; then
    echo "Alembic configuration found but no migrations directory - skipping migrations..."
else
    echo "No alembic configuration found, skipping migrations..."
fi

# Return to application directory
cd /app

# Get the correct module path for uvicorn
# The main FastAPI app is at src/psychic_tribble/app/main.py
export PYTHONPATH="/app/src:$PYTHONPATH"

# Start the FastAPI application with uvicorn
echo "Starting FastAPI application with uvicorn..."
uvicorn psychic_tribble.app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${UVICORN_WORKERS:-4}" \
    --log-level info &

child=$!

# Wait for the process to complete or receive a signal
wait "$child"