"""Casos de uso: autorização, transação e colaboração entre entidades."""

import hashlib
import secrets
import uuid
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Count, Max, Q
from django.utils import timezone
from .forms import (
    validar,
    LoginForm,
    CadastroClienteForm,
    CarrinhoForm,
    ConfirmacaoForm,
    PreparoForm,
    EscalaForm,
    DisponibilidadeForm,
    UsuarioForm,
)
from . import serializers as ser
from .domain import DomainError, MenorCarga, Totais
from .identity import Identidade, Sessao
from .locking import operacao_atomica
from .models import (
    Usuario,
    Cliente,
    Garcom,
    OperadorCozinha,
    Mesa,
    ItemCardapio,
    Pedido,
    ItemPedido,
)

DUMMY_HASH = make_password("senha-aleatoria-para-uniformizar-verificacao")


def pedidos_completos():
    return Pedido.objects.select_related(
        "mesa", "cliente", "garcom__usuario"
    ).prefetch_related("itens__item_cardapio__categoria", "itens__operador__usuario")


def obter(model, pk):
    obj = model.objects.filter(pk=pk).first()
    if obj is None:
        raise DomainError("Registro não encontrado.", 404)
    return obj


class Autenticacao:
    def entrar(self, request, dados):
        dados = validar(LoginForm(dados))
        tipo, login, password = dados["tipo"], dados["login"], dados["senha"]
        # REMOTE_ADDR fornecido pelo proxy confiável; não confiar em X-Forwarded-For arbitrário.
        ip = request.META.get("REMOTE_ADDR", "")
        keys = [
            "login:" + hashlib.sha256(s.encode()).hexdigest()
            for s in (ip, ip + "|" + tipo + "|" + login)
        ]
        erro = None
        with operacao_atomica():
            attempts = [cache.get(key, 0) for key in keys]
            if attempts[0] >= 40 or attempts[1] >= 5:
                erro = DomainError("Muitas tentativas. Aguarde 5 minutos.", 429)
            else:
                if tipo == "usuario":
                    pessoa = authenticate(request, username=login, password=password)
                    valido = pessoa is not None
                else:
                    pessoa = Cliente.objects.filter(email=login).first()
                    valido = check_password(
                        password, pessoa.senha_hash if pessoa else DUMMY_HASH
                    )
                if not valido:
                    for key, n in zip(keys, attempts):
                        cache.set(key, n + 1, 300)
                    erro = DomainError("Credenciais inválidas.", 401)
                else:
                    cache.delete(keys[1])
                    session = Sessao(request)
                    session.entrar(tipo, pessoa)
                    session.salvar()
        if erro:
            raise erro
        return ser.identidade(Identidade(tipo, pessoa))

    def cadastrar(self, request, dados):
        with operacao_atomica():
            form = CadastroClienteForm(dados)
            validar(form)
            client = form.save()
            session = Sessao(request)
            session.entrar("cliente", client)
            session.salvar()
        return ser.identidade(Identidade("cliente", client))


class Carrinho:
    @staticmethod
    def chave(session, origem):
        if origem == "salao":
            session.identidade.exigir_garcom()
        elif origem != "cliente":
            raise DomainError("Origem inválida.", 400)
        elif session.identidade.tipo == "usuario":
            raise DomainError("Use o lançamento do salão com perfil de garçom.", 403)
        return "carrinho_" + origem

    @staticmethod
    def vazio():
        return {"revisao": uuid.uuid4().hex, "mesa_id": None, "linhas": []}

    def ler(self, request, origem):
        with operacao_atomica():
            session = Sessao(request)
            key = self.chave(session, origem)
            cart = session.store.get(key) or self.vazio()
            session.store[key] = cart
            session.salvar()
        return ser.carrinho(cart)

    def alterar(self, request, origem, dados):
        dados = validar(CarrinhoForm(dados))
        with operacao_atomica():
            session = Sessao(request)
            key = self.chave(session, origem)
            cart = session.store.get(key) or self.vazio()
            action = dados["acao"]
            if action == "mesa":
                mesa = obter(Mesa, dados["mesa_id"])
                cart["mesa_id"] = mesa.pk
            elif action == "adicionar":
                if len(cart["linhas"]) >= 50:
                    raise DomainError("Limite de 50 linhas no carrinho.")
                item = obter(ItemCardapio, dados["item_id"])
                if not item.disponivel:
                    raise DomainError("Item indisponível para novas inclusões.")
                cart["linhas"].append(
                    {
                        "id": uuid.uuid4().hex,
                        "item_id": item.pk,
                        "nome": item.nome,
                        "preco": str(item.preco_atual),
                        "tempo": item.tempo_medio_preparo_min,
                        "quantidade": dados["quantidade"],
                        "observacoes": dados["observacoes"],
                    }
                )
            elif action in ("alterar", "remover"):
                line_id = dados["linha_id"]
                line = next((l for l in cart["linhas"] if l["id"] == line_id), None)
                if not line:
                    raise DomainError("Linha não encontrada.", 404)
                if action == "remover":
                    cart["linhas"].remove(line)
                else:
                    line["quantidade"] = dados["quantidade"]
                    line["observacoes"] = dados["observacoes"]
            elif action == "limpar":
                cart["linhas"] = []
            else:
                raise DomainError("Ação inválida.", 400)
            cart["revisao"] = uuid.uuid4().hex
            session.store[key] = cart
            session.salvar()
        return ser.carrinho(cart)


class ConfirmacaoPedido:
    def __init__(self, politica=None):
        self.politica = politica or MenorCarga()

    @staticmethod
    def elegiveis():
        return (
            Garcom.objects.filter(usuario__ativo=True, em_escala=True)
            .select_related("usuario")
            .annotate(
                carga=Count("pedidos", filter=~Q(pedidos__situacao_atual="ENTREGUE")),
                ultima=Max("pedidos__atribuido_em"),
            )
        )

    def executar(self, request, origem, dados):
        dados = validar(ConfirmacaoForm(dados))
        revision = dados["revisao"]
        with operacao_atomica():
            session = Sessao(request)
            key = Carrinho.chave(session, origem)
            receipts = session.store.get("confirmacoes", {})
            receipt_key = origem + ":" + revision
            if receipt_key in receipts:
                return ser.pedido(pedidos_completos().get(pk=receipts[receipt_key]))
            cart = session.store.get(key)
            if not cart or cart["revisao"] != revision:
                raise DomainError("O carrinho mudou. Atualize antes de confirmar.")
            if not cart["linhas"]:
                raise DomainError("Adicione pelo menos um item.")
            mesa = obter(Mesa, cart.get("mesa_id"))
            if origem == "salao":
                garcom = session.identidade.exigir_garcom(escala=True)
                forma = "PELO_SALAO"
            else:
                manual = dados.get("garcom_id")
                if manual is None:
                    garcom, forma = (
                        self.politica.escolher(list(self.elegiveis())),
                        "AUTOMATICA",
                    )
                else:
                    manual = dados["garcom_id"]
                    garcom = self.elegiveis().filter(pk=manual).first()
                    if not garcom:
                        raise DomainError("Garçom não está ativo e em escala.")
                    forma = "MANUAL"
            now = timezone.now()
            total = Totais.das_linhas(cart["linhas"]).total
            if total > 9999999999:
                raise DomainError("Valor excede o limite do pedido.")
            pedido = Pedido.objects.create(
                codigo="F-" + secrets.token_hex(5).upper(),
                mesa=mesa,
                cliente=(
                    session.identidade.pessoa
                    if session.identidade.tipo == "cliente"
                    else None
                ),
                garcom=garcom,
                origem="SALAO" if origem == "salao" else "AUTOATENDIMENTO",
                forma_atribuicao=forma,
                criado_em=now,
                atribuido_em=now,
                meta_preparo_min=min(
                    max(l["tempo"] for l in cart["linhas"]), settings.SLA_PREPARO_MIN
                ),
                valor_total_registrado=total,
            )
            ItemPedido.objects.bulk_create(
                [
                    ItemPedido(
                        pedido=pedido,
                        numero_linha=n,
                        item_cardapio_id=l["item_id"],
                        quantidade=l["quantidade"],
                        observacoes=l["observacoes"],
                        preco_unitario_registrado=l["preco"],
                        tempo_preparo_registrado_min=l["tempo"],
                    )
                    for n, l in enumerate(cart["linhas"], 1)
                ]
            )
            receipts[receipt_key] = pedido.pk
            # 50 confirmações por sessão; o histórico de clientes permanece no banco.
            session.store["confirmacoes"] = dict(list(receipts.items())[-50:])
            owned = session.store.get("pedidos_proprios", [])
            session.store["pedidos_proprios"] = (owned + [pedido.pk])[-200:]
            session.store[key] = {**Carrinho.vazio(), "mesa_id": mesa.pk}
            session.salvar()
            return ser.pedido(pedidos_completos().get(pk=pedido.pk))


class ConsultaPedidos:
    def executar(self, request, escopo, historico=False, antes=None):
        identity = Identidade.da_sessao(request.session)
        orders = pedidos_completos()
        if escopo == "cliente":
            if identity.tipo == "usuario":
                raise DomainError("Use a visão da equipe.", 403)
            if identity.tipo == "cliente":
                permission = Q(cliente=identity.pessoa)
                if not historico:
                    permission |= Q(
                        pk__in=request.session.get("pedidos_proprios", []),
                        cliente__isnull=True,
                    )
                orders = orders.filter(permission)
            else:
                orders = orders.filter(
                    pk__in=request.session.get("pedidos_proprios", []),
                    cliente__isnull=True,
                )
        elif escopo == "salao":
            orders = orders.filter(garcom=identity.exigir_garcom())
        elif escopo in ("cozinha", "monitor"):
            identity.exigir_operador()
        else:
            raise DomainError("Visão inválida.", 400)
        orders = (
            orders.filter(situacao_atual="ENTREGUE")
            if historico
            else orders.exclude(situacao_atual="ENTREGUE")
        )
        if antes:
            orders = orders.filter(pk__lt=antes)
        # ID monotônico torna a paginação estável mesmo com horários iguais.
        rows = list(orders.order_by("-id_pedido")[:101])
        return {
            "pedidos": [ser.pedido(p) for p in rows[:100]],
            "mais": len(rows) > 100,
            "antes": rows[99].pk if len(rows) > 100 else None,
        }


class Preparo:
    def executar(self, request, item_id, dados):
        dados = validar(PreparoForm(dados))
        destination = dados["situacao"]
        with operacao_atomica():
            operator = Identidade.da_sessao(request.session).exigir_operador()
            item = obter(ItemPedido, item_id)
            item.mudar_preparo(destination, operator, timezone.now())
            item.save(
                update_fields=[
                    "operador",
                    "situacao_preparo",
                    "inicio_preparo_em",
                    "pronto_em",
                ]
            )
            pedido = item.pedido
            pedido.recalcular_situacao(
                list(pedido.itens.values_list("situacao_preparo", flat=True))
            )
            pedido.save(update_fields=["situacao_atual"])
            return ser.pedido(pedidos_completos().get(pk=pedido.pk))


class Entrega:
    def executar(self, request, pedido_id):
        with operacao_atomica():
            waiter = Identidade.da_sessao(request.session).exigir_garcom()
            pedido = obter(Pedido, pedido_id)
            if pedido.situacao_atual == "ENTREGUE" and pedido.garcom_id == waiter.pk:
                return ser.pedido(pedidos_completos().get(pk=pedido.pk))
            pedido.entregar(waiter, timezone.now())
            pedido.save(update_fields=["situacao_atual", "entregue_em"])
            return ser.pedido(pedidos_completos().get(pk=pedido.pk))


class Escala:
    def executar(self, request, dados):
        dados = validar(EscalaForm(dados))
        with operacao_atomica():
            garcom = Identidade.da_sessao(request.session).exigir_garcom()
            garcom.em_escala = dados["em_escala"]
            garcom.save(update_fields=["em_escala"])
        return ser.usuario(garcom.usuario)


class Disponibilidade:
    def executar(self, request, item_id, dados):
        dados = validar(DisponibilidadeForm(dados))
        with operacao_atomica():
            Identidade.da_sessao(request.session).exigir_operador()
            item = obter(ItemCardapio, item_id)
            item.disponivel = dados["disponivel"]
            item.save(update_fields=["disponivel"])
        return ser.cardapio(item)


class AdministracaoUsuarios:
    def salvar(self, request, dados, user_id=None):
        with operacao_atomica():
            autor = Identidade.da_sessao(request.session).exigir_admin()
            usuario = obter(Usuario, user_id) if user_id else Usuario()
            form = UsuarioForm.da_api(dados, instance=usuario, autor=autor)
            validar(form)
            usuario = form.save()
            return ser.usuario(Usuario.objects.get(pk=usuario.pk))
