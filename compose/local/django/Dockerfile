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
ENV POETRY_VERSION 1.4.2

WORKDIR ${APP_HOME}

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev gettext libmagic-dev libjpeg-dev zlib1g-dev  && \
    # Dependencies for file preview generation
    apt-get install -y webp libimage-exiftool-perl libmagickwand-dev ffmpeg libgdal-dev && \
    # ML dependencies \
    # none for now
    apt-get purge -y --auto-remove -o APT:AutoRemove:RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv

COPY pyproject.toml poetry.lock /app/
RUN poetry export --without-hashes -f requirements.txt | /venv/bin/pip install -r /dev/stdin
RUN python -m nltk.downloader punkt stopwords wordnet

COPY . .
RUN poetry build && /venv/bin/pip install dist/*.whl


COPY ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY ./compose/local/django/spacy_setup /spacy_setup
RUN sed -i 's/\r$//g' /spacy_setup
RUN chmod +x /spacy_setup

COPY ./compose/local/django/start-redirect /start-redirect
RUN sed -i 's/\r$//g' /start-redirect
RUN chmod +x /start-redirect

COPY ./compose/local/django/install_preview_dependencies /install_preview_dependencies
RUN sed -i 's/\r$//g' /install_preview_dependencies
RUN chmod +x /install_preview_dependencies

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
