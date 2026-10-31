#!/usr/bin/env bash
# Run on your Mac: copies Maya to the Oracle VM and (re)starts her there.
# Usage: deploy/push_to_server.sh ubuntu@<vm-ip> [path/to/ssh-key]
# Run it again any time you change the code.
set -euo pipefail
HOST="${1:?Usage: deploy/push_to_server.sh ubuntu@<vm-ip> [path/to/ssh-key]}"
KEY="${2:-}"
REMOTE_DIR="maya"
DATA_FILES=(league.json flirt.json predictions.json pl_predictions.json)

SSH="ssh -o StrictHostKeyChecking=accept-new"
[ -n "$KEY" ] && SSH="$SSH -i $KEY"
cd "$(dirname "$0")/.."

# Code and .env. The server's saved data (couples, confessions, league, picks) is never overwritten.
EXCLUDES=(--exclude .git --exclude .venv --exclude __pycache__ --exclude '*.log' --exclude .DS_Store)
for f in "${DATA_FILES[@]}"; do EXCLUDES+=(--exclude "$f"); done
rsync -az --delete -e "$SSH" "${EXCLUDES[@]}" ./ "$HOST:$REMOTE_DIR/"

# First time only: bring over the data saved on this Mac.
EXISTING=()
for f in "${DATA_FILES[@]}"; do [ -f "$f" ] && EXISTING+=("$f"); done
if [ ${#EXISTING[@]} -gt 0 ]; then
  rsync -az --ignore-existing -e "$SSH" "${EXISTING[@]}" "$HOST:$REMOTE_DIR/"
fi

$SSH "$HOST" "bash $REMOTE_DIR/deploy/setup_server.sh"
