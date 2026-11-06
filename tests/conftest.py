import os
from decimal import Decimal

import pytest

from src.application.servicios import SolicitudService
from src.domain.entidades import Alumno, Programa
from src.domain.valores import Cupo, Dinero
from src.infrastructure.memoria import (
    AlumnoRepoMemoria,
    ProgramaRepoMemoria,
    PublicadorMemoria,
    SolicitudRepoMemoria,
)


@pytest.fixture
def servicio():
    """Servicio con repos en memoria y un mini catálogo propio."""
    alumnos, programas = AlumnoRepoMemoria(), ProgramaRepoMemoria()
    alumnos.agregar(Alumno("A1", "Ana", es_preferente=True, activo=True))
    alumnos.agregar(Alumno("A2", "Beto", es_preferente=False, activo=False))
    programas.guardar(Programa("P1", "Cloud", Dinero(Decimal("1000")), Cupo(3, 0, "P1")))
    programas.guardar(Programa("P2", "Web", Dinero(Decimal("500")), Cupo(1, 0, "P2")))
    programas.guardar(Programa("P3", "Cerrado", Dinero(Decimal("200")), Cupo(5, 0, "P3"), habilitado=False))
    return SolicitudService(alumnos, programas, SolicitudRepoMemoria(), PublicadorMemoria())


@pytest.fixture
def engine_url():
    """SQLite en memoria por defecto; en Docker Compose se usa PostgreSQL con TEST_DATABASE_URL."""
    return os.getenv("TEST_DATABASE_URL", "sqlite://")
