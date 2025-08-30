#!/bin/bash
# Run database migrations

echo "Running database migrations..."
alembic upgrade head

echo "Migrations complete. Starting Uvicorn server..."
uvicorn backend.api.main:app --reload
