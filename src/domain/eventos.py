"""Domain Events. El Service Layer los publica tras confirmar la transacción (ADR-007)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class EventoDominio:
    solicitud_id: str
    ocurrido_en: datetime = field(default_factory=_ahora)

    @property
    def nombre(self) -> str:
        return type(self).__name__


@dataclass(frozen=True)
class SolicitudCreada(EventoDominio):
    pass


@dataclass(frozen=True)
class SolicitudAceptada(EventoDominio):
    pass


@dataclass(frozen=True)
class InscripcionConfirmada(EventoDominio):  # equivale a PagoRecibido (U5)
    pass


@dataclass(frozen=True)
class SolicitudFinalizada(EventoDominio):
    pass


@dataclass(frozen=True)
class SolicitudCancelada(EventoDominio):
    pass


@dataclass(frozen=True)
class CupoAgotadoEvento(EventoDominio):
    programa_id: str = ""


@dataclass(frozen=True)
class CertificacionEvaluada(EventoDominio):
    elegible: bool = False
