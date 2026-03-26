# F-Build

F-Build is a local Flutter build orchestration system for macOS build machines.
It provides:

- Multi-project Git repository management
- Single-worker queued Android/iOS builds
- Polling-based build status and log viewing
- Pgyer upload integration
- Docker-based deployment

Planned structure:

- `backend/`: FastAPI service managed by `uv`
- `frontend/`: Flutter Web dashboard
- `workspaces/`: checked-out Flutter project workspaces
- `artifacts/`: temporary local build outputs
- `logs/`: task logs
- `data/`: SQLite and runtime state

The repository is being built incrementally through small PR-sized features.

Current deployment direction:

- Local development: `uv` for the backend, Flutter tooling for the web app
- Runtime deployment: Docker containers

Deployment documentation:

- `docs/DEPLOYMENT.md`
