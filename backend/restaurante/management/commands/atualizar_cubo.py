import time
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, close_old_connections


class Command(BaseCommand):
    help = "Atualiza o cubo PostgreSQL; --continuo executa periodicamente. SQLite usa VIEW normal."

    def add_arguments(self, parser):
        parser.add_argument("--continuo", action="store_true")
        parser.add_argument("--intervalo", type=int, default=300)

    def handle(self, *args, **options):
        if options["intervalo"] < 10:
            raise CommandError("Intervalo mínimo: 10 segundos.")
        if connection.vendor != "postgresql":
            self.stdout.write("SQLite: a projeção é consultada em tempo real.")
            return
        while True:
            with connection.cursor() as cursor:
                cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cubo_producao")
            self.stdout.write("Cubo atualizado.", ending="\n")
            self.stdout.flush()
            if not options["continuo"]:
                break
            close_old_connections()
            time.sleep(options["intervalo"])
