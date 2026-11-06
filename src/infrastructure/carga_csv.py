"""Carga los CSV del maestro (data/) a cualquier conjunto de repositorios."""
from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.domain.entidades import Alumno, Programa, Solicitud
from src.domain.estados import EstadoSolicitud
from src.domain.valores import Cupo, Dinero, LineaSolicitud

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _leer(nombre: str, data_dir: Path) -> list[dict]:
    with open(data_dir / nombre, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def cargar_datos(alumnos, programas, solicitudes, data_dir: Path = DATA_DIR) -> dict[str, int]:
    """Importa actores, catálogo y operaciones con su detalle (claves foráneas por id)."""
    for r in _leer("actores.csv", data_dir):
        alumnos.agregar(Alumno(
            id=r["actor_id"], nombre=r["nombre"],
            es_preferente=r["es_preferente"] == "1", activo=r["activo"] == "1",
            ciudad=r["ciudad"],
        ))
    precios: dict[str, Dinero] = {}
    for r in _leer("catalogo.csv", data_dir):
        precio = Dinero(Decimal(r["precio_mxn"]))
        precios[r["recurso_id"]] = precio
        programas.guardar(Programa(
            id=r["recurso_id"], descripcion=r["descripcion"], precio=precio,
            cupo=Cupo(int(r["capacidad_o_stock"]), 0, r["recurso_id"]),
            habilitado=r["habilitado"] == "1",
        ))
    detalle: dict[str, list[LineaSolicitud]] = {}
    for r in _leer("detalle_operaciones.csv", data_dir):
        detalle.setdefault(r["operacion_id"], []).append(
            LineaSolicitud(r["recurso_id"], int(r["cantidad"]), precios[r["recurso_id"]])
        )
    n_ops = 0
    for r in _leer("operaciones.csv", data_dir):
        solicitudes.agregar(Solicitud(
            id=r["operacion_id"], alumno_id=r["actor_id"],
            fecha_solicitud=date.fromisoformat(r["fecha_solicitud"]),
            lineas=detalle.get(r["operacion_id"], []),
            estado=EstadoSolicitud(r["estado_inicial"]),
            promocion_activa=r["promocion_activa"] == "1",
            autorizado=r["autorizado"] == "1", referencia=r["referencia"],
        ))
        n_ops += 1
    return {"actores": len(_leer("actores.csv", data_dir)), "programas": len(precios),
            "operaciones": n_ops}
