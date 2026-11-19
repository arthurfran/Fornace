"""Indicadores calculados sobre a projeção SQL, sem duplicar totais de pedidos."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone as datetime_timezone
from decimal import Decimal
from django.conf import settings
from django.db import connection
from django.utils import timezone
from .identity import Identidade
from .domain import DomainError


def momento(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if timezone.is_naive(value):
        value = timezone.make_aware(value, datetime_timezone.utc)
    return value


def turno(hour):
    if 5 <= hour < 15:
        return "Almoço"
    if 15 <= hour < 18:
        return "Tarde"
    if 18 <= hour < 23:
        return "Jantar"
    return "Ceia"


def media(values):
    return round(sum(values) / len(values), 1) if values else None


class AnaliseProducao:
    def executar(self, request):
        Identidade.da_sessao(request.session).exigir_operador(gerencial=True)
        try:
            days = int(request.GET.get("dias", "30"))
        except ValueError:
            raise DomainError("Período inválido.", 400)
        if days not in (7, 30, 90):
            raise DomainError("Escolha 7, 30 ou 90 dias.", 400)
        now = timezone.now()
        cutoff, previous = now - timedelta(days=days), now - timedelta(days=2 * days)
        with connection.cursor() as cur:
            cur.execute(
                "SELECT * FROM cubo_producao WHERE entregue_em >= %s AND entregue_em <= %s",
                [previous, now],
            )
            keys = [d[0] for d in cur.description]
            rows = [dict(zip(keys, r)) for r in cur.fetchall()]
        for r in rows:
            for field in (
                "criado_em",
                "entregue_em",
                "inicio_preparo_em",
                "pronto_em",
                "atualizado_em",
            ):
                r[field] = momento(r[field])
        current = [r for r in rows if r["entregue_em"] >= cutoff]
        past = [r for r in rows if r["entregue_em"] < cutoff]
        # Tempos de pedido usam todas as suas linhas, mesmo no filtro de categoria.
        ready = {}
        for r in current:
            if r["pronto_em"]:
                ready[r["pedido_id"]] = max(
                    ready.get(r["pedido_id"], r["pronto_em"]), r["pronto_em"]
                )
        category, shift = request.GET.get("categoria"), request.GET.get("turno")

        def selected(items):
            return [
                r
                for r in items
                if (not category or r["categoria"] == category)
                and (
                    not shift
                    or turno(timezone.localtime(r["entregue_em"]).hour) == shift
                )
            ]

        current, past = selected(current), selected(past)
        orders = {r["pedido_id"]: r for r in current}
        previous_orders = {r["pedido_id"]: r for r in past}
        revenue = sum(
            (Decimal(str(r["total_pedido"])) for r in orders.values()), Decimal("0")
        )
        earlier_revenue = sum(
            (Decimal(str(r["total_pedido"])) for r in previous_orders.values()),
            Decimal("0"),
        )
        preparation, late, delivery = [], 0, []
        for key, r in orders.items():
            if key in ready:
                duration = (ready[key] - r["criado_em"]).total_seconds() / 60
                preparation.append(duration)
                late += duration > r["meta_preparo_min"]
                delivery.append((r["entregue_em"] - ready[key]).total_seconds() / 60)
        groups, matrix, rank = defaultdict(list), defaultdict(list), defaultdict(int)
        hours = {h: set() for h in range(24)}
        weekdays = {d: set() for d in range(7)}
        for r in current:
            local = timezone.localtime(r["entregue_em"])
            groups[r["categoria"]].append(r)
            matrix[(r["categoria"], turno(local.hour))].append(r)
            rank[r["item_nome"]] += r["quantidade"]
            hours[local.hour].add(r["pedido_id"])
            weekdays[local.weekday()].add(r["pedido_id"])

        def delta(actual, old):
            return float(round((actual - old) / old * 100, 1)) if old else None

        refreshed = max((r["atualizado_em"] for r in rows), default=None)
        return {
            "dias": days,
            "criterio": "Pedidos entregues, agrupados pela data de entrega.",
            "atualizado_em": refreshed.isoformat() if refreshed else None,
            "projecao": (
                "materializada"
                if connection.vendor == "postgresql"
                else "consulta em tempo real"
            ),
            "pedidos": len(orders),
            "unidades": sum(r["quantidade"] for r in current),
            "receita": str(revenue.quantize(Decimal(".01"))),
            "ticket_medio": (
                str((revenue / len(orders)).quantize(Decimal(".01")))
                if orders
                else "0.00"
            ),
            "variacao_pedidos_pct": delta(len(orders), len(previous_orders)),
            "variacao_receita_pct": delta(revenue, earlier_revenue),
            "preparo_medio_min": media(preparation),
            "atraso_preparo_pct": (
                round(late / len(preparation) * 100, 1) if preparation else None
            ),
            "entrega_media_min": media(delivery),
            "atraso_entrega_pct": (
                round(
                    sum(t > settings.SLA_ENTREGA_MIN for t in delivery)
                    / len(delivery)
                    * 100,
                    1,
                )
                if delivery and settings.SLA_ENTREGA_MIN
                else None
            ),
            "sla_entrega_min": settings.SLA_ENTREGA_MIN,
            "capacidade_hora": settings.CAPACIDADE_PEDIDOS_HORA,
            "categorias": [
                {
                    "nome": k,
                    "unidades": sum(r["quantidade"] for r in group),
                    "preparo_medio_min": media(
                        [
                            (r["pronto_em"] - r["inicio_preparo_em"]).total_seconds()
                            / 60
                            for r in group
                            if r["pronto_em"] and r["inicio_preparo_em"]
                        ]
                    ),
                }
                for k, group in groups.items()
            ],
            "matriz": [
                {
                    "categoria": c,
                    "turno": t,
                    "pedidos": len({r["pedido_id"] for r in group}),
                    "unidades": sum(r["quantidade"] for r in group),
                }
                for (c, t), group in matrix.items()
            ],
            "horas": [
                {"hora": h, "pedidos": len(ids), "media_dia": round(len(ids) / days, 2)}
                for h, ids in hours.items()
            ],
            "semana": [
                {
                    "dia": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][d],
                    "pedidos": len(ids),
                }
                for d, ids in weekdays.items()
            ],
            "ranking": [
                {"nome": k, "unidades": n}
                for k, n in sorted(rank.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
            ],
            "pedidos_detalhe": [
                {
                    "id": r["pedido_id"],
                    "codigo": r["codigo"],
                    "entregue_em": r["entregue_em"].isoformat(),
                    "total": str(r["total_pedido"]),
                }
                for r in sorted(
                    orders.values(), key=lambda r: r["entregue_em"], reverse=True
                )[:100]
            ],
        }
