#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo "Starting OpenSLAM v0.2..."
echo "1. Starting Code Server (Docker)..."
source /home/arman/.venv/bin/activate
python tools/docker_runner.py &
CODE_SERVER_PID=$!
sleep 3
echo "2. Starting Backend Server..."
python -m uvicorn backend.main:app --reload --port 8007 &
BACKEND_PID=$!
sleep 3
echo "3. Starting Frontend Server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..
echo ""
echo "All services started!"
echo "Code Server PID: $CODE_SERVER_PID"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Access:"
echo "  - Code Editor: http://localhost:8080"
echo "  - Frontend: http://localhost:3001"
echo "  - Backend API: http://localhost:8007"
echo ""
echo "Press Ctrl+C to stop all services"
trap "echo 'Stopping services...'; kill $CODE_SERVER_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
