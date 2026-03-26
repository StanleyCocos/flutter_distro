FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    DATA_DIR=/runtime/data \
    LOGS_DIR=/runtime/logs \
    ARTIFACTS_DIR=/runtime/artifacts \
    WORKSPACES_DIR=/runtime/workspaces

COPY pyproject.toml README.md ./
COPY src ./src

RUN uv pip install --system .

EXPOSE 8000

CMD ["uvicorn", "fbuild_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

