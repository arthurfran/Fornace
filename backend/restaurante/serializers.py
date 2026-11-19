from .domain import Totais


def usuario(u):
    g, o = getattr(u, "garcom", None), getattr(u, "operador", None)
    return {
        "id": u.pk,
        "nome": u.nome,
        "login": u.login,
        "ativo": u.ativo,
        "administrador": u.administrador,
        "garcom": (
            {"id": g.pk, "setor": g.setor, "em_escala": g.em_escala} if g else None
        ),
        "operador": (
            {"id": o.pk, "funcao": o.funcao, "perfil_gerencial": o.perfil_gerencial}
            if o
            else None
        ),
    }


def identidade(i):
    if i.tipo == "usuario":
        return {"tipo": i.tipo, **usuario(i.pessoa)}
    if i.tipo == "cliente":
        return {
            "tipo": i.tipo,
            "id": i.pessoa.pk,
            "nome": i.pessoa.nome,
            "email": i.pessoa.email,
        }
    return {"tipo": "anonimo", "nome": "Visitante"}


def cardapio(i):
    return {
        "id": i.pk,
        "categoria": i.categoria.nome,
        "nome": i.nome,
        "descricao": i.descricao,
        "preco": str(i.preco_atual),
        "tempo": i.tempo_medio_preparo_min,
        "disponivel": i.disponivel,
        "foto": i.foto_uri,
    }


def carrinho(c):
    totals = Totais.das_linhas(c["linhas"])
    return {
        **c,
        "subtotal": str(totals.subtotal),
        "servico": str(totals.servico),
        "total": str(totals.total),
    }


def data(d):
    return d.isoformat() if d else None


def pedido(p):
    return {
        "id": p.pk,
        "codigo": p.codigo,
        "mesa": p.mesa.identificacao,
        "mesa_id": p.mesa_id,
        "cliente": p.cliente.nome if p.cliente else "Anônimo",
        "garcom": p.garcom.usuario.nome,
        "garcom_id": p.garcom_id,
        "origem": p.origem,
        "forma_atribuicao": p.forma_atribuicao,
        "situacao": p.situacao_atual,
        "criado_em": data(p.criado_em),
        "entregue_em": data(p.entregue_em),
        "meta_preparo_min": p.meta_preparo_min,
        "taxa_servico_pct": str(p.taxa_servico_pct),
        "total": str(p.valor_total_registrado),
        "itens": [
            {
                "id": i.pk,
                "linha": i.numero_linha,
                "nome": i.item_cardapio.nome,
                "categoria": i.item_cardapio.categoria.nome,
                "quantidade": i.quantidade,
                "observacoes": i.observacoes,
                "preco": str(i.preco_unitario_registrado),
                "tempo": i.tempo_preparo_registrado_min,
                "operador_id": i.operador_id,
                "operador": i.operador.usuario.nome if i.operador else None,
                "situacao": i.situacao_preparo,
                "inicio_em": data(i.inicio_preparo_em),
                "pronto_em": data(i.pronto_em),
            }
            for i in p.itens.all()
        ],
    }
