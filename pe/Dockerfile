# syntax=docker/dockerfile:1
FROM python:3.10-slim

# Bring in uv from the official distroless image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies first (cached layer) using only the lockfile.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then copy the app and finish the sync.
COPY . .
RUN uv sync --frozen --no-dev
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

# Entrypoint migrates the schema before starting the API; CMD is what it execs.
# --forwarded-allow-ips=* trusts nginx's X-Forwarded-Proto/For so the app builds
# https (not http) redirect URLs behind the reverse proxy — matters for the
# admin login redirect and any absolute URL the app generates.
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips", "*"]
