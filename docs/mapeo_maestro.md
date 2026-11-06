# Mapeo entre el paquete del maestro y el análisis propio (BRD / U3)

El maestro indicó que su paquete es un **modelo de pruebas propuesto** y que, si difiere de nuestros requerimientos, hay que **documentar las diferencias** y adaptar fixtures y oráculos. Este documento es esa evidencia.

## 1. Vocabulario
| Paquete del maestro | EduTechAcademy (BRD / U3) | En el código |
|---|---|---|
| actor (`EDU-C###`) | Estudiante | `Alumno` |
| recurso / programa (`EDU-P###`) | Curso + Grupo con Cupo | `Programa` (precio + `Cupo`) |
| `capacidad_o_stock` | Capacidad máxima del grupo (RB-02) | `Cupo.capacidad` |
| `habilitado` | El grupo admite inscripciones | `Programa.habilitado` |
| operación (`EDU-O###`) | Solicitud de inscripción (SUP-14, SUP-16) | `Solicitud` (Aggregate Root) |
| renglón (`detalle_operaciones`) | Lugares solicitados en un programa | `LineaSolicitud` |
| `cantidad` | Lugares / participantes | `LineaSolicitud.cantidad` |
| `autorizado` | Autorización de Control Escolar | `Solicitud.autorizado` |
| `es_preferente` | (no existe en el BRD) | `Alumno.es_preferente` — SUP-18 |
| `promocion_activa` | (no existe en el BRD) | `Solicitud.promocion_activa` — SUP-18 |

## 2. Equivalencia de estados
| Maestro | U3 `EstadoInscripción` | Significado |
|---|---|---|
| SOLICITADA | Pendiente | Solicitud recibida, sin aprobar ni pagar |
| ACEPTADA | Pendiente (con lugar reservado, SUP-11) | Control Escolar validó reglas y reservó cupo; falta el pago |
| INSCRITA | Confirmada (RB-03) | Pago exacto recibido |
| FINALIZADA | (Grupo Finalizado, SUP-10) | Terminó el curso; se puede evaluar certificación |
| CANCELADA | Cancelada / GrupoCancelado (RB-10) | Libera el lugar |

Transiciones válidas (`src/domain/estados.py`): aprobar S→A · inscribir A→I · completar I→F · cancelar S/A/I→C. Todo lo demás lanza `TransicionInvalida` (HTTP 409).

## 3. Reglas del maestro vs reglas propias
| Regla del maestro | Specification | Relación con el BRD |
|---|---|---|
| `puede_procesarse` = actor activo AND ≥1 renglón AND autorización | `puede_procesarse()` | Se parece a RB-01/RB-14 (requisitos + permiso de Control Escolar) |
| `beneficio_referencia` = preferente AND total ≥ 1500 AND NOT promoción | `beneficio_referencia()` | **No existe en el BRD**; se documenta como SUP-18 |
| (propia) programas habilitados | `ProgramasHabilitados` | RB-02/RES-01/ALC-04 |
| (propia) calificación ≥ 70 AND asistencia ≥ 80 | `cumple_certificacion()` | RB-06, RB-07, RB-08 |
| Cupo suficiente | `CupoSuficiente` / `Cupo.ocupar` | RB-02, RES-01 |

`aprobar` exige `puede_aceptarse() = puede_procesarse() AND ProgramasHabilitados`. Los casos `validar_operacion` del maestro se verifican contra `puede_procesarse()` **sin** el extra de programas deshabilitados, para respetar su oráculo.

## 4. Interpretación de las 5 acciones de `transiciones_prueba.csv`
Todas parten de SOLICITADA y cada caso corre sobre datos limpios.
| Acción | Qué ejecuta nuestro sistema | Resultado esperado |
|---|---|---|
| `aprobar` | `aprobar()` | ACEPTADA + `SolicitudAceptada`; o 422 si no cumple reglas; o 409 si no hay cupo |
| `repetir_aprobacion` | `aprobar()` dos veces | La segunda falla con `TransicionInvalida` (409); si la primera ya falla por reglas, 422 |
| `saltar_estado` | `inscribir()` sin aprobar | `TransicionInvalida` (409), el estado no cambia |
| `completar` | `completar()` desde SOLICITADA | `TransicionInvalida` (409): se exige estar INSCRITA |
| `cancelar` | `cancelar()` | CANCELADA + `SolicitudCancelada` |

## 5. Casos límite de los datos (para la defensa)
- 5 operaciones de alumnos inactivos → `puede_procesarse` falsa.
- 7 operaciones no autorizadas → falsa.
- 2 operaciones sin renglones (EDU-O013, EDU-O039) → falsa.
- 1 programa deshabilitado (EDU-P011) → no se puede aceptar (422).
- 6 operaciones con promoción activa → el beneficio no aplica.
- El umbral exacto de $1,500 casi no aparece en los datos, por eso se agregó una prueba propia (`test_beneficio_en_el_umbral_exacto`: 1499.99 / 1500 / 1500.01).

## 6. Evidencia
`python scripts/ejecutar_casos.py` genera `docs/evidencias/resultados_casos.csv` (120 casos) y `resultados_transiciones.csv` (20 casos), y `tests/unit/test_casos_maestro.py` los compara contra un **oráculo independiente** (recalculado solo con `csv` y `Decimal`).
