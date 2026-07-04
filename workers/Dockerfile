FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY celery_app.py .
COPY config.py .
COPY tasks/ tasks/
COPY utils/ utils/
COPY clients/ clients/

RUN pip install --no-cache-dir -e "."

CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]