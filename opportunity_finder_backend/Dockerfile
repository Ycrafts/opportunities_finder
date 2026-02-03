FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir whitenoise

RUN pip install --no-cache-dir gunicorn

COPY . ./

ENV DJANGO_SETTINGS_MODULE=opportunity_finder.settings

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "opportunity_finder.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "120"]
