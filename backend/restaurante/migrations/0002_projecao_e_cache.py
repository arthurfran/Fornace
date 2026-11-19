from django.db import migrations
from django.core.management import call_command

SELECT = """SELECT i.id_item_pedido AS linha_id, p.id_pedido AS pedido_id, p.codigo,
 p.criado_em, p.entregue_em, p.valor_total_registrado AS total_pedido, p.meta_preparo_min,
 i.quantidade, i.preco_unitario_registrado, i.inicio_preparo_em, i.pronto_em,
 i.id_operador AS operador_id, c.nome AS categoria, m.nome AS item_nome,
 CURRENT_TIMESTAMP AS atualizado_em
 FROM item_pedido i JOIN pedido p ON p.id_pedido = i.id_pedido
 JOIN item_cardapio m ON m.id_item_cardapio = i.id_item_cardapio
 JOIN categoria c ON c.id_categoria = m.id_categoria"""


def criar(apps, editor):
    call_command(
        "createcachetable",
        "cache_entries",
        database=editor.connection.alias,
        verbosity=0,
    )
    if editor.connection.vendor == "postgresql":
        editor.execute("CREATE MATERIALIZED VIEW cubo_producao AS " + SELECT)
        editor.execute(
            "CREATE UNIQUE INDEX cubo_producao_linha ON cubo_producao(linha_id)"
        )
    else:
        editor.execute("CREATE VIEW cubo_producao AS " + SELECT)


def remover(apps, editor):
    editor.execute(
        "DROP "
        + ("MATERIALIZED VIEW" if editor.connection.vendor == "postgresql" else "VIEW")
        + " IF EXISTS cubo_producao"
    )
    editor.execute("DROP TABLE IF EXISTS cache_entries")


class Migration(migrations.Migration):
    dependencies = [("restaurante", "0001_initial")]
    operations = [migrations.RunPython(criar, remover)]
