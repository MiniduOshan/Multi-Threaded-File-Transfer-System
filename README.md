# FileFlow - Multi-Threaded Secure File Transfer System

FileFlow is a Flask + socket based file transfer app with encrypted-at-rest storage.
It provides a web dashboard for upload/download/delete and a multi-threaded TCP server for concurrent file operations.

## Overview

The system has two layers:

1. Flask web app (`app.py`): UI and HTTP endpoints.
2. Socket server (`server.py`): receives upload/download commands and processes clients concurrently.

Uploaded files are encrypted using Fernet before being saved in `uploads/`.
Downloaded files are decrypted before being sent back to clients.

## Current Functionality

1. Concurrent client handling with `ThreadPoolExecutor(max_workers=10)`.
2. Encrypted storage using `cryptography.fernet`.
3. Drag-and-drop upload UI with progress.
4. Download and delete from dashboard.
5. Live file list refresh and `/stats` endpoint.
6. Auto-generated `secret.key` on first run if missing.
7. Safer filename handling via `secure_filename`.
8. Newline-delimited socket protocol with explicit `OK/ERROR` responses.

## Architecture

```
[ Browser ]
    |
    | HTTP
    v
[ Flask App: app.py ]
    |
    | TCP commands (UPLOAD/DOWNLOAD)
    v
[ Socket Server: server.py ] --(ThreadPoolExecutor)--> [handle_client threads]
    |
    v
[ encrypted files in uploads/ ]
```

## Project Structure

```
Multi-Threaded-File-Transfer-System/
|-- app.py
|-- server.py
|-- encryption.py
|-- client.py
|-- run.py
|-- templates/
|   |-- index.html
|   `-- partials/file_list.html
|-- static/css/style.css
|-- uploads/
|-- logs/
|-- .gitignore
`-- README.md
```

## Requirements

- Python 3.10+
- Packages:
  - flask
  - cryptography
    - gunicorn (production)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the App

Start one process:

```bash
python app.py
```

Then open:

```
http://127.0.0.1:5000
```

Notes:

1. `app.py` starts Flask and also starts the socket server thread automatically (reloader-safe).
2. You usually do not need to run `server.py` separately unless you want socket-only mode.

## Optional Start Modes

1. Integrated mode (recommended): `python app.py`
2. Socket-only backend: `python server.py`
3. Helper launcher: `python run.py`

## Production Deployment (DigitalOcean)

The repository includes production-ready deployment files for:

1. `gunicorn` web service (`fileflow-web.service`)
2. socket server service (`fileflow-socket.service`)
3. nginx reverse proxy (`deploy/nginx/fileflow.conf`)
4. GitHub Actions deploy script (`deploy/deploy.sh`)

### One-Time Server Setup

Clone your repository under `/opt/fileflow` (or any path), then run:

```bash
cd /opt/fileflow/Multi-Threaded-File-Transfer-System
chmod +x deploy/setup-production.sh deploy/deploy.sh
./deploy/setup-production.sh
```

What this does:

1. Installs OS dependencies (`nginx`, `python3-venv`, `ufw`)
2. Installs nginx config for proxying to `127.0.0.1:5000`
3. Creates/updates Python virtualenv and installs `requirements.txt`
4. Installs and restarts `fileflow-socket` and `fileflow-web` systemd services

### Continuous Deployment via GitHub Actions

Workflow file: `.github/workflows/deploy-digitalocean.yml`

Required GitHub repository secrets:

1. `DO_HOST` - droplet public IP
2. `DO_USER` - SSH user (e.g., `root`)
3. `DO_SSH_KEY` - private SSH key (full key content)
4. `DO_PORT` - SSH port (usually `22`)

On every push to `main`, the workflow SSH-es into the droplet and runs:

```bash
cd /opt/fileflow/Multi-Threaded-File-Transfer-System
./deploy/deploy.sh
```

## API Endpoints

1. `GET /` - dashboard UI
2. `GET /stats` - storage used, number of files, status
3. `POST /upload` - upload one file
4. `GET /files` - HTML partial for current file list
5. `GET /download/<filename>` - download file (decrypted)
6. `POST /delete/<filename>` - delete file

## Security Notes

1. Encryption key is stored in `secret.key`.
2. `secret.key` and common key/env artifacts are ignored by `.gitignore`.
3. This project currently has no authentication/authorization layer.

## Functional Verification (Current)

The current implementation has been verified for:

1. Successful upload/download/delete round trip.
2. Concurrent uploads/downloads from multiple clients.
3. Consistent file counting between `/files` and `/stats`.

## Troubleshooting

1. Port in use (`WinError 10048`):
   - Find process: `netstat -ano | findstr :5001`
   - Kill process: `taskkill /PID <PID> /F`
2. Missing dependency:
   - `pip install flask cryptography`
3. If stats do not update:
   - Refresh dashboard and confirm files exist in `uploads/`.

## Roadmap

1. Add authentication (JWT/session-based).
2. Stream encryption/decryption to reduce memory usage for very large files.
3. Add persistent metadata and audit logs.
4. Add production deployment config (Gunicorn/Waitress + reverse proxy).
