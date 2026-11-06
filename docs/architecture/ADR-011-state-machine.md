# ADR-011: State Machine explícita para la Solicitud de inscripción

**Estado:** Aceptada · **Reglas:** RB-03, RB-10, RES-06, SUP-11, SUP-17

## Contexto
En U3 el estado de la inscripción era un Value Object (`EstadoInscripción`) sin reglas de transición: cualquier código podía asignar cualquier estado. El paquete del maestro exige una máquina de estados con transiciones inválidas detectables (saltar un estado, repetir una aprobación).

## Decisión
Una **tabla de transiciones** `(estado, acción) → estado` en `src/domain/estados.py`, consultada por `MaquinaEstados`. La `Solicitud` solo cambia de estado mediante `aplicar(accion)`, que valida la transición y registra el Domain Event correspondiente. Estados: SOLICITADA, ACEPTADA, INSCRITA, FINALIZADA, CANCELADA.

## Alternativas consideradas
1. **`if/elif` dispersos en el servicio**: rápido, pero las reglas se duplican y no se pueden probar de forma aislada.
2. **Patrón State (una clase por estado)**: más extensible, pero con 5 estados y 4 acciones agrega ~10 clases sin beneficio.
3. **Librería externa (transitions)**: dependencia extra para un problema pequeño.

## Consecuencias
- (+) Toda transición inválida lanza `TransicionInvalida` → HTTP 409.
- (+) Fácil de probar con `parametrize` (`tests/unit/test_maquina_estados.py`).
- (−) Agregar un estado exige editar la tabla y las pruebas.
- Equivalencias con U3 en `docs/mapeo_maestro.md`.
