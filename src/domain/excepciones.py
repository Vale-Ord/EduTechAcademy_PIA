"""Excepciones de dominio de EduTechAcademy.

Cada excepción se traduce a un código HTTP en la capa api (ver src/api/errores.py).
"""


class DominioError(Exception):
    """Base de todos los errores de negocio."""


class TransicionInvalida(DominioError):
    """La acción no es válida desde el estado actual (RES-06, RB-03)."""

    def __init__(self, estado: str, accion: str):
        super().__init__(f"No se puede '{accion}' una solicitud en estado {estado}")
        self.estado = estado
        self.accion = accion


class ReglaNoCumplida(DominioError):
    """Una Specification de negocio no se satisface (RB-01, RB-14, ...)."""

    def __init__(self, motivos: list[str]):
        super().__init__("; ".join(motivos) or "Regla de negocio no cumplida")
        self.motivos = motivos


class CupoAgotado(DominioError):
    """El grupo/programa no tiene lugares suficientes (RB-02, RES-01)."""

    def __init__(self, programa_id: str, solicitados: int, disponibles: int):
        super().__init__(
            f"Cupo agotado en {programa_id}: se piden {solicitados}, hay {disponibles}"
        )
        self.programa_id = programa_id
        self.solicitados = solicitados
        self.disponibles = disponibles


class CantidadInvalida(DominioError):
    """Cantidad, importe o calificación fuera de rango."""


class NoEncontrado(DominioError):
    """La entidad pedida no existe."""


class PermisoDenegado(DominioError):
    """El rol no tiene permiso para la operación (RB-14, ADR-005)."""
