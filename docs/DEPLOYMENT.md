# F-Build Deployment Guide

## 1. What is shipped

This repository contains:

- `frontend`: Flutter Web dashboard
- `backend`: FastAPI API, queue worker, log API, Pgyer upload integration
- `compose.yaml`: container entry for the dashboard/API stack

## 2. Important platform limitation

The project targets a macOS build machine and needs:

- `git`
- `fvm`
- `flutter`
- `pod`
- iOS signing / Xcode toolchain

Those tools are macOS-specific for iOS builds. A Linux Docker container cannot
run Xcode or produce iOS `.ipa` files.

That means:

- `frontend` can be containerized safely
- the current `backend` image is suitable for the API/service layer
- **real iOS build execution must run on the macOS host environment**

If you deploy this project exactly as `docker compose up -d`, the UI and API
will start, but iOS build commands inside the Linux backend container will not
have access to Xcode.

## 3. Recommended production layout

For a real iMac build station, use this split:

1. Run `frontend` in Docker
2. Run `backend` on the macOS host with host-installed `git/fvm/flutter/pod`
3. Keep `workspaces/`, `artifacts/`, `logs/`, `data/` on the host filesystem

If you only want to demo the UI/API layer, Docker Compose alone is enough.

## 4. Environment variables

Create a local `.env` file from `.env.example`.

Supported keys:

- `PGYER_API_KEY`: real Pgyer API key
- `PGYER_INSTALL_TYPE`: default `1`
- `WORKER_POLL_SECONDS`: queue polling interval, default `2`
- `CLEANUP_POLL_SECONDS`: cleanup polling interval, default `3600`
- `ARTIFACT_RETENTION_HOURS`: default `24`
- `WORKSPACE_BUILD_RETENTION_HOURS`: default `168`

Example:

```env
PGYER_API_KEY=your_pgyer_api_key_here
PGYER_INSTALL_TYPE=1
WORKER_POLL_SECONDS=2
CLEANUP_POLL_SECONDS=3600
ARTIFACT_RETENTION_HOURS=24
WORKSPACE_BUILD_RETENTION_HOURS=168
```

## 5. Demo deployment with Docker Compose

This mode is suitable for:

- UI development
- API verification
- queue/status/log polling checks
- non-iOS demonstration

Commands:

```bash
cd /Users/dddd/Work/flutter_distro
cp .env.example .env
docker compose build
docker compose up -d
```

Open:

- dashboard: `http://localhost:3000`
- backend API: `http://localhost:8000/api/health`

Stop:

```bash
docker compose down
```

## 6. Real macOS build-machine deployment

### 6.1 Backend on host

```bash
cd /Users/dddd/Work/flutter_distro/backend
cp /Users/dddd/Work/flutter_distro/.env.example /Users/dddd/Work/flutter_distro/.env
uv sync --group dev
uv run uvicorn fbuild_backend.main:app --host 0.0.0.0 --port 8000
```

Because `backend/src/fbuild_backend/config.py` reads `.env`, the backend will
pick up the same `PGYER_API_KEY` and cleanup settings.

### 6.2 Frontend in Docker

```bash
cd /Users/dddd/Work/flutter_distro
docker compose up -d frontend
```

If the frontend needs to call the host backend instead of the backend
container, build it with a custom API base URL:

```bash
cd /Users/dddd/Work/flutter_distro/frontend
fvm flutter build web --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

Then serve `frontend/build/web` with Nginx or another static server.

## 7. Runtime directories

The system writes data to:

- `/Users/dddd/Work/flutter_distro/data`
- `/Users/dddd/Work/flutter_distro/logs`
- `/Users/dddd/Work/flutter_distro/artifacts`
- `/Users/dddd/Work/flutter_distro/workspaces`

Meaning:

- `data`: SQLite database
- `logs`: reserved runtime logs directory
- `artifacts`: archived build outputs copied out of each workspace
- `workspaces`: checked out Flutter repositories

## 8. Cleanup policy

The backend now performs automatic cleanup:

- files under `artifacts/` older than `24` hours are deleted
- each managed workspace `build/` directory older than `168` hours is deleted

Tune with:

- `ARTIFACT_RETENTION_HOURS`
- `WORKSPACE_BUILD_RETENTION_HOURS`
- `CLEANUP_POLL_SECONDS`

## 9. Smoke test after deployment

Use this checklist:

1. Open the dashboard
2. Add a Git repository
3. Click `同步项目`
4. Confirm remote branches appear
5. Click `发起 Android` or `发起 iOS`
6. Confirm the task appears under `最近构建`
7. Open task detail and confirm logs are growing
8. Confirm the final `Pgyer` field is populated

## 10. Current status of the product

Implemented:

- multi-project repository registration
- remote branch sync
- queue-based build submission
- single background worker
- polling logs
- recent build history
- real Pgyer upload integration
- artifact archiving and cleanup

Not yet hardened for production:

- authentication
- cancel/retry actions
- richer project-level build configuration
- host-agent mode for full Docker-orchestrated macOS build execution
