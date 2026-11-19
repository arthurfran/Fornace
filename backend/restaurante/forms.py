"""Forms e ModelForms compartilhados pela API React e pelo admin do Django."""

from django import forms
from .domain import DomainError
from .locking import operacao_atomica
from .models import (
    Usuario,
    Cliente,
    Garcom,
    OperadorCozinha,
    Pedido,
    ItemPedido,
    ItemCardapio,
    Mesa,
    Categoria,
)


def validar(form):
    if not form.is_valid():
        errors = [
            f"{field}: {message}" if field != "__all__" else str(message)
            for field, messages in form.errors.items()
            for message in messages
        ]
        raise DomainError(" ".join(errors), 400)
    return form.cleaned_data


class BooleanoJSON(forms.BooleanField):
    def to_python(self, value):
        if value is None:
            return False
        if type(value) is not bool:
            raise forms.ValidationError("Informe verdadeiro ou falso.")
        return value


class LoginForm(forms.Form):
    tipo = forms.ChoiceField(choices=[("usuario", "Equipe"), ("cliente", "Cliente")])
    login = forms.CharField(max_length=120)
    senha = forms.CharField(
        min_length=8, max_length=64, strip=False, widget=forms.PasswordInput
    )

    def clean_login(self):
        return self.cleaned_data["login"].lower()


class CadastroClienteForm(forms.ModelForm):
    senha = forms.CharField(
        min_length=8, max_length=64, strip=False, widget=forms.PasswordInput
    )

    class Meta:
        model = Cliente
        fields = ["nome", "email", "senha"]

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def save(self, commit=True):
        cliente = super().save(commit=False)
        cliente.definir_senha(self.cleaned_data["senha"])
        if commit:
            cliente.save()
        return cliente


class CarrinhoForm(forms.Form):
    acao = forms.ChoiceField(
        choices=[(v, v) for v in ["mesa", "adicionar", "alterar", "remover", "limpar"]]
    )
    mesa_id = forms.IntegerField(min_value=1, required=False)
    item_id = forms.IntegerField(min_value=1, required=False)
    linha_id = forms.CharField(max_length=32, required=False)
    quantidade = forms.IntegerField(min_value=1, max_value=20, required=False)
    observacoes = forms.CharField(max_length=200, required=False)

    def clean(self):
        data = super().clean()
        required = {
            "mesa": ["mesa_id"],
            "adicionar": ["item_id", "quantidade"],
            "alterar": ["linha_id", "quantidade"],
            "remover": ["linha_id"],
            "limpar": [],
        }
        for name in required.get(data.get("acao"), []):
            if data.get(name) in (None, "") and name not in self.errors:
                self.add_error(name, "Este campo é obrigatório para esta ação.")
        return data


class ConfirmacaoForm(forms.Form):
    revisao = forms.RegexField(regex=r"^[a-f0-9]{32}$", max_length=32)
    garcom_id = forms.IntegerField(min_value=1, required=False)


class PreparoForm(forms.Form):
    situacao = forms.ChoiceField(choices=ItemPedido.Situacao.choices)


class EscalaForm(forms.Form):
    em_escala = BooleanoJSON(required=False)


class DisponibilidadeForm(forms.Form):
    disponivel = BooleanoJSON(required=False)


class UsuarioForm(forms.ModelForm):
    senha = forms.CharField(
        min_length=8,
        max_length=64,
        required=False,
        strip=False,
        widget=forms.PasswordInput,
        help_text="Na edição, deixe em branco para manter a senha.",
    )
    perfil_garcom = forms.BooleanField(required=False, label="Perfil de garçom")
    setor = forms.CharField(max_length=80, required=False)
    em_escala = forms.BooleanField(required=False, label="Em escala")
    perfil_operador = forms.BooleanField(
        required=False, label="Perfil de operador de cozinha"
    )
    funcao = forms.CharField(max_length=80, required=False, label="Função")
    perfil_gerencial = forms.BooleanField(
        required=False, label="Acesso às análises gerenciais"
    )

    class Meta:
        model = Usuario
        fields = [
            "nome",
            "login",
            "ativo",
            "administrador",
            "senha",
            "perfil_garcom",
            "setor",
            "em_escala",
            "perfil_operador",
            "funcao",
            "perfil_gerencial",
        ]

    def __init__(self, *args, autor=None, **kwargs):
        self.autor = autor
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["senha"].required = True
        elif not self.is_bound:
            garcom = getattr(self.instance, "garcom", None)
            operador = getattr(self.instance, "operador", None)
            self.initial.update(
                perfil_garcom=bool(garcom),
                setor=garcom.setor if garcom else "",
                em_escala=garcom.em_escala if garcom else False,
                perfil_operador=bool(operador),
                funcao=operador.funcao if operador else "",
                perfil_gerencial=operador.perfil_gerencial if operador else False,
            )

    @classmethod
    def da_api(cls, data, **kwargs):
        garcom, operador = data.get("garcom"), data.get("operador")
        for value in (garcom, operador):
            if value is not None and not isinstance(value, dict):
                raise DomainError("Perfil inválido.", 400)
        flags = [data.get("ativo", True), data.get("administrador", False)]
        if garcom is not None:
            flags.append(garcom.get("em_escala", False))
        if operador is not None:
            flags.append(operador.get("perfil_gerencial", False))
        if any(type(value) is not bool for value in flags):
            raise DomainError(
                "Informe os campos de seleção como verdadeiro ou falso.", 400
            )
        return cls(
            data={
                "nome": data.get("nome", ""),
                "login": data.get("login", ""),
                "senha": data.get("senha", ""),
                "ativo": data.get("ativo", True),
                "administrador": data.get("administrador", False),
                "perfil_garcom": garcom is not None,
                "setor": (garcom or {}).get("setor", ""),
                "em_escala": (garcom or {}).get("em_escala", False),
                "perfil_operador": operador is not None,
                "funcao": (operador or {}).get("funcao", ""),
                "perfil_gerencial": (operador or {}).get("perfil_gerencial", False),
            },
            **kwargs,
        )

    def clean_login(self):
        return self.cleaned_data["login"].lower()

    def clean(self):
        data = super().clean()
        if not any(
            data.get(k) for k in ("administrador", "perfil_garcom", "perfil_operador")
        ):
            raise forms.ValidationError(
                "Selecione ao menos um perfil ou a permissão de administrador."
            )
        if data.get("perfil_garcom") and not data.get("setor"):
            self.add_error("setor", "Informe o setor do garçom.")
        if data.get("perfil_operador") and not data.get("funcao"):
            self.add_error("funcao", "Informe a função do operador.")
        user = self.instance
        if user.pk:
            if (
                self.autor
                and self.autor.pk == user.pk
                and (not data.get("ativo") or not data.get("administrador"))
            ):
                raise forms.ValidationError(
                    "Outro administrador deve retirar seu acesso administrativo."
                )
            if not data.get("ativo"):
                if Pedido.objects.ativos().filter(garcom__usuario=user).exists():
                    raise forms.ValidationError(
                        "Conclua os pedidos do garçom antes de desativar o usuário."
                    )
                if (
                    ItemPedido.objects.filter(operador__usuario=user)
                    .exclude(pedido__situacao_atual="ENTREGUE")
                    .exists()
                ):
                    raise forms.ValidationError(
                        "Conclua os pedidos com itens deste operador antes de desativar o usuário."
                    )
            if (
                not data.get("perfil_garcom")
                and Pedido.objects.filter(garcom__usuario=user).exists()
            ):
                raise forms.ValidationError(
                    "O perfil de garçom é referenciado por pedidos e deve ser preservado."
                )
            if (
                not data.get("perfil_operador")
                and ItemPedido.objects.filter(operador__usuario=user).exists()
            ):
                raise forms.ValidationError(
                    "O perfil de operador é referenciado por itens e deve ser preservado."
                )
        return data

    def salvar_perfis(self):
        data, user = self.cleaned_data, self.instance
        if data.get("perfil_garcom"):
            Garcom.objects.update_or_create(
                usuario=user,
                defaults={
                    "setor": data["setor"],
                    "em_escala": data.get("em_escala", False) and user.ativo,
                },
            )
        else:
            Garcom.objects.filter(usuario=user).delete()
        if data.get("perfil_operador"):
            OperadorCozinha.objects.update_or_create(
                usuario=user,
                defaults={
                    "funcao": data["funcao"],
                    "perfil_gerencial": data.get("perfil_gerencial", False),
                },
            )
        else:
            OperadorCozinha.objects.filter(usuario=user).delete()

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("senha"):
            user.set_password(self.cleaned_data["senha"])
        if commit:
            with operacao_atomica():
                user.save()
                self.salvar_perfis()
        return user


class ItemCardapioForm(forms.ModelForm):
    class Meta:
        model = ItemCardapio
        fields = [
            "categoria",
            "nome",
            "descricao",
            "preco_atual",
            "tempo_medio_preparo_min",
            "disponivel",
            "foto_uri",
        ]


class MesaForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = ["identificacao", "tipo_local"]


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome"]
