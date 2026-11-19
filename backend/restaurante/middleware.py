from django.conf import settings
from django.utils.http import http_date
from django.utils import timezone


class CookieSessaoMiddleware:
    """Emite o cookie após a gravação transacional, sem repetir a gravação no banco."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(request, "_sessao_salva", False):
            max_age = request.session.get_expiry_age()
            response.set_cookie(
                settings.SESSION_COOKIE_NAME,
                request.session.session_key,
                max_age=max_age,
                expires=http_date(timezone.now().timestamp() + max_age),
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
                secure=settings.SESSION_COOKIE_SECURE,
                httponly=True,
                samesite="Lax",
            )
        if request.path.startswith("/api/"):
            response["Cache-Control"] = "no-store"
        return response
