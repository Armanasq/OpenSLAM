#!/bin/bash

# OpenSLAM Complete System Startup Script

set -e

echo "========================================="
echo "   OpenSLAM v2.0 - Starting System"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0.32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}[1/4] Checking Python environment...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "  Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt 2>&1 | grep -v "Requirement already satisfied" || true

echo -e "${GREEN}✓ Python environment ready${NC}"
echo ""

echo -e "${BLUE}[2/4] Checking Node.js environment...${NC}"

# Check if node_modules exists in frontend
if [ ! -d "frontend/node_modules" ]; then
    echo "  Installing Node.js dependencies (this may take a few minutes)..."
    cd frontend
    npm install --silent
    cd ..
fi

echo -e "${GREEN}✓ Node.js environment ready${NC}"
echo ""

echo -e "${BLUE}[3/4] Creating required directories...${NC}"

# Create all required directories
mkdir -p data uploads results cache temp logs plugins connectors

echo -e "${GREEN}✓ Directories created${NC}"
echo ""

echo -e "${BLUE}[4/4] Starting services...${NC}"

# Kill any existing processes on the ports
echo "  Checking for existing processes..."
lsof -ti:8007 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true

# Start backend in background
echo "  Starting FastAPI backend on port 8007..."
python3 run_backend.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if ! curl -s http://localhost:8007/api/health > /dev/null; then
    echo -e "${YELLOW}⚠ Backend may not have started properly. Check logs/backend.log${NC}"
else
    echo -e "${GREEN}✓ Backend started successfully (PID: $BACKEND_PID)${NC}"
fi

# Start frontend in background
echo "  Starting React frontend on port 3001..."
cd frontend
SKIP_PREFLIGHT_CHECK=true ESLINT_NO_DEV_ERRORS=true npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✓ Frontend started successfully (PID: $FRONTEND_PID)${NC}"
echo ""

echo "========================================="
echo "   🚀 OpenSLAM is Ready!"
echo "========================================="
echo ""
echo -e "${GREEN}Access the application:${NC}"
echo "  🌐 Frontend:  http://localhost:3001"
echo "  📡 Backend:   http://localhost:8007"
echo "  📖 API Docs:  http://localhost:8007/docs"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  Backend:  tail -f logs/backend.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""
echo -e "${YELLOW}To stop the system:${NC}"
echo "  Press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "========================================="

# Save PIDs for cleanup
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# Wait for user interrupt
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; exit 0" INT TERM

# Keep script running
wait
