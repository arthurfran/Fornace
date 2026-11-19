import json
import logging
from django.core.exceptions import RequestDataTooBig
from django.db import IntegrityError
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views import View
from django.views.generic import ListView
from django.contrib.auth import logout
from .mixins import (
    AdministradorRequiredMixin,
    GarcomRequiredMixin,
    OperadorRequiredMixin,
    GerencialRequiredMixin,
)
from .domain import DomainError
from .identity import Identidade, Sessao
from .locking import operacao_atomica
from .models import ItemCardapio, Mesa, Usuario
from . import serializers as ser
from .services import (
    Autenticacao,
    Carrinho,
    ConfirmacaoPedido,
    ConsultaPedidos,
    Preparo,
    Entrega,
    Escala,
    Disponibilidade,
    AdministracaoUsuarios,
)
from .analytics import AnaliseProducao

logger = logging.getLogger(__name__)


def csrf_failure(request, reason=""):
    return JsonResponse(
        {"erro": "Sessão de segurança expirada. Recarregue a página."}, status=403
    )


class ApiView(View):
    http_method_names = ["get", "post", "patch", "options"]

    def dispatch(self, request, *args, **kwargs):
        try:
            self.dados = {}
            if request.method in ("POST", "PATCH"):
                if request.content_type != "application/json":
                    raise DomainError("Envie JSON.", 415)
                try:
                    self.dados = json.loads(request.body or "{}")
                except (ValueError, UnicodeDecodeError):
                    raise DomainError("JSON inválido.", 400)
                if not isinstance(self.dados, dict):
                    raise DomainError("Envie um objeto JSON.", 400)
            return super().dispatch(request, *args, **kwargs)
        except DomainError as e:
            return JsonResponse({"erro": e.message}, status=e.status)
        except RequestDataTooBig:
            return JsonResponse({"erro": "Requisição muito grande."}, status=413)
        except IntegrityError:
            logger.exception("Restrição de integridade na operação")
            return JsonResponse(
                {"erro": "A alteração viola uma regra do banco de dados."}, status=409
            )

    def resposta(self, data, status=200):
        return JsonResponse(data, status=status)


class ContextoView(ApiView):
    def get(self, request):
        with operacao_atomica():
            session = Sessao(request)
            session.salvar()
        return self.resposta(
            {
                "identidade": ser.identidade(session.identidade),
                "csrf": get_token(request),
                "mesas": list(
                    Mesa.objects.order_by("id_mesa").values(
                        "id_mesa", "identificacao", "tipo_local"
                    )
                ),
                "garcons": [
                    {
                        "id": g.pk,
                        "nome": g.usuario.nome,
                        "setor": g.setor,
                        "carga": g.carga,
                    }
                    for g in ConfirmacaoPedido.elegiveis().order_by("id_garcom")
                ],
            }
        )


class LoginView(ApiView):
    def post(self, request):
        identity = Autenticacao().entrar(request, self.dados)
        return self.resposta({"identidade": identity, "csrf": get_token(request)})


class CadastroView(ApiView):
    def post(self, request):
        identity = Autenticacao().cadastrar(request, self.dados)
        return self.resposta({"identidade": identity, "csrf": get_token(request)}, 201)


class LogoutView(ApiView):
    def post(self, request):
        logout(request)
        return self.resposta({"ok": True})


class ListaJsonView(ApiView, ListView):
    """A mesma ListView do Django, devolvendo JSON para o frontend React."""

    def render_to_response(self, context, **response_kwargs):
        return self.resposta(
            {
                self.context_object_name: [
                    self.serializador(obj) for obj in context[self.context_object_name]
                ]
            }
        )


class CardapioView(ListaJsonView):
    model = ItemCardapio
    context_object_name = "itens"
    serializador = staticmethod(ser.cardapio)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("categoria")
            .order_by("id_item_cardapio")
        )


class CarrinhoView(ApiView):
    def get(self, request, origem):
        return self.resposta(Carrinho().ler(request, origem))

    def post(self, request, origem):
        return self.resposta(Carrinho().alterar(request, origem, self.dados))


class ConfirmacaoView(ApiView):
    def post(self, request, origem):
        return self.resposta(
            {"pedido": ConfirmacaoPedido().executar(request, origem, self.dados)}, 201
        )


class PedidosView(ApiView):
    def get(self, request):
        before = request.GET.get("antes")
        if before:
            try:
                before = int(before)
            except ValueError:
                raise DomainError("Página inválida.", 400)
        return self.resposta(
            ConsultaPedidos().executar(
                request,
                request.GET.get("visao", "cliente"),
                historico=request.GET.get("historico") == "1",
                antes=before,
            )
        )


class PreparoView(OperadorRequiredMixin, ApiView):
    def patch(self, request, item_id):
        return self.resposta(
            {"pedido": Preparo().executar(request, item_id, self.dados)}
        )


class EntregaView(GarcomRequiredMixin, ApiView):
    def post(self, request, pedido_id):
        return self.resposta({"pedido": Entrega().executar(request, pedido_id)})


class EscalaView(GarcomRequiredMixin, ApiView):
    def patch(self, request):
        return self.resposta({"usuario": Escala().executar(request, self.dados)})


class DisponibilidadeView(OperadorRequiredMixin, ApiView):
    def patch(self, request, item_id):
        return self.resposta(
            {"item": Disponibilidade().executar(request, item_id, self.dados)}
        )


class UsuariosView(AdministradorRequiredMixin, ListaJsonView):
    model = Usuario
    context_object_name = "usuarios"
    serializador = staticmethod(ser.usuario)

    def get_queryset(self):
        return (
            super().get_queryset().select_related("garcom", "operador").order_by("nome")
        )

    def post(self, request):
        return self.resposta(
            {"usuario": AdministracaoUsuarios().salvar(request, self.dados)}, 201
        )


class UsuarioView(AdministradorRequiredMixin, ApiView):
    def patch(self, request, user_id):
        return self.resposta(
            {"usuario": AdministracaoUsuarios().salvar(request, self.dados, user_id)}
        )


class AnaliseView(GerencialRequiredMixin, ApiView):
    def get(self, request):
        return self.resposta(AnaliseProducao().executar(request))


class SaudeView(ApiView):
    def get(self, request):
        Mesa.objects.exists()
        return self.resposta({"status": "ok"})
