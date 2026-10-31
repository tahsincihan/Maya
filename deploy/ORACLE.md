# Hosting Maya on an Oracle Cloud Always Free VM

Maya runs as a background service on the VM. She starts on boot, restarts herself if she crashes, and keeps her saved data (couples, confessions, league table, predictions) on the VM's disk.

## 1. Create the VM (once)

1. Sign up at [oracle.com/cloud/free](https://www.oracle.com/cloud/free/). Oracle asks for a card to verify you but doesn't charge for Always Free resources. Your **home region** can't be changed later, so pick one near you.
2. In the console go to **Compute → Instances → Create instance**.
3. **Image**: Canonical **Ubuntu 24.04**.
4. **Shape**: **Ampere VM.Standard.A1.Flex** with 1 OCPU and 6 GB memory (plenty for Maya). If it says "out of capacity", use **VM.Standard.E2.1.Micro** instead, which is also free.
5. **Networking**: leave the defaults and make sure **Assign a public IPv4 address** is on.
6. **SSH keys**: choose **Generate a key pair for me** and download the private key (or upload your own public key).
7. Click **Create**. When it's running, copy the **Public IP address**.

No ports need opening. Maya connects out to Discord.

## 2. Connect from your Mac

```bash
chmod 600 ~/Downloads/ssh-key-*.key
```

```bash
ssh -i ~/Downloads/ssh-key-*.key ubuntu@YOUR_VM_IP
```

If you get a prompt on the VM, it works. Type `exit` to come back.

## 3. Move Maya over

1. Stop Maya on your Mac first (Ctrl+C in her terminal). If she runs in two places, every command gets answered twice.
2. From the project folder on your Mac:

```bash
deploy/push_to_server.sh ubuntu@YOUR_VM_IP ~/Downloads/ssh-key-YOUR-KEY.key
```

This copies the code and your `.env` to `~/maya` on the VM, copies your saved data the first time, installs everything and starts Maya. It ends with ✅ when she's online.

## Updating Maya

After changing code on your Mac, run the same `push_to_server.sh` command again. It only replaces code. Data saved on the server is never overwritten by the copies on your Mac.

## Useful commands (on the VM)

| What | Command |
| --- | --- |
| Live logs | `sudo journalctl -u maya -f` |
| Status | `systemctl status maya` |
| Restart | `sudo systemctl restart maya` |
| Stop | `sudo systemctl stop maya` |

## Backing up the data

From your Mac:

```bash
mkdir -p backups && scp -i ~/Downloads/ssh-key-YOUR-KEY.key "ubuntu@YOUR_VM_IP:maya/*.json" backups/
```

## Caveat: idle reclaim

Oracle may reclaim Always Free VMs that stay almost idle for 7 days, and a Discord bot uses very little CPU. To avoid this, upgrade the account to **Pay As You Go** (Billing → Upgrade). Always Free resources stay free after the upgrade, and the idle rule no longer applies.
