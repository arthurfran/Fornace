from dataclasses import dataclass
from types import SimpleNamespace
from django.contrib import auth
from datetime import timedelta
from django.contrib.sessions.backends.db import SessionStore
from django.middleware.csrf import rotate_token
from django.utils import timezone
from .models import Usuario, Cliente
from .domain import DomainError


@dataclass
class Identidade:
    tipo: str
    pessoa: object = None

    @classmethod
    def da_sessao(cls, session):
        # A equipe usa a sessão autenticada do Django, incluindo validação do hash.
        if session.get(auth.SESSION_KEY):
            pessoa = auth.get_user(SimpleNamespace(session=session))
            if pessoa.is_authenticated and pessoa.ativo:
                return cls("usuario", pessoa)
        raw = session.get("identidade", {})
        if raw.get("tipo") == "cliente":
            pessoa = Cliente.objects.filter(pk=raw.get("id")).first()
            if pessoa:
                return cls("cliente", pessoa)
        return cls("anonimo")

    def exigir_usuario(self):
        if self.tipo != "usuario":
            raise DomainError("Entre com uma conta da equipe.", 403)
        return self.pessoa

    def exigir_garcom(self, escala=False):
        user = self.exigir_usuario()
        if not hasattr(user, "garcom"):
            raise DomainError("Perfil de garçom necessário.", 403)
        if escala and not user.garcom.em_escala:
            raise DomainError("Entre na escala para registrar pedidos no salão.")
        return user.garcom

    def exigir_operador(self, gerencial=False):
        user = self.exigir_usuario()
        if not hasattr(user, "operador"):
            raise DomainError("Perfil de operador necessário.", 403)
        if gerencial and not user.operador.perfil_gerencial:
            raise DomainError("Permissão gerencial necessária.", 403)
        return user.operador

    def exigir_admin(self):
        user = self.exigir_usuario()
        if not user.administrador:
            raise DomainError("Permissão de administrador necessária.", 403)
        return user


class Sessao:
    """Relê o carrinho sob o bloqueio transacional, evitando checkout duplicado."""

    def __init__(self, request):
        self.request = request
        self.store = SessionStore(session_key=request.session.session_key)
        self.store.load()
        if not self.store.get("expira_em"):
            expiry = timezone.now() + timedelta(hours=12)
            self.store["expira_em"] = expiry.isoformat()
            self.store.set_expiry(expiry)
        self.identidade = Identidade.da_sessao(self.store)

    def entrar(self, tipo, pessoa):
        previous = self.store.get("identidade")
        if previous and previous != {"tipo": tipo, "id": pessoa.pk}:
            for key in (
                "carrinho_cliente",
                "carrinho_salao",
                "confirmacoes",
                "pedidos_proprios",
            ):
                self.store.pop(key, None)
        if tipo == "usuario":
            self.request.session = self.store
            auth.login(
                self.request, pessoa, backend="restaurante.backends.UsuarioBackend"
            )
            self.store = self.request.session
        else:
            for key in (
                auth.SESSION_KEY,
                auth.BACKEND_SESSION_KEY,
                auth.HASH_SESSION_KEY,
            ):
                self.store.pop(key, None)
            self.store.cycle_key()
        self.store["identidade"] = {"tipo": tipo, "id": pessoa.pk}
        expiry = timezone.now() + timedelta(hours=12)
        self.store["expira_em"] = expiry.isoformat()
        self.store.set_expiry(expiry)
        rotate_token(self.request)

    def salvar(self):
        self.store.save()
        # SessionMiddleware deve emitir o cookie, sem salvar um snapshot obsoleto.
        self.request.session = self.store
        self.store.modified = False
        self.request._sessao_salva = True
