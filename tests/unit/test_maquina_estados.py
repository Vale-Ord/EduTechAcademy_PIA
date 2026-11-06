import pytest

from src.domain.estados import Accion, EstadoSolicitud as E, MaquinaEstados
from src.domain.excepciones import TransicionInvalida


@pytest.mark.parametrize("estado,accion,esperado", [
    (E.SOLICITADA, Accion.APROBAR, E.ACEPTADA),
    (E.ACEPTADA, Accion.INSCRIBIR, E.INSCRITA),
    (E.INSCRITA, Accion.COMPLETAR, E.FINALIZADA),
    (E.SOLICITADA, Accion.CANCELAR, E.CANCELADA),
    (E.ACEPTADA, Accion.CANCELAR, E.CANCELADA),
    (E.INSCRITA, Accion.CANCELAR, E.CANCELADA),
])
def test_transiciones_validas(estado, accion, esperado):
    assert MaquinaEstados.siguiente(estado, accion) == esperado


@pytest.mark.parametrize("estado,accion", [
    (E.SOLICITADA, Accion.INSCRIBIR),   # saltar_estado
    (E.SOLICITADA, Accion.COMPLETAR),
    (E.ACEPTADA, Accion.APROBAR),       # repetir_aprobacion
    (E.ACEPTADA, Accion.COMPLETAR),
    (E.FINALIZADA, Accion.CANCELAR),
    (E.CANCELADA, Accion.APROBAR),
    (E.CANCELADA, Accion.CANCELAR),
])
def test_transiciones_invalidas(estado, accion):
    with pytest.raises(TransicionInvalida):
        MaquinaEstados.siguiente(estado, accion)


def test_permitidas_por_estado():
    assert set(MaquinaEstados.permitidas(E.SOLICITADA)) == {Accion.APROBAR, Accion.CANCELAR}
    assert MaquinaEstados.permitidas(E.CANCELADA) == []
