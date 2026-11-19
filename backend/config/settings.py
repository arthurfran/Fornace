"""Configuração local do Fornace: Django + SQLite, com PostgreSQL opcional."""

import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv("DEBUG", os.getenv("DJANGO_DEBUG", "1")) == "1"
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    os.getenv(
        "DJANGO_SECRET_KEY", "fornace-local-development-only-change-before-deploy"
    ),
)
if not DEBUG and SECRET_KEY.startswith("fornace-local"):
    raise RuntimeError("Defina SECRET_KEY quando DEBUG=0.")
ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS", os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
).split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "restaurante.apps.RestauranteConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "restaurante.middleware.CookieSessaoMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
AUTH_USER_MODEL = "restaurante.Usuario"
AUTHENTICATION_BACKENDS = ["restaurante.backends.UsuarioBackend"]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
        "OPTIONS": {"timeout": 20, "transaction_mode": "IMMEDIATE"},
    }
}
if os.getenv("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.config(
        conn_max_age=60, conn_health_checks=True
    )
    if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
        DATABASES["default"]["OPTIONS"] = {
            "timeout": 20,
            "transaction_mode": "IMMEDIATE",
        }
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "pt-br"
TIME_ZONE = os.getenv("RESTAURANT_TIME_ZONE", "America/Sao_Paulo")
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = os.getenv("HTTPS_ONLY", "0") == "1"
SECURE_SSL_REDIRECT = os.getenv("HTTPS_ONLY", "0") == "1"
CSRF_TRUSTED_ORIGINS = [
    v for v in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if v
]
CSRF_FAILURE_VIEW = "restaurante.views.csrf_failure"
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_entries",
    }
}
DATA_UPLOAD_MAX_MEMORY_SIZE = 65536
SLA_PREPARO_MIN = int(os.getenv("SLA_PREPARO_MIN", "18"))
SLA_ENTREGA_MIN = int(os.getenv("SLA_ENTREGA_MIN", "0")) or None
CAPACIDADE_PEDIDOS_HORA = int(os.getenv("CAPACIDADE_PEDIDOS_HORA", "0")) or None
if not 6 <= SLA_PREPARO_MIN <= 40:
    raise RuntimeError("SLA_PREPARO_MIN deve estar entre 6 e 40.")
if (SLA_ENTREGA_MIN or 0) < 0 or (CAPACIDADE_PEDIDOS_HORA or 0) < 0:
    raise RuntimeError("Prazos e capacidade devem ser não negativos.")
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"
