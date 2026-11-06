"""State Machine de la Solicitud de inscripción (ADR-011).

Equivalencia con U3 (EstadoInscripción):
  SOLICITADA  = Pendiente (sin aprobar ni pagar)
  ACEPTADA    = Control Escolar aprobó y reservó cupo (SUP-11), falta el pago
  INSCRITA    = Confirmada (pago recibido, RB-03)
  FINALIZADA  = el grupo terminó; ya puede evaluarse certificación (SUP-10)
  CANCELADA   = Cancelada / GrupoCancelado (RB-10)
"""
from __future__ import annotations

from enum import Enum

from src.domain.excepciones import TransicionInvalida


class EstadoSolicitud(str, Enum):
    SOLICITADA = "SOLICITADA"
    ACEPTADA = "ACEPTADA"
    INSCRITA = "INSCRITA"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"


class Accion(str, Enum):
    APROBAR = "aprobar"
    INSCRIBIR = "inscribir"  # registrar el pago
    COMPLETAR = "completar"
    CANCELAR = "cancelar"


E = EstadoSolicitud
A = Accion

TRANSICIONES: dict[tuple[EstadoSolicitud, Accion], EstadoSolicitud] = {
    (E.SOLICITADA, A.APROBAR): E.ACEPTADA,
    (E.ACEPTADA, A.INSCRIBIR): E.INSCRITA,
    (E.INSCRITA, A.COMPLETAR): E.FINALIZADA,
    (E.SOLICITADA, A.CANCELAR): E.CANCELADA,
    (E.ACEPTADA, A.CANCELAR): E.CANCELADA,
    (E.INSCRITA, A.CANCELAR): E.CANCELADA,  # RB-10: grupo cancelado -> reembolso
}

ESTADOS_QUE_RETIENEN_CUPO = {E.ACEPTADA, E.INSCRITA, E.FINALIZADA}


class MaquinaEstados:
    """Tabla de transiciones explícita; nada de strings sueltos ni ifs dispersos."""

    @staticmethod
    def siguiente(estado: EstadoSolicitud, accion: Accion) -> EstadoSolicitud:
        try:
            return TRANSICIONES[(estado, accion)]
        except KeyError:
            raise TransicionInvalida(estado.value, accion.value) from None

    @staticmethod
    def permitidas(estado: EstadoSolicitud) -> list[Accion]:
        return [a for (e, a) in TRANSICIONES if e == estado]
