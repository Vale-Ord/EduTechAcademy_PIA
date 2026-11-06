"""Engine, sesiones y semilla de datos."""
from __future__ import annotations

from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.carga_csv import cargar_datos
from src.infrastructure.orm import AlumnoORM, Base
from src.infrastructure.repositorio_sql import AlumnoRepoSQL, ProgramaRepoSQL, SolicitudRepoSQL


def crear_engine(url: str) -> Engine:
    if url.startswith("sqlite") and (":memory:" in url or url in ("sqlite://", "sqlite:///")):
        # una sola conexión compartida para que la base en memoria viva entre sesiones
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


def crear_tablas(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def sembrar_si_vacio(session: Session) -> bool:
    """Carga los CSV del maestro solo si la base está vacía. Devuelve True si sembró."""
    if session.scalar(select(func.count()).select_from(AlumnoORM)):
        return False
    cargar_datos(AlumnoRepoSQL(session), ProgramaRepoSQL(session), SolicitudRepoSQL(session))
    session.commit()
    return True


def crear_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
