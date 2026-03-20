from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "*"]

# Database for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Explicitly define local storage to ensure cloud storage isn't used by accident

AZURE_ACCOUNT_NAME = config("AZURE_ACCOUNT_NAME", default="")
AZURE_ACCOUNT_KEY = config("AZURE_ACCOUNT_KEY", default="")
AZURE_CONTAINER = config("AZURE_CONTAINER", default="media")

STORAGES = {
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
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS for local development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Enable Django session login backend locally (since base configs usually set it to False to prefer tokens)
REST_SESSION_LOGIN = True
