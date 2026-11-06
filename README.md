# EduTechAcademy — PIA Componentes de Lógica de Negocio

Sistema de inscripción, seguimiento y certificación de cursos. Implementa **DDD + Specification + State Machine + API REST** sobre el análisis de las Unidades 2 y 3 (BRD, User Stories/Gherkin, BPMN, glosario, ADRs).

| | |
|---|---|
| **Repositorio** | https://github.com/Vale-Ord/EduTechAcademy_PIA |
| **Sistema desplegado (Swagger)** | https://edutech-academy-api-6s0l.onrender.com/docs |
| **Equipo** | Valeria Ordaz García (2169894) · Luis José Mendoza Serrano (2223173) · Omar Alejandro Salazar Castro (2226576) |

## Estructura
```
docs/            BRD.md, user_stories_gherkin.md, trazabilidad.md, mapeo_maestro.md,
                 architecture/ (ADRs, diagramas), api/ (OpenAPI), evidencias/
src/domain/      entidades, Value Objects, Specification, State Machine, eventos
src/application/ SolicitudService, permisos por rol (RB-14), puertos
src/infrastructure/ SQLAlchemy, repositorios, carga de CSV, configuración
src/api/         FastAPI (endpoints, schemas, errores HTTP)
tests/           unit/ + integration/
data/            CSV del maestro (40 actores, 20 programas, 60 operaciones)
```

## Ejecutar sin Docker (SQLite)
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
SEED_ON_STARTUP=true uvicorn src.api.main:app --reload     # Windows PowerShell: $env:SEED_ON_STARTUP="true"; uvicorn src.api.main:app --reload
```
Abrir http://localhost:8000/docs.

## Ejecutar con Docker Compose (PostgreSQL)
```bash
cp .env.example .env                     # Windows: copy .env.example .env
docker compose up --build                # DB + API en http://localhost:8000/docs
docker compose run --rm tests            # pruebas + cobertura >= 80% contra otro PostgreSQL
```

## Pruebas, cobertura y lint
```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
ruff check .
python scripts/ejecutar_casos.py          # 120 casos + 20 transiciones del maestro -> docs/evidencias/
python scripts/export_openapi.py          # docs/api/openapi.json
```

## Demostración rápida (Swagger, rol `control_escolar`)
1. `GET /programas` → ver catálogo y cupos.
2. `POST /solicitudes` → `{"actor_id":"EDU-C005","renglones":[{"programa_id":"EDU-P001","cantidad":2}]}`.
3. `GET /solicitudes/{id}/validacion` y `/beneficio` → Specifications con motivos.
4. `POST /solicitudes/{id}/aprobar` → ACEPTADA (reserva cupo). Repetirlo → **409** (State Machine).
5. `POST /solicitudes/{id}/pago` con el total → INSCRITA. Con otro monto → **422**.
6. Cambiar `X-Rol` a `instructor` → `PUT /solicitudes/{id}/resultado` `{"calificacion":"85","asistencia":"90"}`.
7. `POST /solicitudes/{id}/completar` → FINALIZADA; `GET /solicitudes/{id}/certificacion` → Elegible.
8. `GET /solicitudes/{id}/eventos` → Domain Events.
9. Con `X-Rol: estudiante` intentar aprobar → **403** (RB-14).

## Despliegue (Render)
1. Subir el repo a GitHub.
2. En Render: **New → Blueprint** → elegir el repo (usa `render.yaml`: crea PostgreSQL y el servicio web).
3. Cuando termine, abrir `https://<servicio>.onrender.com/docs`.
4. CD: en Render copiar el **Deploy Hook** del servicio y guardarlo en GitHub → Settings → Secrets → `RENDER_DEPLOY_HOOK_URL`.

## Códigos HTTP
201 creación · 400 dato inválido · 403 sin permiso · 404 no existe · 409 transición inválida/cupo agotado · 422 regla no cumplida o esquema inválido.

## Alcance y limitaciones declaradas
Implementado: US-01, 02, 03, 04, 05, 06, 09, 10, 12, 13, 15, 18 (y parcial 08, 11, 17). Pendientes: cambio de grupo (US-14), sustitución de instructor (US-16), agregado Instructor/Grupo (US-07). Concurrencia optimista (ADR-006) no implementada. Ver `docs/user_stories_gherkin.md`.
