FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt
COPY backend/app ./app
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
USER app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
