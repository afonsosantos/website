
# This stage installs build dependencies and compiles Python packages.
# It will be discarded in the final image, keeping only the compiled packages.
FROM python:3.14-slim-bookworm AS builder

# Install system packages required to build Python packages.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

# Pin uv itself for reproducible builds.
COPY --from=ghcr.io/astral-sh/uv:0.9.17 /uv /usr/local/bin/uv

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install dependencies from the lockfile only (no source yet), so this
# layer is cached unless pyproject.toml/uv.lock change. Production deps only.
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-install-project --no-dev


# RUNTIME STAGE
# Use an official Python runtime based on Debian 12 "bookworm" as a parent image.
FROM python:3.14-slim-bookworm AS runtime

# Install runtime system packages required by Wagtail and Django.
# These are the runtime libraries needed by the compiled Python packages.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    libpq5 \
    libmariadb3 \
    libjpeg62-turbo \
    libwebp7 \
 && rm -rf /var/lib/apt/lists/*

# Add user that will be used in the container. `--create-home` gives it a
# writable $HOME - gunicorn 25+ wants one for its control socket, and
# without it logs a (harmless but noisy) permission error on every boot.
RUN useradd --create-home wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000

# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
# 2. Set PORT variable that is used by Gunicorn. This should match "EXPOSE"
#    command.
# 3. Add the virtual environment to PATH.
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=website.settings.production

# Copy the virtual environment from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Use /app folder as a directory where the source code is stored.
WORKDIR /app

# Set this directory to be owned by the "wagtail" user, so media files
# written to a mounted volume (when not using object storage) are writable.
RUN chown wagtail:wagtail /app

# Copy the source code of the project into the container.
COPY --chown=wagtail:wagtail . .

# Pre-create /app/media with the right ownership. When docker-compose mounts
# an empty named volume here, Docker seeds it from the image's existing
# directory - including ownership - so uploads stay writable by "wagtail"
# without a separate entrypoint/chown step.
RUN mkdir -p /app/media && chown wagtail:wagtail /app/media

# Use user "wagtail" to run the build commands below and the server itself.
USER wagtail

# Collect static files. Real secrets aren't available at build time (they're
# injected by the hosting platform at runtime and override these), but
# collectstatic needs settings.production to import cleanly, so provide
# throwaway values sufficient for that.
RUN SECRET_KEY=collectstatic-build-time-only \
    ALLOWED_HOSTS=localhost \
    DATABASE_URL=sqlite:///build-time-only.sqlite3 \
    WAGTAILADMIN_BASE_URL=http://localhost \
    EMAIL_URL=consolemail:// \
    DEFAULT_FROM_EMAIL=webmaster@localhost \
    python manage.py collectstatic --noinput --clear

# Runtime command that executes when "docker run" is called, it does the
# following:
#   1. Migrate the database.
#   2. Start the application server.
# WARNING:
#   Migrating database at the same time as starting the server IS NOT THE BEST
#   PRACTICE. The database should be migrated manually or using the release
#   phase facilities of your hosting platform. This is used only so the
#   Wagtail instance can be started with a simple "docker run" command.
#
# Without --workers, gunicorn defaults to a single sync worker - every
# request (including the Wagtail admin's own autosave, which fires on a
# 500ms debounce while editing, and its live-preview re-render) is handled
# one at a time, so they queue up behind each other instead of running
# concurrently. gthread workers share memory across their threads (unlike
# separate sync worker processes), which matters on a small VM: 2 workers
# x 4 threads gives real concurrency for these I/O-bound admin requests
# without multiplying the app's memory footprint by 8.
CMD set -xe; python manage.py migrate --noinput; gunicorn website.wsgi:application --workers 2 --threads 4 --worker-class gthread
