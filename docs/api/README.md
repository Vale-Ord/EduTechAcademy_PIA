# API REST

- Swagger UI: `/docs` · OpenAPI: `/openapi.json`
- Exportar la especificación al repo (hacerlo una vez y tras cada cambio de endpoints):
  ```bash
  python scripts/export_openapi.py        # genera docs/api/openapi.json
  ```
- Encabezado `X-Rol` obligatorio en la práctica (por defecto `control_escolar`): `estudiante`, `instructor`, `control_escolar`, `administracion`, `cliente_empresarial`.

| Método y ruta | Rol(es) | Éxito | Errores |
|---|---|---|---|
| `GET /health` | — | 200 | — |
| `GET /programas`, `GET /programas/{id}` | todos | 200 | 403, 404 |
| `POST /solicitudes` | estudiante, control_escolar, cliente_empresarial | 201 | 403, 404, 422 |
| `GET /solicitudes?actor_id=&estado=` | estudiante, instructor, control_escolar, administracion | 200 | 403 |
| `GET /solicitudes/{id}` / `/eventos` | ídem | 200 | 403, 404 |
| `GET /solicitudes/{id}/validacion` / `/beneficio` | control_escolar | 200 | 403, 404 |
| `POST /solicitudes/{id}/aprobar` | control_escolar | 200 | 403, 404, 409, 422 |
| `POST /solicitudes/{id}/pago` | estudiante, control_escolar | 200 | 403, 404, 409, 422 |
| `POST /solicitudes/{id}/completar` | control_escolar | 200 | 403, 404, 409 |
| `POST /solicitudes/{id}/cancelar` | estudiante, control_escolar | 200 | 403, 404, 409 |
| `PUT /solicitudes/{id}/resultado` | instructor | 200 | 403, 404, 422 |
| `GET /solicitudes/{id}/certificacion` | estudiante, control_escolar | 200 | 403, 404 |
| `POST /admin/seed` | control_escolar | 200 | 403 |

## Mensajes en las respuestas
- Las respuestas de solicitudes, validación, beneficio, certificación, `/health` y `/admin/seed` incluyen un campo `mensaje` con una explicación en lenguaje claro del proceso realizado y el siguiente paso.
- Los errores de negocio devuelven `error`, `detalle` y `mensaje` (y `motivos` en 422).
- Las listas (`GET /programas`, `GET /solicitudes`, `/eventos`) no llevan `mensaje` para no cambiar su formato; su explicación está en la descripción de cada endpoint en Swagger.
