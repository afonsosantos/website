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

## Tests and linting

```bash
docker compose exec web python manage.py test
docker compose exec web ruff check .
docker compose exec web ruff format .
```

## Content structure

- **Home** — StreamField sections (hero, featured projects, latest posts, CTA).
- **About** — bio, work experience / education / skills (editable inline),
  optional downloadable resume PDF.
- **Projects** — index + detail pages, tech-stack tags, gallery.
- **Blog** — index (with tag/category filtering + pagination) + posts.
- **Contact** — Wagtail form builder page with email notification and a
  honeypot spam trap.
- **Settings → Site settings** — footer text, contact email, social links.

All content is edited through the Wagtail admin; nothing above needs a code
change to update.

## Deployment

The `Dockerfile` builds a production image (gunicorn, WhiteNoise-served
static files, `collectstatic` at build time). Required environment
variables in production (see `.env.example`):

- `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` (Postgres)
- `WAGTAILADMIN_BASE_URL`
- `EMAIL_URL`, `DEFAULT_FROM_EMAIL`
- `AWS_STORAGE_BUCKET_NAME` (+ related `AWS_S3_*` vars) if using S3-compatible
  object storage for media — recommended, since most PaaS containers are
  ephemeral and would otherwise lose uploaded images/documents on redeploy.

Run migrations via your platform's release/pre-deploy hook rather than at
container startup (see the comment in `Dockerfile`).

After first deploy, set the real domain on the site in
**Settings → Sites** in the Wagtail admin (the initial migration points it
at `localhost`).
