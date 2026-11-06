"""Application Service: orquesta casos de uso (ADR-001: Domain Model + Service Layer)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from src.application.puertos import (
    AlumnoRepository,
    ProgramaRepository,
    Publicador,
    SolicitudRepository,
    UnidadDeTrabajo,
)
from src.domain import eventos as ev
from src.domain.entidades import Alumno, ContextoOperacion, Programa, Solicitud
from src.domain.especificaciones import (
    beneficio_referencia,
    cumple_certificacion,
    puede_aceptarse,
    puede_procesarse,
)
from src.domain.estados import Accion, EstadoSolicitud, ESTADOS_QUE_RETIENEN_CUPO
from src.domain.excepciones import (
    CantidadInvalida,
    CupoAgotado,
    NoEncontrado,
    ReglaNoCumplida,
)
from src.domain.valores import LineaSolicitud


class _NullUoW:
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


@dataclass
class ResultadoValidacion:
    solicitud_id: str
    cumple: bool
    motivos: list[str] = field(default_factory=list)


@dataclass
class ResultadoBeneficio:
    solicitud_id: str
    aplica: bool
    total: Decimal
    motivos: list[str] = field(default_factory=list)


@dataclass
class ResultadoCertificacion:
    solicitud_id: str
    estado: str  # Pendiente | Elegible | No elegible
    motivo: str | None = None  # Calificación | Asistencia | Ambos


class SolicitudService:
    def __init__(
        self,
        alumnos: AlumnoRepository,
        programas: ProgramaRepository,
        solicitudes: SolicitudRepository,
        publicador: Publicador,
        uow: UnidadDeTrabajo | None = None,
    ):
        self.alumnos = alumnos
        self.programas = programas
        self.solicitudes = solicitudes
        self.publicador = publicador
        self.uow = uow or _NullUoW()

    # ---- helpers ---------------------------------------------------------
    def _solicitud(self, solicitud_id: str) -> Solicitud:
        sol = self.solicitudes.obtener(solicitud_id)
        if sol is None:
            raise NoEncontrado(f"Solicitud {solicitud_id} no existe")
        return sol

    def _contexto(self, sol: Solicitud) -> ContextoOperacion:
        alumno = self.alumnos.obtener(sol.alumno_id)
        if alumno is None:
            raise NoEncontrado(f"Alumno {sol.alumno_id} no existe")
        programas = {}
        for linea in sol.lineas:
            programa = self.programas.obtener(linea.programa_id)
            if programa is not None:
                programas[linea.programa_id] = programa
        return ContextoOperacion(sol, alumno, programas)

    def _cerrar(self, sol: Solicitud) -> Solicitud:
        """Guarda, confirma la transacción y solo entonces publica eventos (ADR-007)."""
        self.solicitudes.guardar(sol)
        eventos = sol.extraer_eventos()
        self.uow.commit()
        self.publicador.publicar(eventos)
        return sol

    # ---- consultas -------------------------------------------------------
    def listar_programas(self, solo_habilitados: bool = False) -> list[Programa]:  # US-01
        return self.programas.listar(solo_habilitados)

    def obtener_programa(self, programa_id: str) -> Programa:
        programa = self.programas.obtener(programa_id)
        if programa is None:
            raise NoEncontrado(f"Programa {programa_id} no existe")
        return programa

    def obtener(self, solicitud_id: str) -> Solicitud:
        return self._solicitud(solicitud_id)

    def listar(self, alumno_id: str | None = None, estado: str | None = None) -> list[Solicitud]:
        return self.solicitudes.listar(alumno_id, estado)  # US-03, US-12, US-15

    def eventos_de(self, solicitud_id: str) -> list[ev.EventoDominio]:
        self._solicitud(solicitud_id)
        return self.publicador.listar(solicitud_id)

    # ---- reglas (Specification) -----------------------------------------
    def validar(self, solicitud_id: str) -> ResultadoValidacion:
        sol = self._solicitud(solicitud_id)
        ctx = self._contexto(sol)
        spec = puede_procesarse()
        return ResultadoValidacion(sol.id, spec.is_satisfied_by(ctx), spec.motivos_fallo(ctx))

    def evaluar_beneficio(self, solicitud_id: str) -> ResultadoBeneficio:
        sol = self._solicitud(solicitud_id)
        ctx = self._contexto(sol)
        spec = beneficio_referencia()
        return ResultadoBeneficio(
            sol.id, spec.is_satisfied_by(ctx), sol.total.monto, spec.motivos_fallo(ctx)
        )

    # ---- comandos --------------------------------------------------------
    def crear(
        self,
        alumno_id: str,
        lineas: list[tuple[str, int]],
        promocion_activa: bool = False,
        autorizado: bool = True,
        referencia: str = "",
        hoy: date | None = None,
    ) -> Solicitud:
        """US-02 / US-18. Fija el precio vigente al solicitar (ADR-010)."""
        if self.alumnos.obtener(alumno_id) is None:
            raise NoEncontrado(f"Alumno {alumno_id} no existe")
        if not lineas:
            raise ReglaNoCumplida(["la solicitud debe tener al menos un renglón"])
        renglones = []
        for programa_id, cantidad in lineas:
            programa = self.obtener_programa(programa_id)
            renglones.append(LineaSolicitud(programa_id, cantidad, programa.precio))
        sol = Solicitud(
            id=self.solicitudes.siguiente_id(),
            alumno_id=alumno_id,
            fecha_solicitud=hoy or date.today(),
            lineas=renglones,
            promocion_activa=promocion_activa,
            autorizado=autorizado,
            referencia=referencia,
        )
        sol.registrar_evento(ev.SolicitudCreada(solicitud_id=sol.id))
        self.solicitudes.agregar(sol)
        return self._cerrar(sol)

    def aprobar(self, solicitud_id: str) -> Solicitud:
        """SOLICITADA -> ACEPTADA. Valida reglas y reserva cupo (SUP-11)."""
        sol = self._solicitud(solicitud_id)
        sol.verificar(Accion.APROBAR)  # primero la máquina de estados -> 409
        ctx = self._contexto(sol)
        spec = puede_aceptarse()
        if not spec.is_satisfied_by(ctx):
            raise ReglaNoCumplida(spec.motivos_fallo(ctx))
        for programa_id, lugares in sol.lugares_por_programa().items():
            programa = ctx.programas[programa_id]
            if not programa.cupo.hay_lugar(lugares):
                sol.registrar_evento(
                    ev.CupoAgotadoEvento(solicitud_id=sol.id, programa_id=programa_id)
                )
                self.publicador.publicar(sol.extraer_eventos())
                raise CupoAgotado(programa_id, lugares, programa.cupo.disponibles)
        for programa_id, lugares in sol.lugares_por_programa().items():
            ctx.programas[programa_id].ocupar(lugares)
            self.programas.guardar(ctx.programas[programa_id])
        sol.aplicar(Accion.APROBAR)
        return self._cerrar(sol)

    def inscribir(self, solicitud_id: str, monto: Decimal) -> Solicitud:
        """ACEPTADA -> INSCRITA al recibir el pago exacto (RB-03)."""
        sol = self._solicitud(solicitud_id)
        sol.verificar(Accion.INSCRIBIR)
        if Decimal(str(monto)) != sol.total.monto:
            raise ReglaNoCumplida([f"el pago debe ser exactamente {sol.total.monto} MXN"])
        sol.aplicar(Accion.INSCRIBIR)
        return self._cerrar(sol)

    def completar(self, solicitud_id: str) -> Solicitud:
        """INSCRITA -> FINALIZADA (el grupo terminó)."""
        sol = self._solicitud(solicitud_id)
        sol.aplicar(Accion.COMPLETAR)
        return self._cerrar(sol)

    def cancelar(self, solicitud_id: str) -> Solicitud:
        """-> CANCELADA. Libera el cupo si lo tenía reservado (SUP-11, RB-10)."""
        sol = self._solicitud(solicitud_id)
        estado_previo = sol.estado
        sol.verificar(Accion.CANCELAR)
        if estado_previo in ESTADOS_QUE_RETIENEN_CUPO:
            for programa_id, lugares in sol.lugares_por_programa().items():
                programa = self.programas.obtener(programa_id)
                if programa is not None:
                    programa.liberar(lugares)
                    self.programas.guardar(programa)
        sol.aplicar(Accion.CANCELAR)
        return self._cerrar(sol)

    def registrar_resultado(
        self, solicitud_id: str, calificacion: Decimal, asistencia: Decimal
    ) -> Solicitud:
        """US-09 / US-10: calificación final y % de asistencia."""
        sol = self._solicitud(solicitud_id)
        try:
            sol.registrar_resultado(calificacion, asistencia)
        except CantidadInvalida as exc:
            raise ReglaNoCumplida([str(exc)]) from exc
        return self._cerrar(sol)

    def evaluar_certificacion(self, solicitud_id: str) -> ResultadoCertificacion:
        """US-06 / US-13 (RB-06, RB-07, RB-08, RB-12, RB-13; SUP-10)."""
        sol = self._solicitud(solicitud_id)
        if sol.estado != EstadoSolicitud.FINALIZADA or sol.calificacion_final is None:
            return ResultadoCertificacion(sol.id, "Pendiente")
        ctx = self._contexto(sol)
        if cumple_certificacion().is_satisfied_by(ctx):
            resultado = ResultadoCertificacion(sol.id, "Elegible")
        else:
            aprueba = sol.calificacion_final.aprueba()
            asiste = sol.asistencia is not None and sol.asistencia.cumple_minimo()
            motivo = "Ambos" if not aprueba and not asiste else (
                "Calificación" if not aprueba else "Asistencia"
            )
            resultado = ResultadoCertificacion(sol.id, "No elegible", motivo)
        self.publicador.publicar(
            [ev.CertificacionEvaluada(solicitud_id=sol.id, elegible=resultado.estado == "Elegible")]
        )
        return resultado


def alumno_nuevo(**kwargs) -> Alumno:  # utilidad para cargas y pruebas
    return Alumno(**kwargs)
