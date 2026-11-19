"""Carga inicial de mesas, cardápio e equipe de demonstração."""

import json
from getpass import getpass
import os
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from restaurante.models import (
    Usuario,
    Garcom,
    OperadorCozinha,
    Mesa,
    Categoria,
    ItemCardapio,
)
from restaurante.locking import operacao_atomica


class Command(BaseCommand):
    help = "Cria cardápio, mesas e contas demonstrativas; solicita a senha ou lê DEMO_PASSWORD."

    def add_arguments(self, parser):
        parser.add_argument(
            "--render",
            action="store_true",
            help="Lê ADMIN_PASSWORD e DEMO_PASSWORD, sem solicitar entrada.",
        )

    def handle(self, *args, **options):
        password = os.getenv("DEMO_PASSWORD", "")
        if not options["render"] and not password:
            password = getpass("Senha das contas de demonstração (8–64 caracteres): ")
        if not 8 <= len(password) <= 64:
            raise CommandError("Informe DEMO_PASSWORD com 8 a 64 caracteres.")
        admin_password = (
            os.getenv("ADMIN_PASSWORD", "") if options["render"] else password
        )
        if options["render"] and (
            not 8 <= len(admin_password) <= 64 or admin_password == password
        ):
            raise CommandError(
                "Defina ADMIN_PASSWORD com 8 a 64 caracteres, diferente de DEMO_PASSWORD."
            )
        with operacao_atomica():
            for login, nome, admin, waiter, operator in (
                ("admin", "Administrador", True, False, False),
                ("teo", "Téo Marchetti", False, True, False),
                ("iara", "Iara Nogueira", False, True, False),
                ("marina", "Marina Prado", False, False, True),
                ("caio", "Caio Vasques", False, False, True),
                ("duplo", "Atendimento e cozinha", False, True, True),
            ):
                user, created = Usuario.objects.get_or_create(
                    login=login, defaults={"nome": nome, "administrador": admin}
                )
                if created:
                    user.definir_senha(admin_password if admin else password)
                    user.save()
                    if waiter:
                        Garcom.objects.create(
                            usuario=user, setor="Salão", em_escala=True
                        )
                    if operator:
                        OperadorCozinha.objects.create(
                            usuario=user,
                            funcao="Preparo",
                            perfil_gerencial=login == "marina",
                        )
            for n in range(1, 13):
                Mesa.objects.get_or_create(
                    identificacao=f"Mesa {n:02}", defaults={"tipo_local": "MESA"}
                )
            for label, tipo in (("Balcão", "BALCAO"), ("Varanda", "VARANDA")):
                Mesa.objects.get_or_create(
                    identificacao=label, defaults={"tipo_local": tipo}
                )
            path = Path(__file__).resolve().parents[2] / "menu_seed.json"
            for item in json.loads(path.read_text(encoding="utf-8")):
                category, _ = Categoria.objects.get_or_create(nome=item["cat"])
                ItemCardapio.objects.get_or_create(
                    nome=item["name"],
                    defaults={
                        "categoria": category,
                        "descricao": item["desc"],
                        "preco_atual": item["price"],
                        "tempo_medio_preparo_min": item["tempo"],
                        "foto_uri": "/" + item["photo"],
                        "disponivel": True,
                    },
                )
        self.stdout.write(
            self.style.SUCCESS(
                "Demonstração criada. Contas existentes não tiveram a senha alterada."
            )
        )
