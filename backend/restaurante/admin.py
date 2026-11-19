"""Cadastros no Django Admin; os pedidos são consultados sem alterar o fluxo operacional."""

from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import Group
from .forms import UsuarioForm, ItemCardapioForm, MesaForm, CategoriaForm
from .locking import operacao_atomica
from .models import (
    Usuario,
    Garcom,
    OperadorCozinha,
    Cliente,
    Mesa,
    Categoria,
    ItemCardapio,
    Pedido,
    ItemPedido,
)

# O Fornace usa perfis próprios; grupos genéricos não participam do DER.
if admin.site.is_registered(Group):
    admin.site.unregister(Group)

admin.site.site_header = "Fornace · Administração"
admin.site.site_title = "Fornace"
admin.site.index_title = "Cadastros e consultas"
admin.site.site_url = getattr(settings, "FORNACE_URL", "http://127.0.0.1:5173/")


class CadastroAdmin(admin.ModelAdmin):
    def changeform_view(self, request, *args, **kwargs):
        if request.method == "POST":
            with operacao_atomica():
                return super().changeform_view(request, *args, **kwargs)
        return super().changeform_view(request, *args, **kwargs)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Usuario)
class UsuarioAdmin(CadastroAdmin):
    form = UsuarioForm
    list_display = ("nome", "login", "ativo", "administrador")
    list_filter = ("ativo", "administrador")
    search_fields = ("nome", "login")
    fieldsets = (
        ("Conta", {"fields": ("nome", "login", "senha", "ativo", "administrador")}),
        ("Garçom", {"fields": ("perfil_garcom", "setor", "em_escala")}),
        ("Cozinha", {"fields": ("perfil_operador", "funcao", "perfil_gerencial")}),
    )

    def get_form(self, request, obj=None, **kwargs):
        base = super().get_form(request, obj, **kwargs)

        class FormComAutor(base):
            def __init__(self, *args, **kw):
                kw["autor"] = request.user
                super().__init__(*args, **kw)

        return FormComAutor

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.salvar_perfis()


class ConsultaAdmin(admin.ModelAdmin):
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Garcom)
class GarcomAdmin(ConsultaAdmin):
    list_display = ("usuario", "setor", "em_escala")
    list_filter = ("em_escala",)
    search_fields = ("usuario__nome", "usuario__login")
    list_select_related = ("usuario",)


@admin.register(OperadorCozinha)
class OperadorAdmin(ConsultaAdmin):
    list_display = ("usuario", "funcao", "perfil_gerencial")
    list_filter = ("perfil_gerencial",)
    search_fields = ("usuario__nome", "usuario__login")
    list_select_related = ("usuario",)


@admin.register(Cliente)
class ClienteAdmin(ConsultaAdmin):
    fields = ("nome", "email")
    list_display = ("nome", "email")
    search_fields = ("nome", "email")


@admin.register(Mesa)
class MesaAdmin(CadastroAdmin):
    form = MesaForm
    list_display = ("identificacao", "tipo_local")
    list_filter = ("tipo_local",)
    search_fields = ("identificacao",)


@admin.register(Categoria)
class CategoriaAdmin(CadastroAdmin):
    form = CategoriaForm
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(ItemCardapio)
class ItemCardapioAdmin(CadastroAdmin):
    form = ItemCardapioForm
    list_display = ("nome", "categoria", "preco_atual", "disponivel")
    list_filter = ("categoria", "disponivel")
    list_select_related = ("categoria",)
    search_fields = ("nome", "descricao")


class LinhaPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    fields = (
        "numero_linha",
        "item_cardapio",
        "quantidade",
        "preco_unitario_registrado",
        "operador",
        "situacao_preparo",
        "inicio_preparo_em",
        "pronto_em",
    )
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(ConsultaAdmin):
    list_display = (
        "codigo",
        "mesa",
        "cliente",
        "garcom",
        "situacao_atual",
        "valor_total_registrado",
        "criado_em",
    )
    list_filter = ("situacao_atual", "origem")
    search_fields = ("codigo", "mesa__identificacao")
    list_select_related = ("mesa", "cliente", "garcom__usuario")
    inlines = (LinhaPedidoInline,)


@admin.register(ItemPedido)
class ItemPedidoAdmin(ConsultaAdmin):
    list_display = (
        "pedido",
        "numero_linha",
        "item_cardapio",
        "quantidade",
        "operador",
        "situacao_preparo",
    )
    list_filter = ("situacao_preparo",)
    list_select_related = ("pedido", "item_cardapio", "operador__usuario")
    search_fields = ("pedido__codigo", "item_cardapio__nome")
