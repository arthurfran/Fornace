"""Configuração do serviço Fornace no Render, separada da execução local."""

from .settings import *  # noqa: F403

DEBUG = False
SECRET_KEY = os.getenv("SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError("Configure SECRET_KEY no painel do Render.")
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise RuntimeError("Configure DATABASE_URL com o PostgreSQL do Fornace.")

HOST_RENDER = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
ALLOWED_HOSTS = [
    host
    for host in [
        HOST_RENDER,
        "localhost",
        "127.0.0.1",
        *os.getenv("ALLOWED_HOSTS", "").split(","),
    ]
    if host.strip()
]
if HOST_RENDER:
    CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, f"https://{HOST_RENDER}"]

# O proxy do Render termina o TLS e encaminha o esquema original.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r"^api/saude/$"]
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

MIDDLEWARE = [
    MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# WhiteNoise serve o index.html do Vite em / e os arquivos em /assets/.
WHITENOISE_ROOT = BASE_DIR.parent / "frontend" / "dist"
WHITENOISE_INDEX_FILE = True
FORNACE_URL = "/"
