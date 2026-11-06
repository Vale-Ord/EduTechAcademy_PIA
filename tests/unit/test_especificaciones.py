from decimal import Decimal

import pytest

from src.domain.entidades import Alumno, ContextoOperacion, Programa, Solicitud
from src.domain.especificaciones import (
    AlumnoActivo,
    AlumnoPreferente,
    PromocionActiva,
    TotalMinimo,
    beneficio_referencia,
    cumple_certificacion,
    puede_aceptarse,
    puede_procesarse,
)
from src.domain.valores import Calificacion, Cupo, Dinero, LineaSolicitud, PorcentajeAsistencia
from datetime import date


def ctx(activo=True, pref=True, total=1500, promo=False, autorizado=True, lineas=True, habilitado=True):
    alumno = Alumno("A", "x", es_preferente=pref, activo=activo)
    prog = Programa("P", "p", Dinero(total), Cupo(10, 0, "P"), habilitado=habilitado)
    sol = Solicitud("S", "A", date(2026, 1, 1), promocion_activa=promo, autorizado=autorizado)
    if lineas:
        sol.lineas.append(LineaSolicitud("P", 1, prog.precio))
    return ContextoOperacion(sol, alumno, {"P": prog})


def test_puede_procesarse_ok():
    assert puede_procesarse().is_satisfied_by(ctx())


@pytest.mark.parametrize("kw,motivo", [
    ({"activo": False}, "alumno activo"),
    ({"autorizado": False}, "solicitud autorizada"),
    ({"lineas": False}, "al menos un renglón"),
])
def test_puede_procesarse_falla_con_motivo(kw, motivo):
    c = ctx(**kw)
    assert not puede_procesarse().is_satisfied_by(c)
    assert any(motivo in m for m in puede_procesarse().motivos_fallo(c))


@pytest.mark.parametrize("total,esperado", [("1499.99", False), ("1500", True), ("1500.01", True)])
def test_beneficio_en_el_umbral_exacto(total, esperado):  # caso límite propio
    assert beneficio_referencia().is_satisfied_by(ctx(total=Decimal(total))) is esperado


def test_beneficio_no_aplica_con_promocion_o_sin_preferente():
    assert not beneficio_referencia().is_satisfied_by(ctx(promo=True))
    assert not beneficio_referencia().is_satisfied_by(ctx(pref=False))


def test_combinadores_and_or_not():
    c = ctx(activo=True, pref=False)
    assert (AlumnoActivo() | AlumnoPreferente()).is_satisfied_by(c)
    assert not (AlumnoActivo() & AlumnoPreferente()).is_satisfied_by(c)
    assert (~AlumnoPreferente()).is_satisfied_by(c)
    assert not (~PromocionActiva() & TotalMinimo()).is_satisfied_by(ctx(promo=True))


def test_or_y_not_explican_el_fallo():
    c = ctx(activo=False, pref=False)
    assert (AlumnoActivo() | AlumnoPreferente()).motivos_fallo(c)
    assert (~AlumnoActivo()).is_satisfied_by(c)
    assert (~AlumnoPreferente()).motivos_fallo(ctx(pref=True))


def test_puede_aceptarse_exige_programa_habilitado():
    assert not puede_aceptarse().is_satisfied_by(ctx(habilitado=False))
    assert puede_aceptarse().is_satisfied_by(ctx())


@pytest.mark.parametrize("cal,asis,esperado", [
    (70, 80, True), (69, 100, False), (100, 79, False), (69, 79, False),
])
def test_certificacion_rb08(cal, asis, esperado):
    c = ctx()
    c.solicitud.calificacion_final = Calificacion(cal)
    c.solicitud.asistencia = PorcentajeAsistencia(asis)
    assert cumple_certificacion().is_satisfied_by(c) is esperado


def test_certificacion_sin_datos_no_cumple():
    assert not cumple_certificacion().is_satisfied_by(ctx())
