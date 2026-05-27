#!/bin/bash
set -e

echo "==> Starting ScriptPilot (dev mode)"

# Check .env
if [ ! -f .env ]; then
  echo "Error: .env not found. Create it first."
  exit 1
fi

# Backend
if [ ! -d .venv ]; then
  echo "==> Creating venv and installing dependencies..."
  python3 -m venv .venv
  .venv/bin/pip install -q -r backend/requirements.txt
fi

# Frontend
if [ ! -d frontend/node_modules ]; then
  echo "==> Installing frontend dependencies..."
  cd frontend && npm install && cd ..
fi

echo "==> Starting backend on :8000"
.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

echo "==> Starting frontend on :5173"
cd frontend && npx vite --host 127.0.0.1 --port 5173 &
FRONTEND_PID=$!
cd ..

echo ""
echo "ScriptPilot running:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop."

cleanup() {
  echo ""
  echo "==> Stopping..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM

wait
