"""Repositorios SQLAlchemy: traducen entre filas (ORM) y objetos de dominio."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domain.entidades import Alumno, Programa, Solicitud
from src.domain.estados import EstadoSolicitud
from src.domain.eventos import EventoDominio
from src.domain.valores import Calificacion, Cupo, Dinero, LineaSolicitud, PorcentajeAsistencia
from src.infrastructure.orm import AlumnoORM, EventoORM, LineaORM, ProgramaORM, SolicitudORM


class AlumnoRepoSQL:
    def __init__(self, session: Session):
        self.s = session

    def obtener(self, alumno_id):
        r = self.s.get(AlumnoORM, alumno_id)
        return None if r is None else Alumno(r.id, r.nombre, r.es_preferente, r.activo, r.ciudad)

    def agregar(self, a):
        self.s.merge(AlumnoORM(id=a.id, nombre=a.nombre, es_preferente=a.es_preferente,
                               activo=a.activo, ciudad=a.ciudad))
        self.s.flush()


def _programa(r: ProgramaORM) -> Programa:
    return Programa(r.id, r.descripcion, Dinero(r.precio), Cupo(r.capacidad, r.ocupados, r.id), r.habilitado)


class ProgramaRepoSQL:
    def __init__(self, session: Session):
        self.s = session

    def obtener(self, programa_id):
        r = self.s.get(ProgramaORM, programa_id)
        return None if r is None else _programa(r)

    def listar(self, solo_habilitados=False):
        q = select(ProgramaORM).order_by(ProgramaORM.id)
        if solo_habilitados:
            q = q.where(ProgramaORM.habilitado.is_(True))
        return [_programa(r) for r in self.s.scalars(q)]

    def guardar(self, p):
        self.s.merge(ProgramaORM(id=p.id, descripcion=p.descripcion, precio=p.precio.monto,
                                 capacidad=p.cupo.capacidad, ocupados=p.cupo.ocupados,
                                 habilitado=p.habilitado))
        self.s.flush()


def _solicitud(r: SolicitudORM) -> Solicitud:
    return Solicitud(
        id=r.id, alumno_id=r.alumno_id, fecha_solicitud=r.fecha_solicitud,
        lineas=[LineaSolicitud(ln.programa_id, ln.cantidad, Dinero(ln.precio_unitario)) for ln in r.lineas],
        estado=EstadoSolicitud(r.estado), promocion_activa=r.promocion_activa,
        autorizado=r.autorizado, referencia=r.referencia,
        calificacion_final=None if r.calificacion_final is None else Calificacion(r.calificacion_final),
        asistencia=None if r.asistencia is None else PorcentajeAsistencia(r.asistencia),
    )


class SolicitudRepoSQL:
    def __init__(self, session: Session):
        self.s = session

    def obtener(self, solicitud_id):
        r = self.s.get(SolicitudORM, solicitud_id)
        return None if r is None else _solicitud(r)

    def _volcar(self, sol: Solicitud, fila: SolicitudORM | None) -> SolicitudORM:
        fila = fila or SolicitudORM(id=sol.id)
        fila.alumno_id = sol.alumno_id
        fila.fecha_solicitud = sol.fecha_solicitud
        fila.estado = sol.estado.value
        fila.promocion_activa = sol.promocion_activa
        fila.autorizado = sol.autorizado
        fila.referencia = sol.referencia
        fila.calificacion_final = None if sol.calificacion_final is None else sol.calificacion_final.valor
        fila.asistencia = None if sol.asistencia is None else sol.asistencia.valor
        if not fila.lineas:  # las líneas son inmutables tras crear la solicitud (ADR-010)
            fila.lineas = [LineaORM(programa_id=ln.programa_id, cantidad=ln.cantidad,
                                    precio_unitario=ln.precio_unitario.monto) for ln in sol.lineas]
        return fila

    def agregar(self, sol):
        self.s.add(self._volcar(sol, None))
        self.s.flush()

    def guardar(self, sol):
        fila = self.s.get(SolicitudORM, sol.id)
        if fila is None:
            self.s.add(self._volcar(sol, None))
        else:
            self._volcar(sol, fila)
        self.s.flush()

    def listar(self, alumno_id=None, estado=None):
        q = select(SolicitudORM).order_by(SolicitudORM.id)
        if alumno_id:
            q = q.where(SolicitudORM.alumno_id == alumno_id)
        if estado:
            q = q.where(SolicitudORM.estado == estado)
        return [_solicitud(r) for r in self.s.scalars(q)]

    def siguiente_id(self):
        n = self.s.scalar(select(func.count()).select_from(SolicitudORM)) or 0
        while self.s.get(SolicitudORM, f"EDU-N{n + 1:04d}") is not None:
            n += 1
        return f"EDU-N{n + 1:04d}"


class PublicadorSQL:
    """Persiste los eventos de dominio. Se invoca DESPUÉS del commit del caso de uso."""

    def __init__(self, session: Session):
        self.s = session

    def publicar(self, eventos):
        for e in eventos:
            self.s.add(EventoORM(solicitud_id=e.solicitud_id, nombre=e.nombre,
                                 ocurrido_en=e.ocurrido_en.replace(tzinfo=None)))
        self.s.commit()

    def listar(self, solicitud_id):
        q = select(EventoORM).where(EventoORM.solicitud_id == solicitud_id).order_by(EventoORM.id)
        return [_EventoLeido(r.solicitud_id, r.ocurrido_en, r.nombre) for r in self.s.scalars(q)]


class _EventoLeido(EventoDominio):
    """Evento reconstruido desde la base (solo lectura)."""

    def __init__(self, solicitud_id, ocurrido_en, nombre):
        object.__setattr__(self, "solicitud_id", solicitud_id)
        object.__setattr__(self, "ocurrido_en", ocurrido_en)
        object.__setattr__(self, "_nombre", nombre)

    @property
    def nombre(self):
        return self._nombre


class UnidadDeTrabajoSQL:
    def __init__(self, session: Session):
        self.s = session

    def commit(self):
        self.s.commit()

    def rollback(self):
        self.s.rollback()
