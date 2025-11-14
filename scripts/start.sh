#!/bin/bash

echo "Starting OpenSLAM v0.1..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start backend server in background
echo "Starting backend server..."
python backend/api/main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Install frontend dependencies and start
echo "Installing frontend dependencies..."
cd frontend
npm install

echo "Starting frontend development server..."
npm start &
FRONTEND_PID=$!

echo "OpenSLAM is starting up..."
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Access the application at: http://localhost:3001"
echo "Backend API at: http://localhost:8007"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait