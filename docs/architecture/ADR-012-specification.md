# ADR-012: Patrón Specification para reglas de negocio

**Estado:** Aceptada · **Reglas:** RB-01, RB-02, RB-06/07/08, SUP-18, SUP-19

## Contexto
Las reglas (alumno activo, autorización, programas habilitados, cupo, beneficio, certificación) se combinan de formas distintas según el caso de uso y deben poder explicar por qué fallan.

## Decisión
Clase base `Specification` con `is_satisfied_by(ctx)` y operadores `&` (AND), `|` (OR), `~` (NOT), más `motivos_fallo(ctx)`. Las reglas simples son clases pequeñas; las reglas de negocio son composiciones: `puede_procesarse`, `beneficio_referencia`, `puede_aceptarse`, `cumple_certificacion`.

## Alternativas consideradas
1. **Métodos booleanos en las entidades**: mezclan reglas que involucran varios Aggregates (alumno + solicitud + programa) dentro de uno solo.
2. **Funciones sueltas**: no se combinan ni explican su fallo.
3. **Motor de reglas externo**: excesivo para este alcance.

## Consecuencias
- (+) Regla nueva = clase nueva (Abierto/Cerrado).
- (+) Respuesta 422 con `motivos` exactos.
- (−) Un poco más de código que un simple `if`.
