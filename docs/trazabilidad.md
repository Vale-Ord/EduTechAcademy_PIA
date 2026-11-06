# Matriz de trazabilidad: BRD → regla → componente → prueba

| BRD | Regla / requisito | Componente (código) | Prueba |
|---|---|---|---|
| RB-01 / RES-02 | Alumno activo, solicitud con renglones y autorizada | `especificaciones.puede_procesarse()` | `test_especificaciones::test_puede_procesarse_*`, `test_casos_maestro` (60 casos `validar_operacion`) |
| RB-02 / RES-01 | No exceder capacidad | `valores.Cupo.ocupar`, `especificaciones.CupoSuficiente`, `servicios.aprobar` | `test_valores::test_cupo_*`, `test_servicio::test_aprobar_sin_cupo_409…`, `test_servicio::test_ultimo_lugar…`, `test_api::test_409_cupo_agotado` |
| RB-03 / RES-06 | Confirmar solo con pago exacto | `servicios.inscribir`, `estados.INSCRIBIR` | `test_servicio::test_pago_debe_ser_exacto`, `test_api::test_422_pago_incorrecto` |
| RB-04 / RB-05 | Solo el instructor registra asistencia y evaluaciones | `permisos.Permiso.REGISTRAR_RESULTADO` | `test_servicio::test_permisos_rb14`, `test_api::test_403_permisos_rb14` |
| RB-06 | Asistencia ≥ 80 % | `valores.PorcentajeAsistencia.cumple_minimo` | `test_valores::test_asistencia_cumple_minimo_en_el_umbral` |
| RB-07 | Calificación ≥ 70 | `valores.Calificacion.aprueba` | `test_valores::test_calificacion_aprueba_en_el_umbral` |
| RB-08 | Certificado = 70 y 80 % | `especificaciones.cumple_certificacion()`, `servicios.evaluar_certificacion` | `test_especificaciones::test_certificacion_rb08`, `test_servicio::test_flujo_completo_feliz` |
| RB-12 / RB-13 | No elegible por calificación / asistencia | `servicios.evaluar_certificacion` (motivo) | `test_servicio::test_no_elegible_con_motivo` |
| RB-10 | Cancelación libera lugar | `servicios.cancelar`, `estados.CANCELAR` | `test_servicio::test_cancelar_libera_cupo`, `test_repositorio_sql::test_cancelar_libera_cupo_persistido` |
| RB-14 / RES-04 | Permisos por rol | `application/permisos.py`, header `X-Rol` | `test_servicio::test_permisos_rb14`, `test_api::test_403…` |
| RES-05 / SUP-06 | Historial/trazabilidad | `eventos.py`, tabla `eventos_dominio`, `GET /solicitudes/{id}/eventos` | `test_api::test_flujo_completo_por_http` |
| SUP-10 | Certificación solo con grupo finalizado | `servicios.evaluar_certificacion` devuelve Pendiente | `test_servicio::test_no_elegible_con_motivo` |
| SUP-11 | Pendiente ocupa lugar; cancelar libera | `servicios.aprobar/cancelar` | `test_servicio::test_cancelar_libera_cupo` |
| SUP-14 / US-18 | Solicitud con varios participantes | `Solicitud.lineas`, `LineaSolicitud.cantidad` | `test_servicio::test_aprobar_sin_cupo_409…` |
| SUP-18 (maestro) | Beneficio de referencia | `especificaciones.beneficio_referencia()` | `test_especificaciones::test_beneficio_*`, `test_casos_maestro` (60 casos `evaluar_beneficio`) |
| SUP-17 (maestro) | State Machine | `estados.MaquinaEstados` | `test_maquina_estados`, `test_casos_maestro` (20 transiciones) |
| ADR-007 | Eventos tras commit | `servicios._cerrar` | `test_servicio::test_flujo_completo_feliz` |
| ADR-010 | Precio fijado al solicitar | `servicios.crear` copia `programa.precio` a `LineaSolicitud` | `test_repositorio_sql::test_guardar_y_recuperar_solicitud` |

| User Story | Endpoint | Prueba |
|---|---|---|
| US-01 | `GET /programas` | `test_api::test_listar_programas_y_404` |
| US-02 | `POST /solicitudes` + aprobar + pago | `test_api::test_flujo_completo_por_http` |
| US-03, US-12, US-15 | `GET /solicitudes` | `test_api::test_filtros_de_solicitudes_pagos_pendientes` |
| US-06, US-13 | `GET /solicitudes/{id}/certificacion` | `test_api::test_flujo_completo_por_http` |
| US-09, US-10 | `PUT /solicitudes/{id}/resultado` | `test_api::test_resultado_antes_de_inscribir_422` |
| US-18 | `POST /solicitudes` | `test_api::test_flujo_completo_por_http` (cantidad = 2) |

> Mantener esta matriz al día: si agregan una regla o endpoint, agreguen su fila.
