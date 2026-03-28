# FileFlow

Secure file transfer system for production use.

FileFlow gives you a clean web dashboard to upload, download, and delete files while keeping stored files encrypted.

## What You Get

1. Public web access through Nginx.
2. Fast Flask web app served by Gunicorn.
3. Dedicated socket backend for file operations.
4. Encrypted-at-rest files in the uploads folder.
5. Ready-to-use DigitalOcean deployment scripts.

## Live Production Flow

```text
Browser -> Nginx (80) -> Gunicorn (127.0.0.1:5000) -> Flask
                                          |
                                          -> Socket server (127.0.0.1:5001)
```

## One-Time Setup (DigitalOcean)

Run this once on your droplet:

```bash
cd /opt/fileflow/Multi-Threaded-File-Transfer-System
chmod +x deploy/setup-production.sh deploy/deploy.sh
./deploy/setup-production.sh
```

This command set will:

1. Install required packages (`nginx`, Python runtime, `ufw`).
2. Configure Nginx reverse proxy.
3. Create/update Python virtual environment and install dependencies.
4. Install and start production services.

## Daily Deploy (After Code Changes)

When you push new code and want to deploy on the server:

```bash
cd /opt/fileflow/Multi-Threaded-File-Transfer-System
./deploy/deploy.sh
```

## Service Status Commands

```bash
sudo systemctl status fileflow-socket --no-pager -l
sudo systemctl status fileflow-web --no-pager -l
sudo systemctl status nginx --no-pager -l
```

## Quick Health Checks

```bash
curl -I http://127.0.0.1:5000
curl http://127.0.0.1:5000/stats
curl -I http://YOUR_DROPLET_PUBLIC_IP
curl http://YOUR_DROPLET_PUBLIC_IP/stats
```

## GitHub Auto Deploy (Optional)

Workflow is already included in `.github/workflows/deploy-digitalocean.yml`.

Set these GitHub repo secrets:

1. `DO_HOST` = droplet public IP
2. `DO_USER` = SSH user (usually `root`)
3. `DO_SSH_KEY` = private SSH key content
4. `DO_PORT` = `22` (unless changed)

After that, every push to `main` can deploy automatically.

## Main Endpoints

1. `/` dashboard
2. `/stats` system stats
3. `/upload` upload file
4. `/files` file list partial
5. `/download/<filename>` download file
6. `/delete/<filename>` delete file

## Troubleshooting

1. View logs:

```bash
sudo journalctl -u fileflow-web -n 100 --no-pager
sudo journalctl -u fileflow-socket -n 100 --no-pager
sudo journalctl -u nginx -n 100 --no-pager
```

2. Restart all services:

```bash
sudo systemctl restart fileflow-socket fileflow-web nginx
```

3. If public URL fails, verify firewall:

```bash
sudo ufw status
```

## Security Notes

1. Files are encrypted before storage.
2. `secret.key` is local secret material and should not be committed.
3. Gunicorn listens on localhost only; Nginx is the public entrypoint.
