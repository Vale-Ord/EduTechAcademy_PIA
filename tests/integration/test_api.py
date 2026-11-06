"""Integración/E2E: HTTP -> API -> servicio -> repositorios -> base de datos."""
import csv

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.infrastructure.carga_csv import DATA_DIR
from src.infrastructure.config import Settings
from src.infrastructure.db import crear_engine
from src.infrastructure.orm import Base


def _csv(nombre):
    with open(DATA_DIR / nombre, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


ACTIVO = next(a["actor_id"] for a in _csv("actores.csv") if a["activo"] == "1")
INACTIVO = next(a["actor_id"] for a in _csv("actores.csv") if a["activo"] == "0")
PROGRAMA = next(p for p in _csv("catalogo.csv") if p["habilitado"] == "1")
DESHABILITADO = next(p["recurso_id"] for p in _csv("catalogo.csv") if p["habilitado"] == "0")
CE = {"X-Rol": "control_escolar"}


@pytest.fixture
def client(engine_url):
    Base.metadata.drop_all(crear_engine(engine_url))
    app = create_app(Settings(database_url=engine_url, seed_on_startup=True))
    with TestClient(app) as c:
        yield c


def nueva(client, actor=ACTIVO, programa=PROGRAMA["recurso_id"], cantidad=1, rol="control_escolar"):
    return client.post("/solicitudes", headers={"X-Rol": rol}, json={
        "actor_id": actor, "renglones": [{"programa_id": programa, "cantidad": cantidad}]})


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_openapi_y_swagger_disponibles(client):
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_listar_programas_y_404(client):  # US-01
    r = client.get("/programas", headers=CE)
    assert r.status_code == 200 and len(r.json()) == 20
    assert len(client.get("/programas?solo_habilitados=true", headers=CE).json()) == 19
    assert client.get("/programas/NOPE", headers=CE).status_code == 404


def test_flujo_completo_por_http(client):  # US-02 + RB-03 + RB-08
    sol = nueva(client, cantidad=2)
    assert sol.status_code == 201
    sid, total = sol.json()["id"], sol.json()["total"]
    assert sol.json()["estado"] == "SOLICITADA"
    assert client.post(f"/solicitudes/{sid}/aprobar", headers=CE).json()["estado"] == "ACEPTADA"
    assert client.post(f"/solicitudes/{sid}/pago", headers=CE, json={"monto": total}).json()["estado"] == "INSCRITA"
    r = client.put(f"/solicitudes/{sid}/resultado", headers={"X-Rol": "instructor"},
                   json={"calificacion": "85", "asistencia": "90"})
    assert r.status_code == 200
    assert client.post(f"/solicitudes/{sid}/completar", headers=CE).json()["estado"] == "FINALIZADA"
    cert = client.get(f"/solicitudes/{sid}/certificacion", headers=CE).json()
    assert cert["estado"] == "Elegible"
    nombres = [e["evento"] for e in client.get(f"/solicitudes/{sid}/eventos", headers=CE).json()]
    assert nombres[0] == "SolicitudCreada" and "InscripcionConfirmada" in nombres


def test_409_transicion_invalida(client):
    sid = nueva(client).json()["id"]
    r = client.post(f"/solicitudes/{sid}/completar", headers=CE)
    assert r.status_code == 409 and r.json()["error"] == "TransicionInvalida"
    client.post(f"/solicitudes/{sid}/aprobar", headers=CE)
    assert client.post(f"/solicitudes/{sid}/aprobar", headers=CE).status_code == 409


def test_422_alumno_inactivo(client):
    sid = nueva(client, actor=INACTIVO).json()["id"]
    r = client.post(f"/solicitudes/{sid}/aprobar", headers=CE)
    assert r.status_code == 422 and "alumno activo" in r.json()["motivos"][0]


def test_422_programa_deshabilitado(client):
    sid = nueva(client, programa=DESHABILITADO).json()["id"]
    assert client.post(f"/solicitudes/{sid}/aprobar", headers=CE).status_code == 422


def test_409_cupo_agotado(client):
    sid = nueva(client, cantidad=int(PROGRAMA["capacidad_o_stock"]) + 1).json()["id"]
    r = client.post(f"/solicitudes/{sid}/aprobar", headers=CE)
    assert r.status_code == 409 and r.json()["error"] == "CupoAgotado"


def test_422_pago_incorrecto(client):
    sid = nueva(client).json()["id"]
    client.post(f"/solicitudes/{sid}/aprobar", headers=CE)
    assert client.post(f"/solicitudes/{sid}/pago", headers=CE, json={"monto": "1.00"}).status_code == 422


def test_422_validacion_de_esquema(client):
    r = client.post("/solicitudes", headers=CE, json={
        "actor_id": ACTIVO, "renglones": [{"programa_id": "EDU-P001", "cantidad": 0}]})
    assert r.status_code == 422


def test_404_alumno_o_solicitud(client):
    assert nueva(client, actor="NOPE").status_code == 404
    assert client.get("/solicitudes/NOPE", headers=CE).status_code == 404


def test_403_permisos_rb14(client):  # RB-14
    sid = nueva(client).json()["id"]
    assert client.post(f"/solicitudes/{sid}/aprobar", headers={"X-Rol": "estudiante"}).status_code == 403
    assert client.post(f"/solicitudes/{sid}/aprobar", headers={"X-Rol": "inventado"}).status_code == 403
    assert client.put(f"/solicitudes/{sid}/resultado", headers={"X-Rol": "estudiante"},
                      json={"calificacion": "80", "asistencia": "80"}).status_code == 403


def test_validacion_y_beneficio(client):
    sid = nueva(client, actor="EDU-C005", cantidad=3).json()["id"]
    v = client.get(f"/solicitudes/{sid}/validacion", headers=CE).json()
    assert v["cumple"] is True
    b = client.get(f"/solicitudes/{sid}/beneficio", headers=CE).json()
    assert set(b) == {"solicitud_id", "aplica", "total", "motivos", "mensaje"}


def test_resultado_antes_de_inscribir_422(client):
    sid = nueva(client).json()["id"]
    r = client.put(f"/solicitudes/{sid}/resultado", headers={"X-Rol": "instructor"},
                   json={"calificacion": "80", "asistencia": "80"})
    assert r.status_code == 422


def test_filtros_de_solicitudes_pagos_pendientes(client):  # US-03, US-15
    sid = nueva(client).json()["id"]
    client.post(f"/solicitudes/{sid}/aprobar", headers=CE)
    pendientes = client.get("/solicitudes?estado=ACEPTADA", headers=CE).json()
    assert [s["id"] for s in pendientes] == [sid]
    assert len(client.get(f"/solicitudes?actor_id={ACTIVO}", headers=CE).json()) >= 1


def test_cancelar_y_seed_idempotente(client):
    sid = nueva(client).json()["id"]
    assert client.post(f"/solicitudes/{sid}/cancelar", headers=CE).json()["estado"] == "CANCELADA"
    seed = client.post("/admin/seed", headers=CE).json()
    assert seed["sembrada"] is False and seed["mensaje"]
