"""Value Objects inmutables (ADR-003, ADR-010)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.domain.excepciones import CantidadInvalida, CupoAgotado

UMBRAL_CALIFICACION = Decimal("70")  # RB-07
UMBRAL_ASISTENCIA = Decimal("80")  # RB-06


@dataclass(frozen=True)
class Dinero:
    """Importe en MXN. Usa Decimal, nunca float. No puede ser negativo (Precio, U3)."""

    monto: Decimal
    moneda: str = "MXN"

    def __post_init__(self):
        object.__setattr__(self, "monto", Decimal(str(self.monto)))
        if self.monto < 0:
            raise CantidadInvalida("El importe no puede ser negativo")

    def por(self, cantidad: int) -> Dinero:
        return Dinero(self.monto * cantidad, self.moneda)

    def __add__(self, otro: Dinero) -> Dinero:
        return Dinero(self.monto + otro.monto, self.moneda)

    @classmethod
    def cero(cls) -> Dinero:
        return cls(Decimal("0"))


@dataclass(frozen=True)
class Calificacion:
    """0..100. aprueba() si >= 70 (RB-07)."""

    valor: Decimal

    def __post_init__(self):
        object.__setattr__(self, "valor", Decimal(str(self.valor)))
        if not (Decimal("0") <= self.valor <= Decimal("100")):
            raise CantidadInvalida("La calificación debe estar entre 0 y 100")

    def aprueba(self) -> bool:
        return self.valor >= UMBRAL_CALIFICACION


@dataclass(frozen=True)
class PorcentajeAsistencia:
    """0..100. cumple_minimo() si >= 80 (RB-06)."""

    valor: Decimal

    def __post_init__(self):
        object.__setattr__(self, "valor", Decimal(str(self.valor)))
        if not (Decimal("0") <= self.valor <= Decimal("100")):
            raise CantidadInvalida("El porcentaje de asistencia debe estar entre 0 y 100")

    def cumple_minimo(self) -> bool:
        return self.valor >= UMBRAL_ASISTENCIA


@dataclass(frozen=True)
class Cupo:
    """Capacidad y lugares ocupados. Inmutable: ocupar/liberar devuelven otro Cupo (RB-02)."""

    capacidad: int
    ocupados: int = 0
    programa_id: str = ""

    def __post_init__(self):
        if self.capacidad < 0 or self.ocupados < 0 or self.ocupados > self.capacidad:
            raise CantidadInvalida("Cupo inconsistente: ocupados debe estar entre 0 y capacidad")

    @property
    def disponibles(self) -> int:
        return self.capacidad - self.ocupados

    def hay_lugar(self, cantidad: int = 1) -> bool:
        return self.disponibles >= cantidad

    def ocupar(self, cantidad: int = 1) -> Cupo:
        if cantidad <= 0:
            raise CantidadInvalida("La cantidad debe ser mayor a cero")
        if not self.hay_lugar(cantidad):
            raise CupoAgotado(self.programa_id, cantidad, self.disponibles)
        return Cupo(self.capacidad, self.ocupados + cantidad, self.programa_id)

    def liberar(self, cantidad: int = 1) -> Cupo:
        return Cupo(self.capacidad, max(0, self.ocupados - cantidad), self.programa_id)


@dataclass(frozen=True)
class LineaSolicitud:
    """Un renglón: programa, cantidad de lugares y precio fijado al solicitar (ADR-010)."""

    programa_id: str
    cantidad: int
    precio_unitario: Dinero

    def __post_init__(self):
        if not isinstance(self.cantidad, int) or self.cantidad <= 0:
            raise CantidadInvalida("La cantidad de cada renglón debe ser un entero mayor a cero")

    @property
    def subtotal(self) -> Dinero:
        return self.precio_unitario.por(self.cantidad)
