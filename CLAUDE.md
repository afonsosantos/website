# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal website (portfolio / CV / blog / contact form) built on Wagtail 7 + Django 5.2. All content is edited through the Wagtail admin at `/admin/` — page models exist so that Home, About, Projects, and Blog content can be changed without touching code.

## Commands

All commands run inside the `web` container unless noted. The `web` service bind-mounts the repo and runs `manage.py runserver`, so host-side edits take effect immediately.

```bash
# start the stack (postgres, mailhog, web)
docker compose up -d

# migrations / superuser
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

# after changing any model (including StreamField block definitions in
# base/blocks.py — Wagtail migrations track those too)
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# tests — full suite or a single app/test
docker compose exec web python manage.py test
docker compose exec web python manage.py test blog
docker compose exec web python manage.py test contact.tests.ContactPageSubmissionTests.test_valid_submission_creates_record_and_sends_email

# lint / format
docker compose exec web ruff check .
docker compose exec web ruff format .
```

Dependencies are managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock` — no `requirements.txt`). To run without Docker: `uv sync`, then `uv run python manage.py ...`. Use `uv add <package>` / `uv remove <package>` and commit the updated `uv.lock`; don't hand-edit dependency versions in `pyproject.toml`.

Site: http://localhost:8000 · Admin: http://localhost:8000/admin/ · Mailhog (catches contact-form emails in dev): http://localhost:8025

## Architecture

### App boundary: `base` holds shared StreamField blocks, not page content

`base/blocks.py` defines the blocks reused across apps: `BodyStreamBlock` (heading, richtext, image, quote, embed, code) is used by both `blog.BlogPage.body` and `projects.ProjectPage.body`, and `HomeStreamBlock` (hero, featured_projects, latest_posts, CTA) drives `home.HomePage.sections`. When adding a block type meant to appear in more than one page's StreamField, put it in `base/blocks.py`, not in the app that happens to need it first. `base` also holds `SiteSettings` (`base/models.py`, footer text, social links, default OG image) and the `primary_nav` template tag (`base/templatetags/navigation_tags.py`).

Changing `base/blocks.py` changes the migration state of every app whose StreamField uses those blocks (see `blog/migrations/0002_alter_blogpage_body.py` / `projects/migrations/0002_alter_projectpage_body.py` for the precedent) — run `makemigrations` for all affected apps together, not just the one you were editing.

### CV/portfolio data model: Orderable + InlinePanel, not StreamField

`about.AboutPage`'s work experience, education, certificates, and skills are `Orderable` child models with `ParentalKey`/`InlinePanel` (see `about/models.py`), not StreamField blocks. This is deliberate: they're homogeneous, schema-rigid, repeating records (a work history entry always has a job title, org, start/end date), where StreamField's freeform reordering-of-mixed-types doesn't add anything — the plain child-model + `InlinePanel` pattern gives typed fields and ordering for free. `AboutPage.get_grouped_skills()` groups the flat `Skill` list by category for the template.

`projects.Technology` and `blog.BlogCategory` are `@register_snippet` models (shared taxonomies across pages), while `blog` tags use the standard Wagtail/taggit `ClusterTaggableManager` + `TaggedItemBase` pattern (`BlogPageTag`). Don't add a fifth taxonomy mechanism — extend one of these three depending on whether it's a controlled vocabulary (snippet) or freeform (taggit).

`BlogIndexPage.get_context()` filters the category list down to categories actually used by a *live* post (`BlogCategory.objects.filter(blogpage__in=self.get_posts())`) rather than listing every snippet — an unused category is a dead filter option, not a useful one. Keep that pattern if you add a similar filter (e.g. a tag cloud) elsewhere.

### Settings split and env handling

`website/settings/{base,dev,production}.py`, all env-driven via `django-environ`. `production.py` does `from .base import *` and is intentionally exempted from ruff's F403/F405 in `pyproject.toml`. Media storage in `production.py` switches to S3 (`storages.backends.s3.S3Storage`) only if `AWS_STORAGE_BUCKET_NAME` is set — leave it unset for the VM deployment path, where media lives in a local Docker volume instead.

### Two deployment paths, one Dockerfile

`Dockerfile` is multi-stage: `builder` (uv-installed prod deps only) → `dev` (adds the `dev` dependency group on top, bind-mount target for `docker-compose.yml`) → `runtime` (the production image, COPYs the app in, runs `collectstatic` at build time with throwaway env values, then `migrate && gunicorn` at container start).

- `docker-compose.yml` — local dev, targets the `dev` stage.
- `docker-compose.prod.yml` — self-hosted VM deployment (the recommended path for this project): Postgres and uploaded media both live in named Docker volumes on the VM itself (no managed DB, no S3), fronted by Caddy (`Caddyfile`) for automatic HTTPS. Has its own explicit `name: website-prod` — do not remove that, since without it Compose derives the project name from the directory and collides with `docker-compose.yml`'s containers/volumes/images (this happened once; see git history).
- PaaS deployment (Render/Fly/Railway) is also supported by the plain `runtime` stage against a managed Postgres + S3 media — see README for details. Don't assume PaaS when changing deployment-related code; check which path a change targets.

### Design system

`website/static/css/{tokens,layout,components,code}.css`, loaded in that order from `website/templates/base.html`. `tokens.css` defines the palette/type-scale as custom properties (light default, overridden under both `@media (prefers-color-scheme: dark)` and `:root[data-theme="dark"/"light"]` for an explicit toggle) — style everything through the tokens, not with hardcoded colors. Fonts (JetBrains Mono for headings/labels, Public Sans for body) are self-hosted under `website/static/fonts/`, no font CDN.

Two non-obvious CSS fixes worth knowing before you touch related markup:
- `.card__image` needs `height: auto` explicitly — Wagtail's `{% image %}` tag emits `width`/`height` attributes matching the rendition exactly, which makes the browser treat height as definite and ignore the `aspect-ratio` CSS property unless overridden.
- The mobile nav (`base/templates/base/includes/primary_nav.html`) uses a checkbox + sibling-selector toggle, not `<details>`/`<summary>` — a closed `<details>` element's box collapses to 0×0 in every engine even if you force the child's `display` back open with CSS, which breaks a "always-open on desktop, collapsible on mobile" nav.

Code blocks (the `code` block in `BodyStreamBlock`) are highlighted server-side with Pygments (`base/blocks.py`'s `CodeBlock.get_context`) — no client-side JS highlighter. `code.css` holds the generated Pygments theme (light + dark variants); regenerate it with `pygments.formatters.HtmlFormatter(style=...).get_style_defs(...)` if you change the styles, don't hand-edit the color rules.

### Search

Uses Wagtail's built-in DB search backend (`search/views.py`), which automatically uses Postgres full-text search since the project runs on Postgres — no separate search service.
