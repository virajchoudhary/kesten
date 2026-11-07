FROM python:3.12.16-alpine3.24@sha256:e064671ca452259bab50e8e2c7bd896e39e9a343bb06ca25234adf6fe18d0fc7
ARG SOURCE_DATE_EPOCH
ARG CADRISYN_SOURCE_REVISION=development
LABEL org.opencontainers.image.revision=${CADRISYN_SOURCE_REVISION}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apk add --no-cache postgresql17-client=17.11-r0 && apk add --no-cache --virtual .build-deps build-base linux-headers
COPY backend/requirements-workspace.lock.txt backend/requirements-runtime.txt /app/
RUN python -m pip install --no-cache-dir --no-compile pip==26.3 && python -m pip install --no-cache-dir --no-compile -r requirements-runtime.txt && apk del .build-deps
COPY backend /app/backend
COPY scripts/ops /app/scripts/ops
COPY scripts/migrate_workspace.py /app/scripts/migrate_workspace.py
RUN addgroup -S cadrisyn && adduser -S -G cadrisyn -h /app cadrisyn && mkdir -p /app/static && chown -R cadrisyn:cadrisyn /app
WORKDIR /app/backend
RUN DJANGO_SECRET_KEY=build-only-non-runtime-secret-000000000000000000000000000 DJANGO_DEBUG=true DJANGO_STATIC_ROOT=/app/static python manage.py collectstatic --noinput
USER cadrisyn
EXPOSE 8000
CMD ["gunicorn", "quantvision.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30", "--access-logfile", "-", "--access-logformat", "{\"event\":\"gunicorn_request\",\"method\":\"%(m)s\",\"status\":%(s)s,\"duration_seconds\":%(L)s}", "--error-logfile", "-"]
