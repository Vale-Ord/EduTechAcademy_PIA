# User Stories con criterios de aceptación Gherkin (18)

Estado: ✅ implementado y probado · 🟡 parcial · ⏳ pendiente de implementar (ver `docs/PLAN_EQUIPO.md`).
Rol = valor del encabezado `X-Rol` (RB-14).

| US | Rol | Endpoint(s) | Estado |
|---|---|---|---|
| US-01 | estudiante | `GET /programas` | ✅ |
| US-02 | estudiante | `POST /solicitudes`, `POST /solicitudes/{id}/aprobar`, `POST /solicitudes/{id}/pago` | ✅ |
| US-03 | estudiante | `GET /solicitudes?actor_id=` | ✅ |
| US-04 | estudiante | `GET /solicitudes/{id}` (campo `asistencia`) | ✅ |
| US-05 | estudiante | `GET /solicitudes/{id}` (campo `calificacion_final`) | ✅ |
| US-06 | estudiante | `GET /solicitudes/{id}/certificacion` | ✅ |
| US-07 | instructor | — (requiere Aggregate Instructor/Grupo) | ⏳ |
| US-08 | instructor | `GET /solicitudes?estado=INSCRITA` | 🟡 (falta filtrar por programa) |
| US-09 | instructor | `PUT /solicitudes/{id}/resultado` (asistencia) | ✅ |
| US-10 | instructor | `PUT /solicitudes/{id}/resultado` (calificación) | ✅ |
| US-11 | instructor | `GET /solicitudes`, `GET /solicitudes/{id}/certificacion` | 🟡 |
| US-12 | control_escolar | `GET /solicitudes` | ✅ |
| US-13 | control_escolar | `GET /solicitudes/{id}/certificacion` | ✅ |
| US-14 | control_escolar | — (cambio de grupo) | ⏳ |
| US-15 | control_escolar | `GET /solicitudes?estado=ACEPTADA` | ✅ |
| US-16 | control_escolar | — (sustitución de instructor) | ⏳ |
| US-17 | administracion | `GET /programas` (cupos, REP-02) | 🟡 |
| US-18 | cliente_empresarial | `POST /solicitudes` con varios renglones (`cantidad` = participantes) | ✅ |

```gherkin
# language: es
Característica: US-01 Consultar cursos disponibles
  Escenario: El estudiante ve los programas habilitados
    Dado que existen programas en el catálogo
    Cuando el estudiante consulta los programas con solo_habilitados=true
    Entonces recibe la lista de programas habilitados con precio y lugares disponibles

Característica: US-02 Inscripción a un curso
  Escenario: Inscripción exitosa (RB-01, RB-02, RB-03)
    Dado que el alumno está activo y existe cupo en el programa
    Cuando solicita inscribirse, Control Escolar aprueba y el pago es igual al total
    Entonces la solicitud queda INSCRITA y se publica el evento InscripcionConfirmada
  Escenario: Cupo agotado (RB-02)
    Dado que el programa no tiene lugares suficientes
    Cuando Control Escolar intenta aprobar la solicitud
    Entonces el sistema responde 409 CupoAgotado y no reserva ningún lugar
  Escenario: Pago incorrecto (RB-03)
    Dado que la solicitud está ACEPTADA
    Cuando se registra un pago distinto al total
    Entonces el sistema responde 422 y la solicitud sigue ACEPTADA

Característica: US-03 Consultar mis cursos inscritos
  Escenario: Lista de solicitudes del alumno
    Dado que el alumno tiene solicitudes registradas
    Cuando consulta GET /solicitudes?actor_id=<su id>
    Entonces ve cada solicitud con su estado, renglones y total

Característica: US-04 Consultar mi asistencia
  Escenario: Porcentaje acumulado
    Dado que el estudiante está inscrito y el instructor registró su asistencia
    Cuando consulta su solicitud
    Entonces ve su porcentaje de asistencia registrado

Característica: US-05 Consultar mis evaluaciones
  Escenario: Calificación final
    Dado que el instructor registró la calificación del estudiante
    Cuando consulta su solicitud
    Entonces ve su calificación final de 0 a 100

Característica: US-06 Estado de certificación
  Escenario: Elegible en el umbral (RB-06, RB-07, RB-08)
    Dado un grupo FINALIZADO con calificación 70 y asistencia 80
    Cuando el estudiante consulta su certificación
    Entonces el estado es Elegible
  Escenario: No elegible por calificación (RB-12)
    Dado un grupo FINALIZADO con calificación 69 y asistencia 100
    Cuando consulta su certificación
    Entonces el estado es No elegible con motivo Calificación
  Escenario: No elegible por asistencia (RB-13)
    Dado un grupo FINALIZADO con calificación 100 y asistencia 79
    Cuando consulta su certificación
    Entonces el estado es No elegible con motivo Asistencia

Característica: US-07 Consultar mis cursos asignados
  Escenario: Cursos del instructor
    Dado que el instructor tiene grupos asignados (SUP-02)
    Cuando consulta sus cursos
    Entonces ve únicamente los grupos donde es el instructor vigente

Característica: US-08 Consultar estudiantes inscritos (instructor)
  Escenario: Lista de inscritos
    Dado que existen solicitudes INSCRITAS
    Cuando el instructor consulta GET /solicitudes?estado=INSCRITA
    Entonces ve los estudiantes inscritos

Característica: US-09 Registro de asistencia
  Escenario: El instructor registra asistencia
    Dado que la inscripción está confirmada
    Cuando el instructor registra la asistencia
    Entonces queda asociada a la solicitud del estudiante
  Escenario: Solo con inscripción confirmada (RES-03/RES-07)
    Dado que la solicitud sigue SOLICITADA
    Cuando el instructor intenta registrar asistencia
    Entonces el sistema responde 422
  Escenario: Permiso por rol (RB-04, RB-14)
    Cuando un estudiante intenta registrar asistencia
    Entonces el sistema responde 403

Característica: US-10 Registro de evaluación
  Escenario: El instructor registra calificación
    Dado que la inscripción está confirmada
    Cuando el instructor registra una calificación entre 0 y 100
    Entonces queda asociada a la solicitud del estudiante
  Escenario: Calificación fuera de rango
    Cuando se envía una calificación de 101
    Entonces el sistema responde 422

Característica: US-11 Consultar resultados de los estudiantes
  Escenario: Resultados del grupo
    Dado que hay calificaciones registradas
    Cuando el instructor consulta las solicitudes
    Entonces ve calificación y asistencia de cada estudiante

Característica: US-12 Consultar estudiantes inscritos (Control Escolar)
  Escenario: Administrar grupos
    Cuando Control Escolar consulta GET /solicitudes
    Entonces ve todas las solicitudes y puede filtrar por estado o alumno

Característica: US-13 Validación de certificación
  Escenario: Cumple ambos criterios (RB-08)
    Dado un estudiante con calificación >= 70 y asistencia >= 80 y grupo FINALIZADO
    Cuando Control Escolar valida
    Entonces se identifica como candidato elegible
  Escenario: No cumple alguno
    Dado un estudiante que no cumple alguno de los dos criterios
    Cuando Control Escolar valida
    Entonces se identifica como no elegible con el motivo

Característica: US-14 Cambio de grupo
  Escenario: Cambio autorizado (RB-09)
    Dado que el nuevo grupo tiene cupo y Control Escolar autoriza
    Cuando se registra el cambio
    Entonces el estudiante queda en el nuevo grupo y se conserva el grupo anterior

Característica: US-15 Pago pendiente
  Escenario: Identificar inscripciones sin pago (RB-03, SUP-11)
    Dado una solicitud ACEPTADA sin pago
    Cuando Control Escolar consulta GET /solicitudes?estado=ACEPTADA
    Entonces el estudiante aparece como pago pendiente

Característica: US-16 Sustitución de instructor
  Escenario: Registrar nuevo instructor (RB-11)
    Dado un grupo con instructor vigente
    Cuando Control Escolar registra a otro instructor
    Entonces el grupo muestra al nuevo y conserva el registro del anterior

Característica: US-17 Reportes de cursos y estudiantes
  Escenario: Cupos por programa (REP-02)
    Cuando Administración consulta GET /programas
    Entonces ve capacidad, ocupados y disponibles de cada programa

Característica: US-18 Capacitación empresarial
  Escenario: La empresa registra participantes (SUP-14)
    Dado un cliente empresarial
    Cuando solicita una capacitación con cantidad = número de participantes
    Entonces se crea una solicitud SOLICITADA cuyo total es precio x participantes
```
