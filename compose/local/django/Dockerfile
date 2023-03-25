ARG PYTHON_VERSION=3.11-slim

# define an alias for the specfic python version used in this file.
FROM python:${PYTHON_VERSION} as python

# Python build stage
FROM python as python-build-stage

ARG BUILD_ENVIRONMENT=local


# Python 'run' stage
FROM python as python-run-stage

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV DRAWIO_VERSION 15.7.3
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev gettext libmagic-dev libjpeg-dev zlib1g-dev && \
    # Dependencies for file preview generation
    # apt-get install -y poppler-utils libfile-mimeinfo-perl libimage-exiftool-perl ghostscript libsecret-1-0 zlib1g-dev libjpeg-dev imagemagick libmagic1 webp libreoffice inkscape ffmpeg xvfb && \
    apt-get purge -y --auto-remove -o APT:AutoRemove:RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
# Dependencies for file preview generation
# RUN curl -LO https://github.com/jgraph/drawio-desktop/releases/download/v${DRAWIO_VERSION}/drawio-x86_64-${DRAWIO_VERSION}.AppImage && mv drawio-x86_64-${DRAWIO_VERSION}.AppImage /usr/local/bin/drawio
ENV PATH="/root/.local/bin:$PATH"

RUN poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock /app/
RUN poetry install --no-root --only main
RUN preview --check-dependencies


COPY ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start


COPY ./compose/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./compose/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./compose/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower


# copy application code to WORKDIR
COPY . ${APP_HOME}

ENTRYPOINT ["/entrypoint"]
