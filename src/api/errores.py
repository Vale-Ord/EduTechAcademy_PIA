"""Traduce excepciones de dominio a códigos HTTP (contrato del equipo, ver docs/api)."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.excepciones import (
    CantidadInvalida,
    CupoAgotado,
    NoEncontrado,
    PermisoDenegado,
    ReglaNoCumplida,
    TransicionInvalida,
)

MENSAJES = {
    NoEncontrado: "No encontramos lo que buscas. Revisa que el identificador sea correcto.",
    PermisoDenegado: "Tu rol no tiene permiso para realizar esta acción.",
    TransicionInvalida: "Esta acción no se puede realizar con el estado actual de la solicitud.",
    CupoAgotado: "El programa no tiene lugares suficientes para esta solicitud.",
    ReglaNoCumplida: "La solicitud no cumple las reglas de negocio. Revisa los motivos indicados.",
    CantidadInvalida: "Alguno de los valores enviados está fuera del rango permitido.",
}

CODIGOS = [
    (NoEncontrado, 404),        # recurso inexistente
    (PermisoDenegado, 403),     # RB-14
    (TransicionInvalida, 409),  # State Machine
    (CupoAgotado, 409),         # RB-02
    (ReglaNoCumplida, 422),     # Specification no satisfecha
    (CantidadInvalida, 400),    # dato fuera de rango
]


def registrar_manejadores(app: FastAPI) -> None:
    for excepcion, codigo in CODIGOS:
        def _handler(request: Request, exc, _codigo=codigo, _mensaje=MENSAJES[excepcion]):
            detalle = {"error": type(exc).__name__, "detalle": str(exc),
                       "mensaje": _mensaje}
            if isinstance(exc, ReglaNoCumplida):
                detalle["motivos"] = exc.motivos
            return JSONResponse(status_code=_codigo, content=detalle)
        app.add_exception_handler(excepcion, _handler)
