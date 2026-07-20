# Personal website

Wagtail 7 / Django 5.2 personal site: portfolio, CV/resume, blog, and a
contact form.

## Local development

Requires Docker.

```bash
cp .env.example .env          # edit SECRET_KEY etc. if you like
docker compose up -d          # starts postgres, mailhog, and the web app
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Site: http://localhost:8000
Admin: http://localhost:8000/admin/
Mailhog (catches contact-form emails in dev): http://localhost:8025

Code changes on the host are picked up live (the `web` service bind-mounts
the repo and runs `manage.py runserver`).

### Running without Docker

Dependencies are managed with [uv](https://docs.astral.sh/uv/) via
`pyproject.toml` / `uv.lock` (no `requirements.txt`).

```bash
uv sync                      # installs prod + dev deps into .venv
uv run python manage.py migrate
uv run python manage.py runserver
```

`uv add <package>` / `uv remove <package>` to change dependencies —
commit the updated `uv.lock`.

## Tests and linting

```bash
docker compose exec web python manage.py test
docker compose exec web ruff check .
docker compose exec web ruff format .
```

## Content structure

- **Home** — StreamField sections (hero, featured projects, latest posts, CTA).
- **About** — bio, work experience / education / certificates / skills
  (all editable inline), optional downloadable resume PDF.
- **Projects** — index + detail pages, tech-stack tags, gallery, StreamField
  body (headings, rich text, images, quotes, embeds, syntax-highlighted
  code blocks).
- **Blog** — index (with tag/category filtering + pagination) + posts, same
  StreamField body as projects.
- **Contact** — Wagtail form builder page with email notification and a
  honeypot spam trap.
- **Settings → Site settings** — footer text, contact email, social links.

All content is edited through the Wagtail admin; nothing above needs a code
change to update.

## Deployment

Two deployment paths are set up, sharing the same `Dockerfile`
(gunicorn, WhiteNoise-served static files, `collectstatic` at build time):

### Self-hosted VM (`docker-compose.prod.yml`) — recommended for this project

Runs everything on a single VM you control: Postgres as a container with a
persistent volume, uploaded media (images/documents) on a persistent local
volume (no S3/object storage involved), and [Caddy](https://caddyserver.com/)
as a reverse proxy handling automatic HTTPS via Let's Encrypt.

```bash
# on the VM, with Docker + the Compose plugin installed
git clone <this repo> && cd website
cp .env.prod.example .env.prod   # fill in real values - see comments inline
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod exec web python manage.py createsuperuser
```

Before starting, point `DOMAIN`'s DNS A/AAAA record at the VM's public IP —
Caddy needs that to issue a certificate. Migrations run automatically on
container start (see the `CMD` in `Dockerfile`); for a single-VM deployment
like this, that's simpler than a separate release step and there's no
concurrent-deploy race to worry about.

To update: `git pull`, then
`docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build`.

To back up: `docker compose -f docker-compose.prod.yml --env-file .env.prod exec db pg_dump -U <POSTGRES_USER> <POSTGRES_DB> > backup.sql`
(and separately back up the `media_data` volume).

### PaaS (Render, Fly.io, Railway, ...)

The plain `Dockerfile` (runtime stage) also works standalone against a
managed Postgres add-on. Since most PaaS containers are ephemeral, set
`AWS_STORAGE_BUCKET_NAME` (+ related `AWS_S3_*` vars in
`website/settings/production.py`) to use S3-compatible object storage for
media instead of the local filesystem. Run migrations via the platform's
release/pre-deploy hook rather than at container startup in this case.

### Common to both

Required environment variables (see `.env.example` / `.env.prod.example`):
`SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`,
`WAGTAILADMIN_BASE_URL`, `EMAIL_URL`, `DEFAULT_FROM_EMAIL`.

After first deploy, set the real domain on the site in
**Settings → Sites** in the Wagtail admin (the initial migration points it
at `localhost`).
