from decimal import Decimal

import pytest

from src.domain.excepciones import CantidadInvalida, CupoAgotado
from src.domain.valores import Calificacion, Cupo, Dinero, LineaSolicitud, PorcentajeAsistencia


@pytest.mark.parametrize("valor,esperado", [(69, False), ("69.9", False), (70, True), (100, True)])
def test_calificacion_aprueba_en_el_umbral(valor, esperado):  # RB-07
    assert Calificacion(valor).aprueba() is esperado


@pytest.mark.parametrize("valor,esperado", [(79, False), ("79.9", False), (80, True), (100, True)])
def test_asistencia_cumple_minimo_en_el_umbral(valor, esperado):  # RB-06
    assert PorcentajeAsistencia(valor).cumple_minimo() is esperado


@pytest.mark.parametrize("cls", [Calificacion, PorcentajeAsistencia])
@pytest.mark.parametrize("valor", [-1, 101])
def test_rangos_invalidos(cls, valor):
    with pytest.raises(CantidadInvalida):
        cls(valor)


def test_cupo_ocupar_y_liberar_son_inmutables():  # RB-02
    c = Cupo(2, 0, "P")
    c2 = c.ocupar(2)
    assert c.ocupados == 0 and c2.ocupados == 2 and not c2.hay_lugar()
    assert c2.liberar(1).disponibles == 1


def test_cupo_agotado():  # TC-CUPO-02
    with pytest.raises(CupoAgotado):
        Cupo(1, 1, "P").ocupar(1)


def test_cupo_invalido():
    with pytest.raises(CantidadInvalida):
        Cupo(1, 2)
    with pytest.raises(CantidadInvalida):
        Cupo(5, 0).ocupar(0)


def test_dinero_decimal_y_no_negativo():
    assert Dinero("10.10").por(3).monto == Decimal("30.30")
    with pytest.raises(CantidadInvalida):
        Dinero(-1)


@pytest.mark.parametrize("cantidad", [0, -2])
def test_linea_cantidad_invalida(cantidad):
    with pytest.raises(CantidadInvalida):
        LineaSolicitud("P", cantidad, Dinero(10))
