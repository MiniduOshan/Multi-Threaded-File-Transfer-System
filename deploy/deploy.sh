#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$APP_DIR/.venv"

if [ ! -d "$APP_DIR/.git" ]; then
  echo "ERROR: $APP_DIR does not look like a git checkout"
  exit 1
fi

cd "$APP_DIR"
git fetch origin main
git reset --hard origin/main

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

# Install service units so each deploy keeps systemd definitions in sync.
SOCKET_UNIT_TMP="$(mktemp)"
WEB_UNIT_TMP="$(mktemp)"

sed "s|__APP_DIR__|$APP_DIR|g" "$APP_DIR/deploy/systemd/fileflow-socket.service" > "$SOCKET_UNIT_TMP"
sed "s|__APP_DIR__|$APP_DIR|g" "$APP_DIR/deploy/systemd/fileflow-web.service" > "$WEB_UNIT_TMP"

$SUDO install -m 644 "$SOCKET_UNIT_TMP" /etc/systemd/system/fileflow-socket.service
$SUDO install -m 644 "$WEB_UNIT_TMP" /etc/systemd/system/fileflow-web.service

rm -f "$SOCKET_UNIT_TMP" "$WEB_UNIT_TMP"

$SUDO systemctl daemon-reload
$SUDO systemctl enable fileflow-socket fileflow-web
$SUDO systemctl restart fileflow-socket fileflow-web

$SUDO systemctl --no-pager --full status fileflow-socket
$SUDO systemctl --no-pager --full status fileflow-web

echo "Deployment complete"