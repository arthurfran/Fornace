"""Atualiza o painel do PostgreSQL sem um processo periódico no Render."""

from importlib import import_module

from django.db import migrations

SELECT = import_module(".0002_projecao_e_cache", __package__).SELECT


def usar_view(apps, editor):
    if editor.connection.vendor == "postgresql":
        editor.execute("DROP MATERIALIZED VIEW cubo_producao")
        editor.execute("CREATE VIEW cubo_producao AS " + SELECT)


def restaurar_materializada(apps, editor):
    if editor.connection.vendor == "postgresql":
        editor.execute("DROP VIEW cubo_producao")
        editor.execute("CREATE MATERIALIZED VIEW cubo_producao AS " + SELECT)
        editor.execute(
            "CREATE UNIQUE INDEX cubo_producao_linha ON cubo_producao(linha_id)"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("restaurante", "0004_alter_categoria_options_alter_cliente_options_and_more"),
    ]
    operations = [migrations.RunPython(usar_view, restaurar_materializada)]
