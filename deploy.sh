#!/bin/bash
set -e

IMAGE="scriptpilot"
CONTAINER="scriptpilot"
PORT="${PORT:-8000}"

echo "==> Deploying ScriptPilot"

# Check .env
if [ ! -f .env ]; then
  echo "Error: .env not found. Create it first."
  exit 1
fi

# Stop existing container
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "==> Stopping existing container..."
  docker stop "$CONTAINER" && docker rm "$CONTAINER"
fi

# Build
echo "==> Building image..."
docker build -t "$IMAGE" .

# Run
echo "==> Starting container on :${PORT}"
docker run -d \
  --name "$CONTAINER" \
  -p "${PORT}:8000" \
  --env-file .env \
  --restart unless-stopped \
  "$IMAGE"

echo ""
echo "ScriptPilot running: http://localhost:${PORT}"
docker logs -f "$CONTAINER"
