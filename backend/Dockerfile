FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements-workspace.lock.txt backend/requirements-runtime.txt /app/
RUN pip install --no-cache-dir -r requirements-runtime.txt
COPY backend /app/backend
RUN groupadd --system cadrisyn && useradd --system --gid cadrisyn --home-dir /app cadrisyn && mkdir -p /app/static && chown -R cadrisyn:cadrisyn /app
WORKDIR /app/backend
USER cadrisyn
EXPOSE 8000
CMD ["gunicorn", "quantvision.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30", "--access-logfile", "-", "--error-logfile", "-"]
