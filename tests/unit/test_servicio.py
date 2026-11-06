from decimal import Decimal

import pytest

from src.application.permisos import Permiso, autorizar
from src.domain.estados import EstadoSolicitud as E
from src.domain.excepciones import (
    CantidadInvalida,
    CupoAgotado,
    NoEncontrado,
    PermisoDenegado,
    ReglaNoCumplida,
    TransicionInvalida,
)


def nombres(servicio, sid):
    return [e.nombre for e in servicio.publicador.listar(sid)]


def test_flujo_completo_feliz(servicio):  # US-02 + RB-03 + SUP-10 + RB-08
    sol = servicio.crear("A1", [("P1", 2)])
    assert sol.estado == E.SOLICITADA and sol.total.monto == Decimal("2000")
    servicio.aprobar(sol.id)
    assert servicio.obtener_programa("P1").cupo.ocupados == 2
    servicio.inscribir(sol.id, Decimal("2000"))
    servicio.completar(sol.id)
    servicio.registrar_resultado(sol.id, Decimal("90"), Decimal("100"))
    assert servicio.evaluar_certificacion(sol.id).estado == "Elegible"
    assert nombres(servicio, sol.id)[:4] == [
        "SolicitudCreada", "SolicitudAceptada", "InscripcionConfirmada", "SolicitudFinalizada"]


def test_crear_alumno_o_programa_inexistente(servicio):
    with pytest.raises(NoEncontrado):
        servicio.crear("NOPE", [("P1", 1)])
    with pytest.raises(NoEncontrado):
        servicio.crear("A1", [("NOPE", 1)])
    with pytest.raises(NoEncontrado):
        servicio.obtener("NOPE")


def test_crear_sin_renglones_o_cantidad_invalida(servicio):
    with pytest.raises(ReglaNoCumplida):
        servicio.crear("A1", [])
    with pytest.raises(CantidadInvalida):
        servicio.crear("A1", [("P1", 0)])


def test_aprobar_alumno_inactivo_422(servicio):
    sol = servicio.crear("A2", [("P1", 1)])
    with pytest.raises(ReglaNoCumplida) as exc:
        servicio.aprobar(sol.id)
    assert "alumno activo" in exc.value.motivos[0]
    assert sol.estado == E.SOLICITADA


def test_aprobar_programa_deshabilitado_422(servicio):
    sol = servicio.crear("A1", [("P3", 1)])
    with pytest.raises(ReglaNoCumplida):
        servicio.aprobar(sol.id)


def test_aprobar_sin_cupo_409_y_no_reserva_nada(servicio):  # RB-02, TC-CUPO-02
    sol = servicio.crear("A1", [("P1", 1), ("P2", 2)])  # P2 solo tiene 1
    with pytest.raises(CupoAgotado):
        servicio.aprobar(sol.id)
    assert servicio.obtener_programa("P1").cupo.ocupados == 0
    assert "CupoAgotadoEvento" in nombres(servicio, sol.id)


def test_ultimo_lugar_se_puede_ocupar(servicio):  # TC-CUPO-03
    sol = servicio.crear("A1", [("P2", 1)])
    servicio.aprobar(sol.id)
    assert servicio.obtener_programa("P2").cupo.disponibles == 0
    otra = servicio.crear("A1", [("P2", 1)])
    with pytest.raises(CupoAgotado):
        servicio.aprobar(otra.id)


def test_pago_debe_ser_exacto(servicio):  # RB-03
    sol = servicio.crear("A1", [("P1", 1)])
    servicio.aprobar(sol.id)
    with pytest.raises(ReglaNoCumplida):
        servicio.inscribir(sol.id, Decimal("999.99"))
    assert servicio.obtener(sol.id).estado == E.ACEPTADA


def test_no_se_puede_pagar_sin_aprobar(servicio):
    sol = servicio.crear("A1", [("P1", 1)])
    with pytest.raises(TransicionInvalida):
        servicio.inscribir(sol.id, Decimal("1000"))


def test_cancelar_libera_cupo(servicio):  # SUP-11
    sol = servicio.crear("A1", [("P1", 3)])
    servicio.aprobar(sol.id)
    assert servicio.obtener_programa("P1").cupo.disponibles == 0
    servicio.cancelar(sol.id)
    assert servicio.obtener_programa("P1").cupo.disponibles == 3
    with pytest.raises(TransicionInvalida):
        servicio.aprobar(sol.id)


def test_cancelar_solicitada_no_toca_cupo(servicio):
    sol = servicio.crear("A1", [("P1", 1)])
    servicio.cancelar(sol.id)
    assert servicio.obtener_programa("P1").cupo.ocupados == 0


def test_resultado_solo_con_inscripcion_confirmada(servicio):
    sol = servicio.crear("A1", [("P1", 1)])
    with pytest.raises(ReglaNoCumplida):
        servicio.registrar_resultado(sol.id, Decimal("80"), Decimal("90"))


@pytest.mark.parametrize("cal,asis,motivo", [
    ("69", "100", "Calificación"), ("100", "75", "Asistencia"), ("50", "50", "Ambos"),
])
def test_no_elegible_con_motivo(servicio, cal, asis, motivo):  # RB-12, RB-13
    sol = servicio.crear("A1", [("P1", 1)])
    servicio.aprobar(sol.id)
    servicio.inscribir(sol.id, Decimal("1000"))
    servicio.registrar_resultado(sol.id, Decimal(cal), Decimal(asis))
    assert servicio.evaluar_certificacion(sol.id).estado == "Pendiente"  # aún no finalizada
    servicio.completar(sol.id)
    r = servicio.evaluar_certificacion(sol.id)
    assert r.estado == "No elegible" and r.motivo == motivo


def test_listar_filtros_y_pagos_pendientes(servicio):  # US-03, US-15
    a = servicio.crear("A1", [("P1", 1)])
    servicio.crear("A2", [("P2", 1)])
    servicio.aprobar(a.id)
    assert len(servicio.listar(alumno_id="A1")) == 1
    assert [s.id for s in servicio.listar(estado="ACEPTADA")] == [a.id]  # aceptada = pago pendiente
    assert len(servicio.listar_programas(solo_habilitados=True)) == 2


def test_validar_y_beneficio(servicio):
    sol = servicio.crear("A1", [("P1", 2)])  # 2000, preferente
    assert servicio.validar(sol.id).cumple
    assert servicio.evaluar_beneficio(sol.id).aplica
    chica = servicio.crear("A1", [("P2", 1)])
    assert not servicio.evaluar_beneficio(chica.id).aplica


@pytest.mark.parametrize("rol,permiso,ok", [
    ("control_escolar", Permiso.APROBAR, True),
    ("estudiante", Permiso.APROBAR, False),
    ("instructor", Permiso.REGISTRAR_RESULTADO, True),
    ("estudiante", Permiso.REGISTRAR_RESULTADO, False),
    ("administracion", Permiso.VER_REPORTES, True),
    ("cliente_empresarial", Permiso.CREAR_SOLICITUD, True),
    ("cliente_empresarial", Permiso.CANCELAR, False),
])
def test_permisos_rb14(rol, permiso, ok):
    if ok:
        autorizar(rol, permiso)
    else:
        with pytest.raises(PermisoDenegado):
            autorizar(rol, permiso)


def test_rol_desconocido():
    with pytest.raises(PermisoDenegado):
        autorizar("hacker", Permiso.APROBAR)
