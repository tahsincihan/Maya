#!/usr/bin/env bash
# Runs on the Oracle VM (Ubuntu), inside Maya's folder. push_to_server.sh calls it for you.
# Installs Python packages, then installs and (re)starts Maya as a background service.
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

if [ ! -f .env ]; then
  echo "Missing $APP_DIR/.env (needs DISCORD_BOT_TOKEN)." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  echo "First run: installing Python..."
  sudo apt-get update -y
  sudo apt-get install -y python3 python3-venv python3-pip git
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
fi
.venv/bin/pip install -q -r deploy/requirements-server.txt

sed -e "s|__USER__|$(whoami)|" -e "s|__DIR__|$APP_DIR|g" deploy/maya.service \
  | sudo tee /etc/systemd/system/maya.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable maya >/dev/null 2>&1
sudo systemctl restart maya

sleep 8
sudo journalctl -u maya -n 15 --no-pager
if systemctl is-active --quiet maya; then
  echo "✅ Maya is running on the server."
else
  echo "❌ Maya didn't start. Logs are above." >&2
  exit 1
fi
