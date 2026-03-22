from .base import *
from decouple import config

DEBUG = False

# Enforce strictly defined hosts
ALLOWED_HOSTS = [
    ".railway.app",
    "gradus-django.up.railway.app",
]

# External domain from env overrides if provided
if config("DOMAIN_NAME", default=""):
    ALLOWED_HOSTS.append(config("DOMAIN_NAME"))

try:
    import dj_database_url
    # Production databases typically utilize external services (e.g Postgres) via credentials provided in DATABASE_URL
    DATABASES = {
        "default": dj_database_url.config(
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
except ImportError:
    # Safe fallback just in case the app goes live without dj-database-url
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ==============================
# CLOUD STORAGE (Media & Static)
# ==============================
# Azure overrides read safely from environment
AZURE_ACCOUNT_NAME = config("AZURE_ACCOUNT_NAME", default="")
AZURE_ACCOUNT_KEY = config("AZURE_ACCOUNT_KEY", default="")
AZURE_CONTAINER = config("AZURE_CONTAINER", default="media")

WHITENOISE_MANIFEST_STRICT = False

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "account_name": AZURE_ACCOUNT_NAME,
            "account_key": AZURE_ACCOUNT_KEY,
            "azure_container": AZURE_CONTAINER,
            "custom_domain": config("AZURE_CUSTOM_DOMAIN", default=None),
            "timeout": 20,
            # Production URLs shouldn't expire if they are public media. 
            # If they should be private, adjust expiration_secs logic here.
            "expiration_secs": config("AZURE_URL_EXPIRATION_SECS", default=None, cast=lambda v: int(v) if v else None),
        },
    },
}


# ==============================
# HTTP PROXY HEADERS & SECURITY
# ==============================

CSRF_TRUSTED_ORIGINS = [
    "https://gradus-django.up.railway.app",
    "https://*.railway.app",
    "https://gradus-frontend-theta.vercel.app",
]

CORS_ALLOWED_ORIGINS = [
    "https://gradus-django.up.railway.app",
    "https://gradus-frontend-theta.vercel.app",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# Instructs Django to use HTTPS
SECURE_SSL_REDIRECT = config("DJANGO_SECURE_SSL_REDIRECT", default=True, cast=bool)

# Cookie hardening
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Additional Security Checkups
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# HTTP Strict Transport Security
SECURE_HSTS_SECONDS = 31536000 # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True 

# Forwarding IP configuration when behind proxy (like Railway/Heroku)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
