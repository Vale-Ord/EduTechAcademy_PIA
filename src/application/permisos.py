"""Permisos por rol (RB-14, RES-04, ADR-005). Viven en el Service Layer, no en el dominio."""
from __future__ import annotations

from enum import Enum

from src.domain.excepciones import PermisoDenegado


class Rol(str, Enum):
    ESTUDIANTE = "estudiante"
    INSTRUCTOR = "instructor"
    CONTROL_ESCOLAR = "control_escolar"
    ADMINISTRACION = "administracion"
    CLIENTE_EMPRESARIAL = "cliente_empresarial"


class Permiso(str, Enum):
    CONSULTAR_PROGRAMAS = "consultar_programas"  # US-01
    CREAR_SOLICITUD = "crear_solicitud"  # US-02, US-18
    CONSULTAR_SOLICITUDES = "consultar_solicitudes"  # US-03, US-12, US-15
    VALIDAR_SOLICITUD = "validar_solicitud"  # US-13 (reglas)
    APROBAR = "aprobar"  # US-02 / gestionar inscripciones
    REGISTRAR_PAGO = "registrar_pago"  # US-02, SUP-14
    COMPLETAR = "completar"
    CANCELAR = "cancelar"  # RB-10
    REGISTRAR_RESULTADO = "registrar_resultado"  # US-09, US-10
    CONSULTAR_CERTIFICACION = "consultar_certificacion"  # US-06, US-13
    VER_REPORTES = "ver_reportes"  # US-17

R, P = Rol, Permiso
PERMISOS: dict[Rol, set[Permiso]] = {
    R.ESTUDIANTE: {
        P.CONSULTAR_PROGRAMAS, P.CREAR_SOLICITUD, P.CONSULTAR_SOLICITUDES,
        P.REGISTRAR_PAGO, P.CANCELAR, P.CONSULTAR_CERTIFICACION,
    },
    R.INSTRUCTOR: {P.CONSULTAR_PROGRAMAS, P.CONSULTAR_SOLICITUDES, P.REGISTRAR_RESULTADO},
    R.CONTROL_ESCOLAR: {
        P.CONSULTAR_PROGRAMAS, P.CREAR_SOLICITUD, P.CONSULTAR_SOLICITUDES,
        P.VALIDAR_SOLICITUD, P.APROBAR, P.REGISTRAR_PAGO, P.COMPLETAR, P.CANCELAR,
        P.CONSULTAR_CERTIFICACION,
    },
    R.ADMINISTRACION: {P.CONSULTAR_PROGRAMAS, P.CONSULTAR_SOLICITUDES, P.VER_REPORTES},
    R.CLIENTE_EMPRESARIAL: {P.CONSULTAR_PROGRAMAS, P.CREAR_SOLICITUD},
}


def autorizar(rol: str, permiso: Permiso) -> None:
    try:
        rol_enum = Rol(rol)
    except ValueError:
        raise PermisoDenegado(f"Rol desconocido: {rol}") from None
    if permiso not in PERMISOS[rol_enum]:
        raise PermisoDenegado(f"El rol '{rol}' no tiene permiso para '{permiso.value}'")
