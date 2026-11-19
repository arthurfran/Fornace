from contextlib import contextmanager
from django.db import connection, transaction


@contextmanager
def operacao_atomica():
    """Serializa alterações que disputam escala/carga/responsabilidade.

    PostgreSQL: advisory lock transacional compartilhado por todos os serviços.
    SQLite local: BEGIN IMMEDIATE, configurado no backend do Django.
    O bloqueio global é deliberado para o porte desta iteração.
    """
    with transaction.atomic():
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [3304001])
        yield
