"""Ejecuta los 120 casos de prueba y 20 de transición del maestro contra el dominio propio.

Interpretación de las acciones sugeridas (documentada en docs/mapeo_maestro.md):
  aprobar            SOLICITADA -> ACEPTADA (si cumple puede_aceptarse y hay cupo)
  repetir_aprobacion aprobar dos veces; la segunda debe fallar (TransicionInvalida)
  saltar_estado      intentar inscribir (pagar) sin haber aprobado -> TransicionInvalida
  completar          finalizar desde SOLICITADA -> TransicionInvalida (se exige INSCRITA)
  cancelar           SOLICITADA -> CANCELADA
Cada caso corre sobre un estado limpio (repos nuevos) para que sean independientes.
"""
from __future__ import annotations

import csv
from pathlib import Path

from src.application.servicios import SolicitudService
from src.domain.excepciones import CupoAgotado, DominioError, ReglaNoCumplida, TransicionInvalida
from src.infrastructure.carga_csv import DATA_DIR, cargar_datos
from src.infrastructure.memoria import (
    AlumnoRepoMemoria,
    ProgramaRepoMemoria,
    PublicadorMemoria,
    SolicitudRepoMemoria,
)


def nuevo_servicio(data_dir: Path = DATA_DIR) -> SolicitudService:
    alumnos, programas, solicitudes = AlumnoRepoMemoria(), ProgramaRepoMemoria(), SolicitudRepoMemoria()
    cargar_datos(alumnos, programas, solicitudes, data_dir)
    return SolicitudService(alumnos, programas, solicitudes, PublicadorMemoria())


def _leer(nombre: str, data_dir: Path) -> list[dict]:
    with open(data_dir / nombre, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def ejecutar_caso(caso: dict, data_dir: Path = DATA_DIR) -> dict:
    svc = nuevo_servicio(data_dir)
    op = caso["operacion_id"]
    if caso["tipo_prueba"] == "validar_operacion":
        r = svc.validar(op)
        return {"resultado": "CUMPLE" if r.cumple else "NO_CUMPLE",
                "evidencia": "; ".join(r.motivos) or "todas las condiciones satisfechas"}
    r = svc.evaluar_beneficio(op)
    return {"resultado": "APLICA" if r.aplica else "NO_APLICA",
            "evidencia": f"total={r.total} MXN" + ("; " + "; ".join(r.motivos) if r.motivos else "")}


def ejecutar_transicion(caso: dict, data_dir: Path = DATA_DIR) -> dict:
    svc = nuevo_servicio(data_dir)
    op, accion = caso["operacion_id"], caso["accion_sugerida"]
    try:
        if accion == "aprobar":
            svc.aprobar(op)
        elif accion == "repetir_aprobacion":
            svc.aprobar(op)
            svc.aprobar(op)
        elif accion == "saltar_estado":
            svc.inscribir(op, svc.obtener(op).total.monto)
        elif accion == "completar":
            svc.completar(op)
        elif accion == "cancelar":
            svc.cancelar(op)
        else:
            return {"estado_final": caso["estado_inicial"], "resultado": "ACCION_DESCONOCIDA",
                    "evidencia": accion}
    except TransicionInvalida as exc:
        return {"estado_final": svc.obtener(op).estado.value, "resultado": "EXCEPCION TransicionInvalida (HTTP 409)",
                "evidencia": str(exc)}
    except ReglaNoCumplida as exc:
        return {"estado_final": svc.obtener(op).estado.value, "resultado": "EXCEPCION ReglaNoCumplida (HTTP 422)",
                "evidencia": str(exc)}
    except CupoAgotado as exc:
        return {"estado_final": svc.obtener(op).estado.value, "resultado": "EXCEPCION CupoAgotado (HTTP 409)",
                "evidencia": str(exc)}
    except DominioError as exc:  # pragma: no cover
        return {"estado_final": svc.obtener(op).estado.value, "resultado": f"EXCEPCION {type(exc).__name__}",
                "evidencia": str(exc)}
    sol = svc.obtener(op)
    eventos = ",".join(e.nombre for e in svc.publicador.listar(op))
    return {"estado_final": sol.estado.value, "resultado": "OK", "evidencia": f"eventos: {eventos}"}


def ejecutar_todo(data_dir: Path = DATA_DIR, salida: Path | None = None) -> dict:
    casos = _leer("casos_prueba.csv", data_dir)
    trans = _leer("transiciones_prueba.csv", data_dir)
    res_casos = [{**c, **ejecutar_caso(c, data_dir)} for c in casos]
    res_trans = [{**t, **ejecutar_transicion(t, data_dir)} for t in trans]
    if salida:
        salida.mkdir(parents=True, exist_ok=True)
        for nombre, filas in (("resultados_casos.csv", res_casos), ("resultados_transiciones.csv", res_trans)):
            with open(salida / nombre, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
                w.writeheader()
                w.writerows(filas)
    return {"casos": res_casos, "transiciones": res_trans}
