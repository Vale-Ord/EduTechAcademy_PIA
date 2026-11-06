# BRD — EduTechAcademy (versión integrada para el PIA)

> Base: BRD de la Unidad 2 y refinamientos de la Unidad 3 (SUP-09 a SUP-15).
> Equipo: Valeria Ordaz García (2169894) · Luis José Mendoza Serrano (2223173) · Omar Alejandro Salazar Castro (2226576).
> Curso: Componentes de Lógica de Negocio. Docente: Miguel Ángel Gómez Marroquín.

## 1. Información general
EduTechAcademy ofrece cursos de capacitación y educación continua, presenciales y en línea, a estudiantes individuales y a clientes empresariales. El proceso va desde la inscripción hasta la impartición, el registro de asistencia y evaluaciones y, si se cumplen los criterios, la certificación.

## 2. Problema actual
| ID | Problema |
|---|---|
| PA-01 | Validación manual de certificados (pérdida de tiempo y errores). |
| PA-02 | Errores al consolidar asistencia y calificaciones. |
| PA-03 | Dificultad para rastrear cambios de grupo. |
| PA-04 | Dificultad para identificar candidatos a certificación. |

## 3. Stakeholders
Estudiante · Instructor · Control Escolar · Administración · Cliente empresarial.

## 4. Necesidades del negocio
BN-01 Gestionar inscripciones · BN-02 Controlar cupo · BN-03 Seguimiento de pagos · BN-04 Asistencia · BN-05 Evaluaciones · BN-06 Criterios académicos · BN-07 Asistencia mínima · BN-08 Validar candidatos a certificación · BN-09 Trazabilidad de cambios de grupo · BN-10 Sustituciones de instructor · BN-11 Situaciones excepcionales · BN-12 Reportes.

## 5. Alcance
ALC-01 Cursos · ALC-02 Grupos · ALC-03 Inscripción · ALC-04 Control de cupo · ALC-05 Seguimiento de pagos · ALC-06 Asistencia · ALC-07 Evaluaciones · … · ALC-14 Capacitación empresarial.
**Fuera de alcance:** FAL-01 nómina · FAL-02 contratación de instructores · FAL-03 contabilidad general · FAL-04 recursos humanos · FAL-05 otros procesos administrativos.

## 6. Reglas de negocio
| ID | Regla |
|---|---|
| RB-01 | El estudiante debe cumplir los requisitos del curso antes de inscribirse. |
| RB-02 | No se inscribe a un grupo que alcanzó su capacidad máxima. |
| RB-03 | La inscripción no queda confirmada hasta que el pago se haya realizado. |
| RB-04 | El instructor registra la asistencia. |
| RB-05 | El instructor registra las evaluaciones. |
| RB-06 | Asistencia mínima de 80 % para el criterio de certificación. |
| RB-07 | Calificación mínima de 70/100 para aprobar. |
| RB-08 | Certificado = calificación ≥ 70 **y** asistencia ≥ 80 %. |
| RB-09 | Cambio de grupo autorizado por Control Escolar, con cupo en el nuevo grupo y conservando el grupo anterior. |
| RB-10 | Curso cancelado: se notifica y el estudiante elige reembolso o transferencia. |
| RB-11 | Sustitución de instructor: se registra al nuevo y se conserva el anterior. |
| RB-12 | Reprobado: sin certificado; puede reinscribirse en otra edición. |
| RB-13 | Asistencia insuficiente: sin certificado aunque haya aprobado. |
| RB-14 | Permisos por rol (tabla siguiente). |

### RB-14 — Permisos por rol
| Rol | Permisos |
|---|---|
| Estudiante | Consultar cursos, inscripciones, asistencia, evaluaciones y estado de certificación. |
| Instructor | Consultar sus cursos y estudiantes inscritos; registrar asistencia y evaluaciones; consultar resultados. |
| Control Escolar | Gestionar inscripciones y cambios de grupo; pagos pendientes; información académica; validar certificación; sustituciones de instructor. |
| Administración | Consultar información general y reportes. |
| Cliente empresarial | Solicitar capacitación y proporcionar datos de participantes. |

## 7. Restricciones
RES-01 capacidad de grupos · RES-02 requisitos del curso · RES-03 criterios de certificación · RES-04 permisos por rol · RES-05 trazabilidad de cambios · RES-06 estado del pago · RES-07 registro académico.

## 8. Supuestos
SUP-01 a SUP-08 (BRD U2: grupos por curso, instructor asignado, registro de asistencia y evaluaciones, validación por Control Escolar, historial de cambios, operaciones por rol, capacitación empresarial).

| ID | Supuesto (U3) |
|---|---|
| SUP-09 | Calificación final = promedio simple de evaluaciones (0–100). |
| SUP-10 | % asistencia = sesiones con presencia / sesiones registradas; certificación se evalúa con el grupo Finalizado. |
| SUP-11 | La inscripción pendiente de pago ocupa un lugar; se libera al cancelar o cambiar de grupo. |
| SUP-12 | Un estudiante no tiene dos inscripciones activas en el mismo grupo. |
| SUP-13 | Un pago rechazado no cambia el estado. |
| SUP-14 | Al aceptar una solicitud empresarial, cada participante genera Estudiante + Inscripción. |
| SUP-15 | Los requisitos son texto verificado por la política de inscripción o Control Escolar. |

### Supuestos nuevos del PIA (requeridos por el paquete del maestro)
| ID | Supuesto | Origen |
|---|---|---|
| SUP-16 | Una **operación** del maestro = **Solicitud de inscripción**: un alumno pide lugares en uno o más programas; `cantidad` = lugares (SUP-14: varios participantes). | `docs/mapeo_maestro.md` |
| SUP-17 | Estados de implementación: SOLICITADA → ACEPTADA → INSCRITA → FINALIZADA (o CANCELADA). Se mapean a EstadoInscripción de U3. | `docs/mapeo_maestro.md` |
| SUP-18 | Un **alumno preferente** con total ≥ $1,500 MXN y sin promoción activa califica para el *beneficio de referencia* (regla de prueba del maestro; el BRD original no tiene descuentos). Se implementa como Specification, no altera precios. | Paquete del maestro |
| SUP-19 | Un programa deshabilitado no admite solicitudes aceptadas (RB-02/RES-01 + ALC-04). | Dato `habilitado` del catálogo |
| SUP-20 | El pago debe ser exactamente igual al total de la solicitud (RB-03). Un curso con total 0 queda por confirmar. | U5 (TC-PAGO-03) |

## 9. Reportes (REP-01 a REP-10)
Inscritos por curso · cupos por grupo · asistencia · resultados · pagos pendientes · cumplen criterios · no cumplen · cambios de grupo · info de cursos · capacitación empresarial.

## 10. Criterios de éxito y prioridades
Prioridad alta: facilitar validación de certificaciones, reducir errores de asistencia/calificaciones, identificar rápidamente candidatos, seguimiento de cambios de grupo. Prioridad media: pagos pendientes y acceso a información académica.
