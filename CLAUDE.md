# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal website (portfolio / CV / blog / contact form) built on Wagtail 7 + Django 5.2. All content is edited through the Wagtail admin at `/admin/` — page models exist so that Home, About, Projects, and Blog content can be changed without touching code.

## Commands

Local dev runs directly with `manage.py runserver` — no Docker, no separate database server. `website/settings/dev.py` defaults to SQLite (`db.sqlite3`) if `DATABASE_URL` isn't set.

```bash
uv sync                       # install/update deps into .venv

# migrations / superuser
uv run python manage.py migrate
uv run python manage.py createsuperuser

# after changing any model (including StreamField block definitions in
# base/blocks.py — Wagtail migrations track those too)
uv run python manage.py makemigrations
uv run python manage.py migrate

# tests — full suite or a single app/test
uv run python manage.py test
uv run python manage.py test blog
uv run python manage.py test contact.tests.ContactPageSubmissionTests.test_valid_submission_creates_record_and_sends_email

# lint / format
uv run ruff check .
uv run ruff format .

uv run python manage.py runserver
```

Dependencies are managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock` — no `requirements.txt`). Use `uv add <package>` / `uv remove <package>` and commit the updated `uv.lock`; don't hand-edit dependency versions in `pyproject.toml`.

Site: http://localhost:8000 · Admin: http://localhost:8000/admin/ · Emails print to the console in dev (see `EMAIL_URL` in `.env.example`).

## Architecture

### App boundary: `base` holds shared StreamField blocks, not page content

`base/blocks.py` defines the blocks reused across apps: `BodyStreamBlock` (heading, richtext, image, quote, embed, code) is used by both `blog.BlogPage.body` and `projects.ProjectPage.body`, and `HomeStreamBlock` (hero, featured_projects, latest_posts, CTA) drives `home.HomePage.sections`. When adding a block type meant to appear in more than one page's StreamField, put it in `base/blocks.py`, not in the app that happens to need it first. `base` also holds `SiteSettings` (`base/models.py`, footer text, social links, default OG image) and the `primary_nav` template tag (`base/templatetags/navigation_tags.py`).

Changing `base/blocks.py` changes the migration state of every app whose StreamField uses those blocks (see `blog/migrations/0002_alter_blogpage_body.py` / `projects/migrations/0002_alter_projectpage_body.py` for the precedent) — run `makemigrations` for all affected apps together, not just the one you were editing.

### CV/portfolio data model: Orderable + InlinePanel, not StreamField

`about.AboutPage`'s work experience, education, certificates, and skills are `Orderable` child models with `ParentalKey`/`InlinePanel` (see `about/models.py`), not StreamField blocks. This is deliberate: they're homogeneous, schema-rigid, repeating records (a work history entry always has a job title, org, start/end date), where StreamField's freeform reordering-of-mixed-types doesn't add anything — the plain child-model + `InlinePanel` pattern gives typed fields and ordering for free. `AboutPage.get_grouped_skills()` groups the flat `Skill` list by category for the template.

`projects.Technology` and `blog.BlogCategory` are `@register_snippet` models (shared taxonomies across pages), while `blog` tags use the standard Wagtail/taggit `ClusterTaggableManager` + `TaggedItemBase` pattern (`BlogPageTag`). Don't add a fifth taxonomy mechanism — extend one of these three depending on whether it's a controlled vocabulary (snippet) or freeform (taggit).

The CV itself is single-language. The only bilingual piece is the resume download — `AboutPage.resume_pdf` (English) and `resume_pdf_pt` (Português) are just two separate uploaded files, and the template shows both download buttons whenever both are set. This was a deliberate scope cut: don't extend it into full page-content translation (per-language `intro`/`intro_pt` fields, duplicated work-experience/education entries, etc.) unless explicitly asked for — that was tried once and explicitly rejected in favor of keeping this scoped to just the resume file.

`BlogIndexPage.get_context()` filters the category list down to categories actually used by a *live* post (`BlogCategory.objects.filter(blogpage__in=self.get_posts())`) rather than listing every snippet — an unused category is a dead filter option, not a useful one. Keep that pattern if you add a similar filter (e.g. a tag cloud) elsewhere.

### Settings split and env handling

`website/settings/{base,dev,production}.py`, all env-driven via `django-environ`. `dev.py` defaults `DATABASE_URL` to a local SQLite file and `EMAIL_URL` to the console backend, so local dev needs no external services. `production.py` does `from .base import *` and is intentionally exempted from ruff's F403/F405 in `pyproject.toml`. Media storage in `production.py` switches to S3 (`storages.backends.s3.S3Storage`) only if `AWS_STORAGE_BUCKET_NAME` is set — leave it unset for the VM deployment path, where media lives in a local Docker volume instead.

### Two deployment paths, one Dockerfile

Docker is a production-only concern in this repo — local dev runs `manage.py runserver` directly, no containers involved. `Dockerfile` is multi-stage: `builder` (uv-installed prod deps only) → `runtime` (the production image, COPYs the app in, runs `collectstatic` at build time with throwaway env values, then `migrate && gunicorn` at container start).

- `docker-compose.prod.yml` — self-hosted VM deployment (the recommended path for this project): Postgres and uploaded media both live in named Docker volumes on the VM itself (no managed DB, no S3), fronted by Caddy (`Caddyfile`). Has its own explicit `name: website-prod`.
- PaaS deployment (Render/Fly/Railway) is also supported by the plain `runtime` stage against a managed Postgres + S3 media — see README for details.

Don't assume one when changing deployment-related code; check which path a change targets.

Caddy defaults to `{$DOMAIN}` for automatic Let's Encrypt HTTPS, which needs the VM directly reachable on 80/443 from the public internet. If the VM instead sits behind another reverse proxy that already terminates TLS (this repo's own deployment is set up this way, behind CloudPanel) — the Caddyfile switches to `:80` plain HTTP, the Caddy port mapping in `docker-compose.prod.yml` becomes `8080:80` instead of `80:80` (rootless Docker installs can't bind ports below 1024 without extra host config), and `.env.prod` keeps `SECURE_SSL_REDIRECT=false` as a defensive default even though the `trusted_proxies` fix below means Django now detects HTTPS correctly. Also note: Django's `urls.py` only serves `MEDIA_URL` when `DEBUG=True` — in production, Caddy serves `/media/*` directly from the same `media_data` volume (mounted read-only into the `caddy` service too), not Django/WhiteNoise.

The Caddyfile's global `servers { trusted_proxies static 172.16.0.0/12 }` block matters in the reverse-proxy-fronted mode: Docker's port-publishing NAT makes CloudPanel's connection appear to Caddy as coming from the Docker bridge gateway IP, not CloudPanel's real address, so without `trusted_proxies` Caddy doesn't trust the `X-Forwarded-Proto: https` CloudPanel actually sends and resets it to `http` (Caddy's own listener is plain HTTP) before forwarding to Django. That silently broke `request.is_secure()`/`request.scheme` — canonical URLs, `og:url`, and JSON-LD `url` fields rendered as `http://` despite every real visitor being on HTTPS, and Django's own HSTS header logic never fired. Confirmed via a temporary Caddy access log on the deployed VM showing the real inbound `X-Forwarded-Proto` and connecting IP; verify a fresh deployment's actual Docker bridge subnet with `docker network inspect <project>_default` if headers still look wrong after deploying — `172.16.0.0/12` covers Docker's default bridge range but isn't guaranteed for every Docker install.

Security response headers are split by who has a config knob for them: `Content-Security-Policy`, `Permissions-Policy`, and `Cross-Origin-Resource-Policy` are set in `Caddyfile` since Django has no built-in setting for them, while `Strict-Transport-Security`, `X-Content-Type-Options`, and `X-Frame-Options` come from Django's `SecurityMiddleware`/`XFrameOptionsMiddleware` (`website/settings/production.py`) — don't add HSTS to the Caddyfile too, that produced two different `Strict-Transport-Security` values on the same response (see the `trusted_proxies` note above for why Django's copy didn't used to fire in the reverse-proxy-fronted mode). CSP/Permissions-Policy are scoped to skip `/admin/*` (via a Caddy `not path` matcher) because Wagtail admin and the front-end `{% wagtailuserbar %}` overlay need inline scripts/styles that a strict policy would break. If a reverse proxy in front of Caddy (e.g. CloudPanel) also injects its own default security headers, turn that off in the proxy's vhost config — otherwise the client sees two values for the same header (observed in practice: CloudPanel's own `X-Frame-Options: SAMEORIGIN` alongside Django's `X-Frame-Options: DENY`), which security scanners flag and browsers resolve inconsistently.

### Design system

`website/static/css/{tokens,layout,components,code}.css`, loaded in that order from `website/templates/base.html`. `tokens.css` defines the palette/type-scale as custom properties (light default, overridden under both `@media (prefers-color-scheme: dark)` and `:root[data-theme="dark"/"light"]` for an explicit toggle) — style everything through the tokens, not with hardcoded colors. Two font families carry the whole site (self-hosted under `website/static/fonts/`, no font CDN): Clash Display for headings and the sidebar wordmark, General Sans for body copy. JetBrains Mono is used only inside code blocks, not as a UI font.

The layout is a fixed-width left "spine" (`base/templates/base/includes/primary_nav.html`, `.frame`/`.spine` in `layout.css`), not a top navbar: an identity mark, a numbered index of pages, and a colophon, sticky down the left side above the `64rem` breakpoint and collapsing to a full-screen overlay below it. Project/post listings (`.index-list`/`.index-row` in `components.css`) are numbered rows with a hover-revealed thumbnail rather than a card grid — `.card-grid` still exists, but only for the plain image gallery on project pages, with no card styling.

Two non-obvious things worth knowing before you touch related markup:
- The mobile nav's checkbox (`#nav-toggle`) must stay the *first* child inside `.spine__inner`, before `.spine__mark`, the toggle `<label>`, and `.spine__nav`. The CSS reveals the nav and swaps the toggle label's text via `:checked ~` (general sibling) selectors, which only match elements *after* the checkbox in the DOM — move the checkbox later and the toggle silently stops working (no error, it just never opens). A `<details>`/`<summary>` element was tried instead of this checkbox pattern early on and rejected: a closed `<details>`'s box collapses to 0×0 in every engine even if you force the child's `display` back open with CSS.
- Content-width containers come in three sizes (`tokens.css`'s `--content-width`/`--content-width-wide`/`--wide-width`, `.container--narrow`/`.container--medium`/`.container` in `layout.css`). About, Projects, and Blog (both index and detail pages) all deliberately use `.container--medium` so their content columns line up at the same width — don't reintroduce `.container--narrow` there without a reason.

Code blocks (the `code` block in `BodyStreamBlock`) are highlighted server-side with Pygments (`base/blocks.py`'s `CodeBlock.get_context`) — no client-side JS highlighter. `code.css` holds the generated Pygments theme (light + dark variants); regenerate it with `pygments.formatters.HtmlFormatter(style=...).get_style_defs(...)` if you change the styles, don't hand-edit the color rules.

There is no front-end search page — the `search` app (a custom `/search/` view over Wagtail's DB search backend) was removed as unused. Wagtail's built-in search (`wagtail.search`, used internally by the admin) is unaffected.
