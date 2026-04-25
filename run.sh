#!/bin/bash

# Start PostgreSQL database (uses port 5435 to avoid conflicts)
docker-compose up -d db

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Run migrations
source venv/bin/activate
alembic upgrade head

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
