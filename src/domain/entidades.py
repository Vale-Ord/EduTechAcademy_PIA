"""Entidades y Aggregate Roots usados en la implementación del PIA.

Aggregates (se relacionan solo por identificador, ADR-002):
  - Alumno (Estudiante en U3)
  - Programa (Curso/Grupo con Cupo; recurso del maestro)
  - Solicitud (raíz de la inscripción: líneas + estado + resultado académico)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from src.domain import eventos as ev
from src.domain.estados import Accion, EstadoSolicitud, MaquinaEstados
from src.domain.excepciones import CantidadInvalida
from src.domain.valores import (
    Calificacion,
    Cupo,
    Dinero,
    LineaSolicitud,
    PorcentajeAsistencia,
)


@dataclass
class Alumno:
    id: str
    nombre: str
    es_preferente: bool = False
    activo: bool = True
    ciudad: str = ""


@dataclass
class Programa:
    id: str
    descripcion: str
    precio: Dinero
    cupo: Cupo
    habilitado: bool = True

    def ocupar(self, cantidad: int) -> None:
        self.cupo = self.cupo.ocupar(cantidad)

    def liberar(self, cantidad: int) -> None:
        self.cupo = self.cupo.liberar(cantidad)


@dataclass
class Solicitud:
    """Aggregate Root. Todo cambio de estado pasa por la máquina de estados."""

    id: str
    alumno_id: str
    fecha_solicitud: date
    lineas: list[LineaSolicitud] = field(default_factory=list)
    estado: EstadoSolicitud = EstadoSolicitud.SOLICITADA
    promocion_activa: bool = False
    autorizado: bool = True
    referencia: str = ""
    calificacion_final: Calificacion | None = None
    asistencia: PorcentajeAsistencia | None = None
    _eventos: list[ev.EventoDominio] = field(default_factory=list, repr=False)

    # ---- consultas -------------------------------------------------------
    @property
    def total(self) -> Dinero:
        total = Dinero.cero()
        for linea in self.lineas:
            total = total + linea.subtotal
        return total

    def lugares_por_programa(self) -> dict[str, int]:
        lugares: dict[str, int] = {}
        for linea in self.lineas:
            lugares[linea.programa_id] = lugares.get(linea.programa_id, 0) + linea.cantidad
        return lugares

    def acciones_permitidas(self) -> list[Accion]:
        return MaquinaEstados.permitidas(self.estado)

    # ---- comandos (State Machine) ---------------------------------------
    def verificar(self, accion: Accion) -> EstadoSolicitud:
        """Lanza TransicionInvalida si la acción no procede; no modifica nada."""
        return MaquinaEstados.siguiente(self.estado, accion)

    def aplicar(self, accion: Accion) -> None:
        nuevo = self.verificar(accion)
        self.estado = nuevo
        evento = {
            Accion.APROBAR: ev.SolicitudAceptada,
            Accion.INSCRIBIR: ev.InscripcionConfirmada,
            Accion.COMPLETAR: ev.SolicitudFinalizada,
            Accion.CANCELAR: ev.SolicitudCancelada,
        }[accion]
        self._eventos.append(evento(solicitud_id=self.id))

    def registrar_resultado(self, calificacion: Decimal, asistencia: Decimal) -> None:
        """US-09/US-10: resultado académico de la inscripción (SUP-09, SUP-10)."""
        if self.estado not in (EstadoSolicitud.INSCRITA, EstadoSolicitud.FINALIZADA):
            raise CantidadInvalida(
                "Solo se registra resultado académico con la inscripción confirmada"
            )
        self.calificacion_final = Calificacion(calificacion)
        self.asistencia = PorcentajeAsistencia(asistencia)

    def registrar_evento(self, evento: ev.EventoDominio) -> None:
        self._eventos.append(evento)

    def extraer_eventos(self) -> list[ev.EventoDominio]:
        eventos, self._eventos = self._eventos, []
        return eventos


@dataclass
class ContextoOperacion:
    """Lo que las Specifications necesitan evaluar: la solicitud y los datos que referencia."""

    solicitud: Solicitud
    alumno: Alumno
    programas: dict[str, Programa]
