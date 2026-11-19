from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse


class PerfilRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixins do Django com erro JSON para o React, em lugar de redirecionamento."""

    perfil = None

    def test_func(self):
        usuario = self.request.user
        if not usuario.is_authenticated or not usuario.ativo:
            return False
        if self.perfil == "administrador":
            return usuario.administrador
        if self.perfil == "gerencial":
            return hasattr(usuario, "operador") and usuario.operador.perfil_gerencial
        return hasattr(usuario, self.perfil)

    def handle_no_permission(self):
        return JsonResponse(
            {"erro": "Entre com uma conta que possua o perfil necessário."}, status=403
        )


class AdministradorRequiredMixin(PerfilRequiredMixin):
    perfil = "administrador"


class GarcomRequiredMixin(PerfilRequiredMixin):
    perfil = "garcom"


class OperadorRequiredMixin(PerfilRequiredMixin):
    perfil = "operador"


class GerencialRequiredMixin(PerfilRequiredMixin):
    perfil = "gerencial"
