# ADR-013: FastAPI + SQLAlchemy + PostgreSQL, Docker Compose y despliegue en Render

**Estado:** Aceptada

## Contexto
El PIA exige API REST con OpenAPI, base de datos, Docker Compose (DB + App + Tests), variables de entorno y despliegue con Swagger activo. El equipo ya usó FastAPI y SQLAlchemy en U4/U5.

## Decisión
- **FastAPI**: genera OpenAPI/Swagger automáticamente (`/docs`).
- **SQLAlchemy 2.0** con repositorios que traducen ORM ↔ dominio; **PostgreSQL** en Compose y producción, **SQLite en memoria** para pruebas rápidas (las pruebas de integración también corren contra PostgreSQL en CI y en `docker compose run tests`).
- **Configuración por entorno** (`DATABASE_URL`, `SEED_ON_STARTUP`, `APP_ENV`) según 12-Factor; `.env.example` sin secretos.
- **Render** (Blueprint `render.yaml`) construye la imagen del `Dockerfile` y crea la base gratuita; CD mediante deploy hook desde GitHub Actions.
- **Códigos HTTP**: 201 creación · 400 dato inválido · 403 sin permiso · 404 no existe · 409 transición inválida/cupo agotado · 422 regla no cumplida o esquema inválido.

## Alternativas
Flask/Django (más código o más pesado), Railway/Fly.io (equivalentes; Render tiene Blueprint simple), SQLite en producción (no demuestra DB real).

## Consecuencias
(+) Entorno reproducible con un comando. (−) El plan gratuito de Render duerme el servicio tras inactividad: abrir `/docs` antes de la demo.
