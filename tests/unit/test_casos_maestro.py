"""Oráculo independiente: recalcula con csv + Decimal y compara contra el dominio."""
import csv
from decimal import Decimal

import pytest

from src.application.casos_maestro import ejecutar_caso, ejecutar_transicion
from src.infrastructure.carga_csv import DATA_DIR


def leer(nombre):
    with open(DATA_DIR / nombre, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


ACTORES = {r["actor_id"]: r for r in leer("actores.csv")}
CATALOGO = {r["recurso_id"]: r for r in leer("catalogo.csv")}
OPS = {r["operacion_id"]: r for r in leer("operaciones.csv")}
DETALLE: dict[str, list[dict]] = {}
for _r in leer("detalle_operaciones.csv"):
    DETALLE.setdefault(_r["operacion_id"], []).append(_r)


def total(op):
    return sum(Decimal(CATALOGO[d["recurso_id"]]["precio_mxn"]) * int(d["cantidad"]) for d in DETALLE.get(op, []))


def esperado_validar(op):
    a, o = ACTORES[OPS[op]["actor_id"]], OPS[op]
    return a["activo"] == "1" and len(DETALLE.get(op, [])) > 0 and o["autorizado"] == "1"


def esperado_beneficio(op):
    a, o = ACTORES[OPS[op]["actor_id"]], OPS[op]
    return a["es_preferente"] == "1" and total(op) >= Decimal("1500") and o["promocion_activa"] == "0"


CASOS = leer("casos_prueba.csv")


def test_el_paquete_trae_120_casos_y_20_transiciones():
    assert len(CASOS) == 120 and len(leer("transiciones_prueba.csv")) == 20


@pytest.mark.parametrize("caso", CASOS, ids=[c["caso_id"] for c in CASOS])
def test_casos_validar_y_beneficio(caso):
    r = ejecutar_caso(caso)
    if caso["tipo_prueba"] == "validar_operacion":
        assert (r["resultado"] == "CUMPLE") is esperado_validar(caso["operacion_id"])
    else:
        assert (r["resultado"] == "APLICA") is esperado_beneficio(caso["operacion_id"])


TRANS = leer("transiciones_prueba.csv")


@pytest.mark.parametrize("caso", TRANS, ids=[c["caso_id"] for c in TRANS])
def test_transiciones_del_maestro(caso):
    r = ejecutar_transicion(caso)
    accion, op = caso["accion_sugerida"], caso["operacion_id"]
    if accion == "cancelar":
        assert r["estado_final"] == "CANCELADA" and r["resultado"] == "OK"
    elif accion in ("completar", "saltar_estado"):
        assert r["resultado"].startswith("EXCEPCION TransicionInvalida")
        assert r["estado_final"] == "SOLICITADA"
    elif accion == "aprobar":
        procesable = esperado_validar(op) and CATALOGO_OK(op)
        assert (r["estado_final"] == "ACEPTADA") is procesable
    elif accion == "repetir_aprobacion":
        if esperado_validar(op) and CATALOGO_OK(op):
            assert r["resultado"].startswith("EXCEPCION TransicionInvalida")
            assert r["estado_final"] == "ACEPTADA"
        else:
            assert r["resultado"].startswith("EXCEPCION ReglaNoCumplida")


def CATALOGO_OK(op):
    return all(CATALOGO[d["recurso_id"]]["habilitado"] == "1" for d in DETALLE.get(op, []))
