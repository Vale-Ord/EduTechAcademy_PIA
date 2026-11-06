"""Mapeo SQLAlchemy 2.0. Las tablas son un detalle de infraestructura; el dominio no las conoce."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AlumnoORM(Base):
    __tablename__ = "alumnos"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    es_preferente: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    ciudad: Mapped[str] = mapped_column(String(80), default="")


class ProgramaORM(Base):
    __tablename__ = "programas"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    descripcion: Mapped[str] = mapped_column(String(120))
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    capacidad: Mapped[int] = mapped_column(Integer)
    ocupados: Mapped[int] = mapped_column(Integer, default=0)
    habilitado: Mapped[bool] = mapped_column(Boolean, default=True)


class SolicitudORM(Base):
    __tablename__ = "solicitudes"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    alumno_id: Mapped[str] = mapped_column(ForeignKey("alumnos.id"), index=True)
    fecha_solicitud: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(20), index=True)
    promocion_activa: Mapped[bool] = mapped_column(Boolean, default=False)
    autorizado: Mapped[bool] = mapped_column(Boolean, default=True)
    referencia: Mapped[str] = mapped_column(String(60), default="")
    calificacion_final: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    asistencia: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    lineas: Mapped[list[LineaORM]] = relationship(
        back_populates="solicitud", cascade="all, delete-orphan", order_by="LineaORM.id"
    )


class LineaORM(Base):
    __tablename__ = "lineas_solicitud"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solicitud_id: Mapped[str] = mapped_column(ForeignKey("solicitudes.id"), index=True)
    programa_id: Mapped[str] = mapped_column(ForeignKey("programas.id"))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    solicitud: Mapped[SolicitudORM] = relationship(back_populates="lineas")


class EventoORM(Base):
    """Registro de Domain Events publicados (ADR-007)."""

    __tablename__ = "eventos_dominio"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solicitud_id: Mapped[str] = mapped_column(String(20), index=True)
    nombre: Mapped[str] = mapped_column(String(60))
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime)
