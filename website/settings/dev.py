import environ

from .base import *  # noqa: F401,F403
from .base import BASE_DIR

env = environ.Env()
environ.Env.read_env(str(BASE_DIR / ".env"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str(
    "SECRET_KEY", default="django-insecure-dev-only-secret-key-do-not-use-in-prod"
)

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

# Re-read DATABASE_URL now that .env has been loaded.
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

EMAIL_CONFIG = env.email_url("EMAIL_URL", default="consolemail://")
vars().update(EMAIL_CONFIG)

# Static files served straight off disk in dev - no compressed manifest storage.
STORAGES["staticfiles"]["BACKEND"] = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
)

try:
    from .local import *  # noqa: F401,F403
except ImportError:
    pass
