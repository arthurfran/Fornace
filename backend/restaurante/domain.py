"""Objetos de valor e políticas independentes da interface HTTP."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


class DomainError(Exception):
    def __init__(self, message, status=409):
        self.message, self.status = message, status
        super().__init__(message)


@dataclass(frozen=True)
class Totais:
    subtotal: Decimal
    servico: Decimal
    total: Decimal

    @classmethod
    def das_linhas(cls, linhas):
        subtotal = sum(
            (Decimal(str(l["preco"])) * l["quantidade"] for l in linhas),
            Decimal("0.00"),
        )
        servico = (subtotal * Decimal("0.10")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return cls(subtotal, servico, subtotal + servico)


class PoliticaAtribuicao(ABC):
    @abstractmethod
    def escolher(self, elegiveis): ...


class MenorCarga(PoliticaAtribuicao):
    """Carga; nunca atribuído; última atribuição mais antiga; menor PK."""

    def escolher(self, elegiveis):
        if not elegiveis:
            raise DomainError(
                "Nenhum garçom ativo e em escala. O carrinho foi preservado."
            )
        return min(
            elegiveis,
            key=lambda g: (
                g.carga,
                g.ultima is not None,
                g.ultima.timestamp() if g.ultima else 0,
                g.pk,
            ),
        )
