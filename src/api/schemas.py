"""Contratos de entrada/salida de la API (Pydantic v2)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class RenglonIn(BaseModel):
    programa_id: str = Field(examples=["EDU-P001"])
    cantidad: int = Field(gt=0, examples=[2], description="Lugares solicitados (> 0)")


class SolicitudIn(BaseModel):
    actor_id: str = Field(examples=["EDU-C005"], description="Id del alumno")
    renglones: list[RenglonIn] = Field(min_length=1)
    promocion_activa: bool = False
    autorizado: bool = True
    referencia: str = ""


class PagoIn(BaseModel):
    monto: Decimal = Field(examples=["1500.00"], description="Debe ser igual al total (RB-03)")


class ResultadoAcademicoIn(BaseModel):
    calificacion: Decimal = Field(ge=0, le=100, examples=["85"])
    asistencia: Decimal = Field(ge=0, le=100, examples=["90"])


class RenglonOut(BaseModel):
    programa_id: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class SolicitudOut(BaseModel):
    id: str
    actor_id: str
    estado: str
    fecha_solicitud: date
    total: Decimal
    promocion_activa: bool
    autorizado: bool
    referencia: str
    renglones: list[RenglonOut]
    acciones_permitidas: list[str]
    calificacion_final: Decimal | None = None
    asistencia: Decimal | None = None
    mensaje: str = Field(default="", description="Mensaje en lenguaje claro sobre lo que ocurrió y cuál es el siguiente paso")


class ProgramaOut(BaseModel):
    id: str
    descripcion: str
    precio_mxn: Decimal
    capacidad: int
    ocupados: int
    disponibles: int
    habilitado: bool


class ValidacionOut(BaseModel):
    solicitud_id: str
    cumple: bool
    motivos: list[str]
    mensaje: str = Field(default="", description="Mensaje en lenguaje claro sobre lo que ocurrió y cuál es el siguiente paso")


class BeneficioOut(BaseModel):
    solicitud_id: str
    aplica: bool
    total: Decimal
    motivos: list[str]
    mensaje: str = Field(default="", description="Mensaje en lenguaje claro sobre lo que ocurrió y cuál es el siguiente paso")


class CertificacionOut(BaseModel):
    solicitud_id: str
    estado: str
    motivo: str | None = None
    mensaje: str = Field(default="", description="Mensaje en lenguaje claro sobre lo que ocurrió y cuál es el siguiente paso")


class EventoOut(BaseModel):
    evento: str
    solicitud_id: str
    ocurrido_en: str


class HealthOut(BaseModel):
    status: str = Field(examples=["ok"])
    entorno: str = Field(examples=["production"])
    mensaje: str = Field(examples=["El servicio está funcionando correctamente."])


class SeedOut(BaseModel):
    sembrada: bool = Field(description="true si se cargaron los datos; false si la base ya tenía información")
    mensaje: str


class ErrorOut(BaseModel):
    """Formato de todos los errores de negocio de la API."""

    error: str = Field(examples=["TransicionInvalida"], description="Tipo técnico del error")
    detalle: str = Field(description="Detalle técnico")
    mensaje: str = Field(description="Explicación en lenguaje claro para el usuario")
    motivos: list[str] | None = Field(default=None, description="Reglas que no se cumplieron (solo en 422)")
