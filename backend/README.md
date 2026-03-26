# Backend

The backend service is built with FastAPI and managed by `uv`.

Planned responsibilities:

- Project registration and branch sync
- Build queue coordination
- Build execution and log persistence
- Pgyer upload integration

Development commands will follow this pattern:

```bash
cd backend
uv run uvicorn fbuild_backend.main:app --reload

Deployment is expected to run through Docker, with `uv` managing Python package
resolution inside the backend image.
```
