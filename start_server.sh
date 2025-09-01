#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Find an available port
PORT=8000
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; do
    echo "Port $PORT is in use, trying next port..."
    PORT=$((PORT + 1))
done

echo "================================================"
echo "Starting TravelBook Backend Server"
echo "================================================"
echo ""
echo "Server will run on: http://localhost:$PORT"
echo "API endpoints: http://localhost:$PORT/api/"
echo "Admin panel: http://localhost:$PORT/admin/"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================================"

# Run the server
python manage.py runserver 0.0.0.0:$PORT