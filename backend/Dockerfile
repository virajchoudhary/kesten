FROM python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client openssl libssl3t64 && rm -rf /var/lib/apt/lists/*
COPY backend/requirements-workspace.lock.txt backend/requirements-runtime.txt /app/
RUN python -m pip install --no-cache-dir pip==26.3 && python -m pip install --no-cache-dir -r requirements-runtime.txt
COPY backend /app/backend
COPY scripts/ops /app/scripts/ops
COPY scripts/migrate_workspace.py /app/scripts/migrate_workspace.py
RUN groupadd --system cadrisyn && useradd --system --gid cadrisyn --home-dir /app cadrisyn && mkdir -p /app/static && chown -R cadrisyn:cadrisyn /app
WORKDIR /app/backend
RUN DJANGO_SECRET_KEY=build-only-non-runtime-secret-000000000000000000000000000 DJANGO_DEBUG=true DJANGO_STATIC_ROOT=/app/static python manage.py collectstatic --noinput
USER cadrisyn
EXPOSE 8000
CMD ["gunicorn", "quantvision.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30", "--access-logfile", "-", "--access-logformat", "{\"event\":\"gunicorn_request\",\"method\":\"%(m)s\",\"status\":%(s)s,\"duration_seconds\":%(L)s}", "--error-logfile", "-"]
