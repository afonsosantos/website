from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# SECURITY WARNING: fail loudly if no secret key is set - never fall back
# to an insecure default in production.
SECRET_KEY = env.str("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Most PaaS platforms (Render, Fly.io, Railway) terminate TLS at a reverse
# proxy in front of the container and forward this header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

# Media storage: containers on most PaaS targets are ephemeral, so
# user-uploaded Images/Documents (including the CV/resume PDF) need
# persistent storage. Switch to S3-compatible object storage (AWS S3,
# Cloudflare R2, Backblaze B2, ...) whenever a bucket is configured;
# otherwise fall back to the local filesystem (fine only for single-instance
# deploys with an attached persistent volume).
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", default="")
if AWS_STORAGE_BUCKET_NAME:
    STORAGES["default"]["BACKEND"] = "storages.backends.s3.S3Storage"
    AWS_S3_ENDPOINT_URL = env.str("AWS_S3_ENDPOINT_URL", default="")
    AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="")
    AWS_S3_CUSTOM_DOMAIN = env.str("AWS_S3_CUSTOM_DOMAIN", default="")
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False

WAGTAILADMIN_BASE_URL = env.str("WAGTAILADMIN_BASE_URL")

EMAIL_CONFIG = env.email_url("EMAIL_URL")
vars().update(EMAIL_CONFIG)
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL")

# Log to stdout so the platform's log collector picks it up.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env.str("DJANGO_LOG_LEVEL", default="INFO"),
    },
}

try:
    from .local import *  # noqa: F401,F403
except ImportError:
    pass
