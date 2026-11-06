"""Patrón Specification (ADR-012).

Cada regla es una clase pequeña; se combinan con & (AND), | (OR) y ~ (NOT).
Cada una explica por qué falla (motivos) para responder 422 con detalle.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from src.domain.entidades import ContextoOperacion
from src.domain.valores import Dinero

UMBRAL_BENEFICIO = Dinero(Decimal("1500"))


class Specification(ABC):
    descripcion: str = ""

    @abstractmethod
    def is_satisfied_by(self, ctx: ContextoOperacion) -> bool: ...

    def motivos_fallo(self, ctx: ContextoOperacion) -> list[str]:
        return [] if self.is_satisfied_by(ctx) else [self.descripcion or type(self).__name__]

    def __and__(self, otra: Specification) -> Specification:
        return AndSpecification(self, otra)

    def __or__(self, otra: Specification) -> Specification:
        return OrSpecification(self, otra)

    def __invert__(self) -> Specification:
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, izq: Specification, der: Specification):
        self.izq, self.der = izq, der
        self.descripcion = f"({izq.descripcion} AND {der.descripcion})"

    def is_satisfied_by(self, ctx):
        return self.izq.is_satisfied_by(ctx) and self.der.is_satisfied_by(ctx)

    def motivos_fallo(self, ctx):
        return self.izq.motivos_fallo(ctx) + self.der.motivos_fallo(ctx)


class OrSpecification(Specification):
    def __init__(self, izq: Specification, der: Specification):
        self.izq, self.der = izq, der
        self.descripcion = f"({izq.descripcion} OR {der.descripcion})"

    def is_satisfied_by(self, ctx):
        return self.izq.is_satisfied_by(ctx) or self.der.is_satisfied_by(ctx)

    def motivos_fallo(self, ctx):
        if self.is_satisfied_by(ctx):
            return []
        return [self.descripcion]


class NotSpecification(Specification):
    def __init__(self, interna: Specification):
        self.interna = interna
        self.descripcion = f"NOT {interna.descripcion}"

    def is_satisfied_by(self, ctx):
        return not self.interna.is_satisfied_by(ctx)


# ---- Specifications simples (hojas) -------------------------------------
class AlumnoActivo(Specification):
    descripcion = "alumno activo"

    def is_satisfied_by(self, ctx):
        return ctx.alumno.activo


class TieneLineas(Specification):
    descripcion = "solicitud con al menos un renglón"

    def is_satisfied_by(self, ctx):
        return len(ctx.solicitud.lineas) > 0


class SolicitudAutorizada(Specification):
    descripcion = "solicitud autorizada"

    def is_satisfied_by(self, ctx):
        return ctx.solicitud.autorizado


class AlumnoPreferente(Specification):
    descripcion = "alumno preferente"

    def is_satisfied_by(self, ctx):
        return ctx.alumno.es_preferente


class TotalMinimo(Specification):
    def __init__(self, minimo: Dinero = UMBRAL_BENEFICIO):
        self.minimo = minimo
        self.descripcion = f"total >= {minimo.monto} MXN"

    def is_satisfied_by(self, ctx):
        return ctx.solicitud.total.monto >= self.minimo.monto


class PromocionActiva(Specification):
    descripcion = "promoción activa"

    def is_satisfied_by(self, ctx):
        return ctx.solicitud.promocion_activa


class ProgramasHabilitados(Specification):
    descripcion = "todos los programas habilitados"

    def is_satisfied_by(self, ctx):
        return all(
            ctx.programas.get(linea.programa_id) is not None
            and ctx.programas[linea.programa_id].habilitado
            for linea in ctx.solicitud.lineas
        )


class CupoSuficiente(Specification):
    descripcion = "cupo suficiente en todos los programas"

    def is_satisfied_by(self, ctx):
        for programa_id, lugares in ctx.solicitud.lugares_por_programa().items():
            programa = ctx.programas.get(programa_id)
            if programa is None or not programa.cupo.hay_lugar(lugares):
                return False
        return True


class CalificacionAprobatoria(Specification):
    descripcion = "calificación final >= 70 (RB-07)"

    def is_satisfied_by(self, ctx):
        cal = ctx.solicitud.calificacion_final
        return cal is not None and cal.aprueba()


class AsistenciaMinima(Specification):
    descripcion = "asistencia >= 80% (RB-06)"

    def is_satisfied_by(self, ctx):
        asis = ctx.solicitud.asistencia
        return asis is not None and asis.cumple_minimo()


# ---- Composiciones de negocio ------------------------------------------
def puede_procesarse() -> Specification:
    """Regla del maestro: actor activo AND con renglones AND autorizada. (RB-01/RB-14)"""
    return AlumnoActivo() & TieneLineas() & SolicitudAutorizada()


def beneficio_referencia() -> Specification:
    """Regla del maestro: preferente AND total >= 1500 AND NOT promoción activa."""
    return AlumnoPreferente() & TotalMinimo() & ~PromocionActiva()


def puede_aceptarse() -> Specification:
    """Regla propia de EduTech: lo anterior + programas habilitados (RB-02, RES-01)."""
    return puede_procesarse() & ProgramasHabilitados()


def cumple_certificacion() -> Specification:
    """RB-08: calificación >= 70 AND asistencia >= 80%."""
    return CalificacionAprobatoria() & AsistenciaMinima()
