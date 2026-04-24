#!/bin/sh
# Probalyze — start script for Synology NAS (no Docker)

APP_DIR="/volume1/web/Probalyze"
NODE="/usr/local/bin/node"
PYTHON="/var/packages/Python3.9/target/usr/bin/python3"
UVICORN="$HOME/.local/bin/uvicorn"
LOG_DIR="$APP_DIR/logs"

mkdir -p "$LOG_DIR"

# Load env vars
set -a
. "$APP_DIR/.env"
set +a

export PYTHONPATH="$APP_DIR"
export NEXT_PUBLIC_API_URL="https://probalyze.picsnature.fr/api"

# ── Redis ─────────────────────────────────────────────────────────────────────
if ! redis-cli ping > /dev/null 2>&1; then
    echo "[probalyze] Starting Redis..."
    redis-server --daemonize yes --logfile "$LOG_DIR/redis.log" --port 6379
    sleep 1
fi
echo "[probalyze] Redis: OK"

# ── Kill existing processes ────────────────────────────────────────────────────
pkill -f "uvicorn apps.api.main" 2>/dev/null
pkill -f "apps.worker.main" 2>/dev/null
pkill -f "standalone/server.js" 2>/dev/null
sleep 1

# ── FastAPI (port 8000) ────────────────────────────────────────────────────────
echo "[probalyze] Starting FastAPI on :8000..."
cd "$APP_DIR"
nohup "$PYTHON" -m uvicorn apps.api.main:app \
    --host 0.0.0.0 --port 8000 --workers 2 \
    > "$LOG_DIR/api.log" 2>&1 &
echo $! > "$LOG_DIR/api.pid"
echo "[probalyze] API PID: $(cat $LOG_DIR/api.pid)"

# ── Worker (background) ────────────────────────────────────────────────────────
echo "[probalyze] Starting Worker..."
cd "$APP_DIR"
nohup "$PYTHON" -m apps.worker.main \
    > "$LOG_DIR/worker.log" 2>&1 &
echo $! > "$LOG_DIR/worker.pid"
echo "[probalyze] Worker PID: $(cat $LOG_DIR/worker.pid)"

# ── Next.js (port 3001) ────────────────────────────────────────────────────────
echo "[probalyze] Starting Next.js on :3001..."
cd "$APP_DIR/apps/web"
nohup "$NODE" node_modules/.bin/next start -p 3001 \
    > "$LOG_DIR/web.log" 2>&1 &
echo $! > "$LOG_DIR/web.pid"
echo "[probalyze] Web PID: $(cat $LOG_DIR/web.pid)"

sleep 2
echo ""
echo "=========================================="
echo " Probalyze démarré !"
echo " API  : http://localhost:8000/docs"
echo " Web  : http://localhost:3001"
echo " Logs : $LOG_DIR/"
echo "=========================================="
