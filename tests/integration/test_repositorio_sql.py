"""Integración: dominio + repositorios SQLAlchemy + base real (SQLite o PostgreSQL)."""
from datetime import date
from decimal import Decimal

import pytest

from src.application.servicios import SolicitudService
from src.domain.entidades import Alumno, Programa, Solicitud
from src.domain.estados import EstadoSolicitud
from src.domain.excepciones import CupoAgotado
from src.domain.valores import Cupo, Dinero, LineaSolicitud
from src.infrastructure.db import (
    crear_engine,
    crear_session_factory,
    crear_tablas,
    sembrar_si_vacio,
)
from src.infrastructure.orm import Base
from src.infrastructure.repositorio_sql import (
    AlumnoRepoSQL,
    ProgramaRepoSQL,
    PublicadorSQL,
    SolicitudRepoSQL,
    UnidadDeTrabajoSQL,
)


@pytest.fixture
def session(engine_url):
    engine = crear_engine(engine_url)
    Base.metadata.drop_all(engine)
    crear_tablas(engine)
    with crear_session_factory(engine)() as s:
        yield s
    engine.dispose()


def servicio_sql(session):
    return SolicitudService(
        AlumnoRepoSQL(session), ProgramaRepoSQL(session), SolicitudRepoSQL(session),
        PublicadorSQL(session), UnidadDeTrabajoSQL(session),
    )


def test_guardar_y_recuperar_solicitud(session):
    AlumnoRepoSQL(session).agregar(Alumno("A1", "Ana", True, True, "Apodaca"))
    ProgramaRepoSQL(session).guardar(Programa("P1", "Cloud", Dinero("100.50"), Cupo(5, 0, "P1")))
    repo = SolicitudRepoSQL(session)
    repo.agregar(Solicitud("S1", "A1", date(2026, 10, 1),
                           lineas=[LineaSolicitud("P1", 2, Dinero("100.50"))]))
    session.commit()
    sol = repo.obtener("S1")
    assert sol.estado == EstadoSolicitud.SOLICITADA
    assert sol.total.monto == Decimal("201.00")
    assert repo.obtener("NOPE") is None


def test_rollback_descarta_cambios_no_confirmados(session):  # patrón de U5 (E4)
    AlumnoRepoSQL(session).agregar(Alumno("A1", "Ana"))
    session.rollback()
    assert AlumnoRepoSQL(session).obtener("A1") is None


def test_sembrar_carga_40_20_60_y_es_idempotente(session):
    assert sembrar_si_vacio(session) is True
    assert sembrar_si_vacio(session) is False
    assert len(ProgramaRepoSQL(session).listar()) == 20
    assert len(SolicitudRepoSQL(session).listar()) == 60
    assert AlumnoRepoSQL(session).obtener("EDU-C001").nombre == "Alumno 01"
    assert len(ProgramaRepoSQL(session).listar(solo_habilitados=True)) == 19


def test_flujo_completo_persistido(session):
    sembrar_si_vacio(session)
    svc = servicio_sql(session)
    sol = svc.crear("EDU-C005", [("EDU-P001", 2)])
    svc.aprobar(sol.id)
    assert svc.obtener_programa("EDU-P001").cupo.ocupados == 2
    svc.inscribir(sol.id, sol.total.monto)
    svc.registrar_resultado(sol.id, Decimal("90"), Decimal("95"))
    svc.completar(sol.id)
    assert svc.evaluar_certificacion(sol.id).estado == "Elegible"
    nombres = [e.nombre for e in svc.eventos_de(sol.id)]
    assert nombres[:4] == ["SolicitudCreada", "SolicitudAceptada",
                           "InscripcionConfirmada", "SolicitudFinalizada"]


def test_cupo_agotado_persistido(session):
    sembrar_si_vacio(session)
    svc = servicio_sql(session)
    programa = svc.obtener_programa("EDU-P001")
    sol = svc.crear("EDU-C005", [("EDU-P001", programa.cupo.capacidad + 1)])
    with pytest.raises(CupoAgotado):
        svc.aprobar(sol.id)
    assert svc.obtener_programa("EDU-P001").cupo.ocupados == 0


def test_cancelar_libera_cupo_persistido(session):
    sembrar_si_vacio(session)
    svc = servicio_sql(session)
    sol = svc.crear("EDU-C005", [("EDU-P002", 3)])
    svc.aprobar(sol.id)
    svc.cancelar(sol.id)
    assert svc.obtener_programa("EDU-P002").cupo.ocupados == 0
    assert svc.obtener(sol.id).estado == EstadoSolicitud.CANCELADA
    assert len(svc.listar(estado="CANCELADA")) == 1
