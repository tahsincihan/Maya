# Deploying a Discord bot to our Oracle VM

Give this file to an AI assistant (or follow it yourself) to put a new bot on the same VM that already runs Maya and the Imposter bot.

## Fill these in first

| Placeholder | What it is |
| --- | --- |
| `<VM_IP>` | The VM's public IP address (Oracle console → Compute → Instances) |
| `<SSH_KEY>` | Path to the private key on the Mac, e.g. `~/Downloads/ssh-key-2026-10-31.key` |
| `<BOT>` | Short lowercase name for the new bot, e.g. `quizbot`. Used for its folder and service name |
| `<ENTRY>` | The file that starts the bot, e.g. `main.py` or `bot.py` |

## The VM

- Oracle Cloud Always Free, shape **VM.Standard.E2.1.Micro**: 2 vCPUs, **1 GB RAM**, 50 GB disk
- **Ubuntu 22.04**, **Python 3.10**, login user `ubuntu` (has passwordless `sudo`)
- No inbound ports are needed. Discord bots connect out, so leave the firewall alone
- Already running (don't touch these):

| Bot | Folder | Service |
| --- | --- | --- |
| Maya | `~/maya` | `maya` |
| Imposter | `~/imposter` | `imposter` |

## How deployment works

Each bot lives in its own folder on the VM and runs as its own **systemd service**. It starts on boot and restarts 10 seconds after a crash.

Code goes from the Mac to the VM with `rsync` over SSH, not through GitHub. Nothing has to be pushed first, and the `.env` file (the bot token) is copied along with the code.

Every bot repo gets a `deploy/` folder with four files (full contents below):

```
deploy/
  <BOT>.service             systemd service template
  requirements-server.txt   exact package versions to install on the VM
  setup_server.sh           runs ON THE VM: makes the venv, installs packages, (re)starts the service
  push_to_server.sh         runs ON THE MAC: copies the code over, then runs setup_server.sh
```

Deploying the first time and every later update is the same single command, run from the bot's folder on the Mac:

```bash
deploy/push_to_server.sh ubuntu@<VM_IP> <SSH_KEY>
```

It ends with `✅ <BOT> is running on the server.` and prints the last log lines.

## Rules for the AI doing this

1. **Keep the code Python 3.10 compatible**, because that's what the VM has. No `except*`, no `tomllib`, no `typing.Self`, and no other 3.11+ features.
2. **Never edit, restart or stop `maya` or `imposter`**, and never touch `~/maya` or `~/imposter`. Only work inside `~/<BOT>`.
3. **The bot must read its token from `.env`** with python-dotenv. Call `load_dotenv(".env")` with an explicit path.
4. **The `.env` file must exist on the Mac** in the bot's folder before pushing. `push_to_server.sh` copies it over. Never commit it, and never print the token.
5. **Pin package versions** in `deploy/requirements-server.txt` to what works locally. Run `pip freeze` in the bot's local venv to get them.
6. **Files the bot saves at runtime** (JSON databases and the like) go in `DATA_FILES` in `push_to_server.sh`. They're copied once on the first deploy and are never overwritten afterwards. Without this, a redeploy would wipe the live data.
7. **Memory is tight (1 GB total).** A small discord.py bot uses about 50 MB. Don't add heavy dependencies (ML models, headless browsers) without checking `free -m` on the VM.
8. **Stop the bot on the Mac** once it runs on the VM. Two copies with the same token answer every command twice.
9. **The bot doesn't need a web keep-alive server** (Flask and similar). The VM never sleeps.
10. Commit the `deploy/` folder to the bot's repo. Push to GitHub only when the user asks.

## File templates

Replace `<BOT>` and `<ENTRY>` everywhere.

### `deploy/<BOT>.service`

`__USER__` and `__DIR__` stay as they are. `setup_server.sh` fills them in.

```ini
[Unit]
Description=<BOT> Discord bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=__USER__
WorkingDirectory=__DIR__
ExecStart=__DIR__/.venv/bin/python <ENTRY>
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### `deploy/requirements-server.txt`

```text
# The exact versions the bot runs with locally.
discord.py==2.7.1
python-dotenv==1.2.2
```

### `deploy/setup_server.sh`

```bash
#!/usr/bin/env bash
# Runs on the Oracle VM (Ubuntu), inside the bot's folder. push_to_server.sh calls it for you.
# Installs Python packages, then installs and (re)starts the bot as a background service.
set -euo pipefail
SERVICE="<BOT>"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

if [ ! -f .env ]; then
  echo "Missing $APP_DIR/.env (needs the bot token)." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  if ! python3 -m venv --help >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-venv python3-pip git
  fi
  python3 -m venv .venv || { sudo apt-get install -y python3-venv && python3 -m venv .venv; }
  .venv/bin/pip install -q --upgrade pip
fi
.venv/bin/pip install -q -r deploy/requirements-server.txt

sed -e "s|__USER__|$(whoami)|" -e "s|__DIR__|$APP_DIR|g" "deploy/$SERVICE.service" \
  | sudo tee "/etc/systemd/system/$SERVICE.service" >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE" >/dev/null 2>&1
sudo systemctl restart "$SERVICE"

sleep 8
sudo journalctl -u "$SERVICE" -n 15 --no-pager
if systemctl is-active --quiet "$SERVICE"; then
  echo "✅ $SERVICE is running on the server."
else
  echo "❌ $SERVICE didn't start. Logs are above." >&2
  exit 1
fi
```

### `deploy/push_to_server.sh`

```bash
#!/usr/bin/env bash
# Run on the Mac: copies the bot to the Oracle VM and (re)starts it there.
# Usage: deploy/push_to_server.sh ubuntu@<vm-ip> [path/to/ssh-key]
# Run it again any time the code changes.
set -euo pipefail
HOST="${1:?Usage: deploy/push_to_server.sh ubuntu@<vm-ip> [path/to/ssh-key]}"
KEY="${2:-}"
REMOTE_DIR="<BOT>"
# Files the bot saves at runtime. Copied the first time only; never overwritten after that.
DATA_FILES=()

SSH="ssh -o StrictHostKeyChecking=accept-new"
[ -n "$KEY" ] && SSH="$SSH -i $KEY"
cd "$(dirname "$0")/.."

EXCLUDES=(--exclude .git --exclude .venv --exclude venv --exclude __pycache__ --exclude .claude
          --exclude '*.log' --exclude .DS_Store)
for f in "${DATA_FILES[@]+"${DATA_FILES[@]}"}"; do EXCLUDES+=(--exclude "$f"); done
rsync -az --delete -e "$SSH" "${EXCLUDES[@]}" ./ "$HOST:$REMOTE_DIR/"

EXISTING=()
for f in "${DATA_FILES[@]+"${DATA_FILES[@]}"}"; do [ -f "$f" ] && EXISTING+=("$f"); done
if [ ${#EXISTING[@]} -gt 0 ]; then
  rsync -az --ignore-existing -e "$SSH" "${EXISTING[@]}" "$HOST:$REMOTE_DIR/"
fi

$SSH "$HOST" "bash $REMOTE_DIR/deploy/setup_server.sh"
```

After creating the scripts, run `chmod +x deploy/*.sh`.

## Steps, start to finish

1. In the bot's folder on the Mac, check that it runs locally and that `.env` has the token.
2. Create the four `deploy/` files above. Fill in `<BOT>` and `<ENTRY>`, pin the requirements, and list any data files.
3. Run `bash -n deploy/*.sh` to syntax-check the scripts.
4. Stop the bot if it's running on the Mac.
5. Run `deploy/push_to_server.sh ubuntu@<VM_IP> <SSH_KEY>`.
6. Check for `✅` and a successful login line in the printed log, then try a command in Discord.
7. Commit the `deploy/` folder.

## Day-to-day commands

From the Mac:

| What | Command |
| --- | --- |
| Deploy an update | `deploy/push_to_server.sh ubuntu@<VM_IP> <SSH_KEY>` |
| Live logs | `ssh -i <SSH_KEY> ubuntu@<VM_IP> "sudo journalctl -u <BOT> -f"` |
| Status of all bots | `ssh -i <SSH_KEY> ubuntu@<VM_IP> "systemctl status maya imposter <BOT> --no-pager"` |
| Restart | `ssh -i <SSH_KEY> ubuntu@<VM_IP> "sudo systemctl restart <BOT>"` |
| Memory left | `ssh -i <SSH_KEY> ubuntu@<VM_IP> "free -m"` |
| Back up data files | `scp -i <SSH_KEY> "ubuntu@<VM_IP>:<BOT>/*.json" backups/` |

## Removing a bot

```bash
ssh -i <SSH_KEY> ubuntu@<VM_IP> "sudo systemctl disable --now <BOT> && sudo rm /etc/systemd/system/<BOT>.service && sudo systemctl daemon-reload"
```

Then delete `~/<BOT>` on the VM only after backing up any data files it holds.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Permission denied (publickey)` | Wrong key path, or the key isn't private: `chmod 600 <SSH_KEY>` |
| `Missing .env` | Create `.env` in the bot's folder on the Mac and push again |
| Service keeps restarting | Read `sudo journalctl -u <BOT> -n 50`. Usually a missing package or Python 3.11+ syntax |
| `Improper token` / `401` | Wrong token in `.env`, or it was reset in the Discord Developer Portal |
| Bot online but ignores commands | Turn on **Message Content Intent** (and any others it uses) in the Developer Portal |
| Every command answered twice | The bot is still running on the Mac too. Stop it there |
| `Killed` in the logs / out of memory | Check `free -m`. The VM has 1 GB shared by all bots |
| Oracle stopped the VM | Always Free VMs that stay idle can be reclaimed. Upgrading to Pay As You Go prevents it, and the free resources stay free |
