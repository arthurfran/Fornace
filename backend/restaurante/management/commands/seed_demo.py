"""Carga explícita para desenvolvimento. Nenhuma credencial fixa no código."""

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

    def handle(self, *args, **options):
        password = os.getenv("DEMO_PASSWORD") or getpass(
            "Senha das contas de demonstração (8–64 caracteres): "
        )
        if not 8 <= len(password) <= 64:
            raise CommandError("Informe uma senha com 8 a 64 caracteres.")
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
                    user.definir_senha(password)
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
