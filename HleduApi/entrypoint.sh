#!/bin/bash
set -e

APP_ENV=${ENV:-dev}

echo "Starting Hledu API in $APP_ENV environment..."

if [ "$APP_ENV" = "prod" ]; then
    echo "Production mode: Using Gunicorn with multiple workers"
    exec gunicorn app.main:app \
        --bind 0.0.0.0:8000 \
        --workers 4 \
        --worker-class uvicorn.workers.UvicornWorker \
        --worker-connections 1000 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --timeout 30 \
        --keep-alive 2 \
        --access-logfile - \
        --error-logfile - \
        --log-level info
elif [ "$APP_ENV" = "stg" ]; then
    echo "Staging mode: Using Gunicorn with fewer workers"
    exec gunicorn app.main:app \
        --bind 0.0.0.0:8000 \
        --workers 2 \
        --worker-class uvicorn.workers.UvicornWorker \
        --worker-connections 500 \
        --max-requests 500 \
        --max-requests-jitter 50 \
        --timeout 30 \
        --keep-alive 2 \
        --access-logfile - \
        --error-logfile - \
        --log-level info
else
    echo "Development mode: Using Uvicorn with auto-reload"
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --factory \
        --log-level debug
fi