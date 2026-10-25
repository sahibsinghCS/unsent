# Unsent: one container that serves the API and the built React app on port 7860.
# Built for a free Hugging Face Docker Space (CPU basic, non-root uid 1000); runs anywhere Docker does.
#   docker build -t unsent .
#   docker run --rm -p 7860:7860 -e OPENAI_API_KEY=... unsent

# ---- 1. Build the frontend -------------------------------------------------------------------
FROM node:20-slim AS frontend
WORKDIR /src
# The prebuild step copies the crisis content from content/ into the bundle.
COPY content/ content/
COPY frontend/package.json frontend/package-lock.json frontend/
RUN cd frontend && npm ci --no-audit --no-fund
COPY frontend/ frontend/
RUN cd frontend && npm run build

# ---- 2. Runtime -------------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

RUN pip install --no-cache-dir "uv==0.11.32" \
    && useradd --create-home --uid 1000 user \
    && mkdir /app && chown user:user /app
USER user
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FASTEMBED_CACHE_PATH=/app/.cache/fastembed

# Dependencies first (cached layer): exactly the versions in uv.lock, no dev tools.
COPY --chown=user:user pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Only what the server reads at runtime.
COPY --chown=user:user backend/ backend/
COPY --chown=user:user data/ data/
COPY --chown=user:user content/ content/
COPY --chown=user:user models/ models/
COPY --chown=user:user eval/reports/ eval/reports/
COPY --chown=user:user deploy/predownload.py deploy/predownload.py
COPY --from=frontend --chown=user:user /src/frontend/dist/ frontend/dist/

# Bake the embedding model into the image: fast start, no network needed for it at runtime.
RUN python -m deploy.predownload

ENV FR_ENV=prod \
    FR_EMBED=fastembed \
    FR_TRUST_PROXY=1 \
    HF_HUB_OFFLINE=1 \
    PORT=7860
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:7860/api/health', timeout=4).status == 200 else 1)"

# Exactly one worker: sessions live in this process's memory. No access log: it would print
# session IDs in URLs; the app writes its own text-free request log instead.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1", \
     "--proxy-headers", "--forwarded-allow-ips=*", "--no-access-log", "--no-server-header"]
