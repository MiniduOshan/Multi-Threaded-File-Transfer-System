#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

$SUDO apt update
$SUDO apt install -y python3 python3-venv python3-pip nginx ufw

$SUDO install -m 644 "$APP_DIR/deploy/nginx/fileflow.conf" /etc/nginx/sites-available/fileflow
$SUDO ln -sfn /etc/nginx/sites-available/fileflow /etc/nginx/sites-enabled/fileflow
$SUDO rm -f /etc/nginx/sites-enabled/default
$SUDO nginx -t
$SUDO systemctl enable nginx
$SUDO systemctl reload nginx

$SUDO ufw allow OpenSSH
$SUDO ufw allow 'Nginx Full'
$SUDO ufw --force enable

"$APP_DIR/deploy/deploy.sh"

echo "Production setup complete"