from django.db import models
from django.db.models import Q, F
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from .domain import DomainError


class Credencial(models.Model):
    """Reuso de comportamento sem criar tabela ou herança multi-table."""

    class Meta:
        abstract = True

    def definir_senha(self, senha):
        self.senha_hash = make_password(senha)

    def verificar_senha(self, senha):
        return check_password(senha, self.senha_hash)


class UsuarioManager(BaseUserManager):
    def create_user(self, login, password=None, **extra_fields):
        if not login:
            raise ValueError("Informe o login.")
        if not password or not 8 <= len(password) <= 64:
            raise ValueError("A senha deve ter de 8 a 64 caracteres.")
        usuario = self.model(login=login.strip().lower(), **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, login, password=None, **extra_fields):
        extra_fields["administrador"] = True
        extra_fields["ativo"] = True
        return self.create_user(login, password, **extra_fields)


class Usuario(AbstractBaseUser):
    """Conta da equipe integrada ao auth do Django, com as seis colunas do DER."""

    id_usuario = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=120)
    login = models.CharField(max_length=120, unique=True)
    password = models.CharField(max_length=255, db_column="senha_hash")
    ativo = models.BooleanField(default=True)
    administrador = models.BooleanField(default=False)
    # O DER não contém last_login; o Django não registra esse campo opcional.
    last_login = None

    objects = UsuarioManager()
    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = ["nome"]

    class Meta:
        db_table = "usuario"
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self):
        return self.nome

    @property
    def is_active(self):
        return self.ativo

    @property
    def is_staff(self):
        return self.administrador

    @property
    def is_superuser(self):
        return self.administrador

    @property
    def senha_hash(self):
        return self.password

    @senha_hash.setter
    def senha_hash(self, value):
        self.password = value

    def definir_senha(self, senha):
        self.set_password(senha)

    def verificar_senha(self, senha):
        return self.check_password(senha)

    def get_full_name(self):
        return self.nome

    def get_short_name(self):
        return self.nome.split()[0] if self.nome else self.login

    def has_perm(self, perm, obj=None):
        return self.ativo and self.administrador

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        return self.ativo and self.administrador

    def get_all_permissions(self, obj=None):
        if not self.ativo or not self.administrador:
            return set()
        from django.contrib.auth.models import Permission

        return {
            f"{app}.{codename}"
            for app, codename in Permission.objects.values_list(
                "content_type__app_label", "codename"
            )
        }


class Garcom(models.Model):
    id_garcom = models.BigAutoField(primary_key=True)
    usuario = models.OneToOneField(
        Usuario, on_delete=models.PROTECT, db_column="id_usuario", related_name="garcom"
    )
    setor = models.CharField(max_length=80)
    em_escala = models.BooleanField(default=False)

    class Meta:
        db_table = "garcom"
        verbose_name = "garçom"
        verbose_name_plural = "garçons"

    def __str__(self):
        return self.usuario.nome


class OperadorCozinha(models.Model):
    id_operador = models.BigAutoField(primary_key=True)
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        db_column="id_usuario",
        related_name="operador",
    )
    funcao = models.CharField(max_length=80)
    perfil_gerencial = models.BooleanField(default=False)

    class Meta:
        db_table = "operador_cozinha"
        verbose_name = "operador de cozinha"
        verbose_name_plural = "operadores de cozinha"

    def __str__(self):
        return self.usuario.nome


class Cliente(Credencial):
    id_cliente = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=120)
    email = models.EmailField(max_length=120, unique=True)
    senha_hash = models.CharField(max_length=255)

    class Meta:
        db_table = "cliente"
        verbose_name = "cliente"
        verbose_name_plural = "clientes"

    def __str__(self):
        return self.nome


class Mesa(models.Model):
    class Tipo(models.TextChoices):
        MESA = "MESA", "Mesa"
        BALCAO = "BALCAO", "Balcão"
        VARANDA = "VARANDA", "Varanda"

    id_mesa = models.BigAutoField(primary_key=True)
    identificacao = models.CharField(max_length=60, unique=True)
    tipo_local = models.CharField(max_length=10, choices=Tipo.choices)

    class Meta:
        db_table = "mesa"
        verbose_name = "mesa"
        verbose_name_plural = "mesas"
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo_local__in=["MESA", "BALCAO", "VARANDA"]),
                name="mesa_tipo_valido",
            )
        ]

    def __str__(self):
        return self.identificacao


class Categoria(models.Model):
    id_categoria = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "categoria"
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.nome


class ItemCardapio(models.Model):
    id_item_cardapio = models.BigAutoField(primary_key=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        db_column="id_categoria",
        related_name="itens",
    )
    nome = models.CharField(max_length=80)
    descricao = models.CharField(max_length=200)
    preco_atual = models.DecimalField(max_digits=12, decimal_places=2)
    tempo_medio_preparo_min = models.PositiveIntegerField()
    disponivel = models.BooleanField(default=True)
    foto_uri = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "item_cardapio"
        verbose_name = "item do cardápio"
        verbose_name_plural = "itens do cardápio"
        constraints = [
            models.CheckConstraint(
                condition=Q(preco_atual__gte=0), name="preco_cardapio_positivo"
            )
        ]

    def __str__(self):
        return self.nome


class PedidoQuerySet(models.QuerySet):
    def ativos(self):
        return self.exclude(situacao_atual="ENTREGUE")

    def delete(self):
        raise DomainError("Pedidos concluídos e ativos devem ser preservados.")


class Pedido(models.Model):
    class Situacao(models.TextChoices):
        RECEBIDO = "RECEBIDO", "Recebido"
        EM_PREPARO = "EM_PREPARO", "Em preparo"
        PRONTO = "PRONTO", "Pronto"
        ENTREGUE = "ENTREGUE", "Entregue"

    id_pedido = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=32, unique=True)
    mesa = models.ForeignKey(Mesa, on_delete=models.PROTECT, db_column="id_mesa")
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, db_column="id_cliente", null=True, blank=True
    )
    garcom = models.ForeignKey(
        Garcom, on_delete=models.PROTECT, db_column="id_garcom", related_name="pedidos"
    )
    origem = models.CharField(max_length=16)
    forma_atribuicao = models.CharField(max_length=12)
    situacao_atual = models.CharField(
        max_length=10, choices=Situacao.choices, default=Situacao.RECEBIDO
    )
    criado_em = models.DateTimeField()
    atribuido_em = models.DateTimeField()
    meta_preparo_min = models.PositiveIntegerField()
    taxa_servico_pct = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    valor_total_registrado = models.DecimalField(max_digits=12, decimal_places=2)
    entregue_em = models.DateTimeField(null=True, blank=True)
    objects = PedidoQuerySet.as_manager()

    class Meta:
        db_table = "pedido"
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-criado_em", "-id_pedido"]
        indexes = [
            models.Index(fields=["garcom", "situacao_atual"]),
            models.Index(fields=["criado_em"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(taxa_servico_pct=10), name="pedido_taxa_dez"
            ),
            models.CheckConstraint(
                condition=Q(valor_total_registrado__gte=0), name="pedido_total_positivo"
            ),
            models.CheckConstraint(
                condition=Q(
                    situacao_atual__in=["RECEBIDO", "EM_PREPARO", "PRONTO", "ENTREGUE"]
                ),
                name="pedido_situacao_valida",
            ),
            models.CheckConstraint(
                condition=(
                    Q(origem="SALAO", forma_atribuicao="PELO_SALAO")
                    | Q(
                        origem="AUTOATENDIMENTO",
                        forma_atribuicao__in=["MANUAL", "AUTOMATICA"],
                    )
                ),
                name="pedido_origem_atribuicao",
            ),
            models.CheckConstraint(
                condition=(
                    Q(situacao_atual="ENTREGUE", entregue_em__isnull=False)
                    | (~Q(situacao_atual="ENTREGUE") & Q(entregue_em__isnull=True))
                ),
                name="pedido_entrega_coerente",
            ),
            models.CheckConstraint(
                condition=Q(entregue_em__isnull=True)
                | Q(entregue_em__gte=F("criado_em")),
                name="pedido_entrega_apos_criacao",
            ),
        ]

    def recalcular_situacao(self, estados):
        if self.situacao_atual == self.Situacao.ENTREGUE:
            raise DomainError("Pedido entregue não pode ser alterado.")
        if not estados:
            raise DomainError("Pedido precisa de ao menos uma linha.")
        self.situacao_atual = (
            "PRONTO"
            if all(s == "PRONTO" for s in estados)
            else "RECEBIDO" if all(s == "AGUARDANDO" for s in estados) else "EM_PREPARO"
        )

    def entregar(self, garcom, agora):
        if garcom.pk != self.garcom_id:
            raise DomainError("Somente o garçom atribuído pode entregar.", 403)
        if self.situacao_atual != "PRONTO":
            raise DomainError("Todas as linhas precisam estar prontas.")
        self.situacao_atual, self.entregue_em = "ENTREGUE", agora

    def delete(self, *args, **kwargs):
        raise DomainError("Pedidos devem ser preservados.")

    def __str__(self):
        return self.codigo


class ItemPedidoQuerySet(models.QuerySet):
    def delete(self):
        raise DomainError("Linhas confirmadas devem ser preservadas.")


class ItemPedido(models.Model):
    objects = ItemPedidoQuerySet.as_manager()

    class Situacao(models.TextChoices):
        AGUARDANDO = "AGUARDANDO", "Aguardando"
        EM_PREPARO = "EM_PREPARO", "Em preparo"
        PRONTO = "PRONTO", "Pronto"

    id_item_pedido = models.BigAutoField(primary_key=True)
    pedido = models.ForeignKey(
        Pedido, on_delete=models.PROTECT, db_column="id_pedido", related_name="itens"
    )
    numero_linha = models.PositiveIntegerField()
    item_cardapio = models.ForeignKey(
        ItemCardapio, on_delete=models.PROTECT, db_column="id_item_cardapio"
    )
    quantidade = models.PositiveSmallIntegerField()
    observacoes = models.CharField(max_length=200, blank=True, null=True)
    preco_unitario_registrado = models.DecimalField(max_digits=12, decimal_places=2)
    tempo_preparo_registrado_min = models.PositiveIntegerField()
    operador = models.ForeignKey(
        OperadorCozinha,
        on_delete=models.PROTECT,
        db_column="id_operador",
        null=True,
        blank=True,
        related_name="itens",
    )
    situacao_preparo = models.CharField(
        max_length=10, choices=Situacao.choices, default=Situacao.AGUARDANDO
    )
    inicio_preparo_em = models.DateTimeField(null=True, blank=True)
    pronto_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "item_pedido"
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"
        ordering = ["numero_linha"]
        constraints = [
            models.UniqueConstraint(
                fields=["pedido", "numero_linha"], name="item_numero_por_pedido"
            ),
            models.CheckConstraint(
                condition=Q(numero_linha__gte=1), name="item_linha_positiva"
            ),
            models.CheckConstraint(
                condition=Q(quantidade__gte=1, quantidade__lte=20),
                name="item_quantidade_limite",
            ),
            models.CheckConstraint(
                condition=Q(preco_unitario_registrado__gte=0),
                name="item_preco_positivo",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        situacao_preparo="AGUARDANDO",
                        inicio_preparo_em__isnull=True,
                        pronto_em__isnull=True,
                    )
                    | Q(
                        situacao_preparo="EM_PREPARO",
                        operador__isnull=False,
                        inicio_preparo_em__isnull=False,
                        pronto_em__isnull=True,
                    )
                    | Q(
                        situacao_preparo="PRONTO",
                        operador__isnull=False,
                        inicio_preparo_em__isnull=False,
                        pronto_em__isnull=False,
                    )
                ),
                name="item_preparo_coerente",
            ),
            models.CheckConstraint(
                condition=Q(pronto_em__isnull=True)
                | Q(pronto_em__gte=F("inicio_preparo_em")),
                name="item_marcos_ordenados",
            ),
        ]

    def mudar_preparo(self, destino, operador, agora):
        if self.pedido.situacao_atual == "ENTREGUE":
            raise DomainError("Pedido entregue não pode ser alterado.")
        if self.operador_id and self.operador_id != operador.pk:
            raise DomainError("Esta linha pertence a outro operador.", 403)
        if destino == self.situacao_preparo:
            return
        if destino == "EM_PREPARO":
            self.operador = operador
            if self.situacao_preparo == "AGUARDANDO":
                self.inicio_preparo_em = agora
            self.pronto_em = None
        elif destino == "PRONTO":
            if self.situacao_preparo != "EM_PREPARO":
                raise DomainError("Inicie o preparo antes de concluir.")
            self.pronto_em = agora
        elif destino == "AGUARDANDO":
            self.inicio_preparo_em = self.pronto_em = None
        else:
            raise DomainError("Situação de preparo inválida.", 400)
        self.situacao_preparo = destino

    def delete(self, *args, **kwargs):
        raise DomainError("Linhas confirmadas devem ser preservadas.")

    def __str__(self):
        return f"{self.pedido.codigo} · linha {self.numero_linha}"
