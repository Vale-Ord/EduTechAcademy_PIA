# Plan de equipo (3 personas) y checklist de entrega

> Entrega: **6 de noviembre de 2026**. Este archivo es de trabajo interno; pueden borrarlo antes de la defensa.

## Paso 0 — Quien crea el repo (5 min)
```bash
# En GitHub: crear repo vacío (sin README), invitar a los 2 compañeros como Collaborators
cd edutech-academy-pia
git init -b main
git add .
git commit -m "feat: base del proyecto EduTechAcademy (dominio, API, docs)"
git remote add origin https://github.com/<USUARIO>/<REPO>.git
git push -u origin main
```
Los otros dos: `git clone https://github.com/<USUARIO>/<REPO>.git` y trabajar **cada uno en su rama** (`git checkout -b persona-b`), hacer commits pequeños y abrir Pull Request a `main`. Configuren su nombre real: `git config user.name "Tu Nombre"` y `git config user.email "tu-correo-de-github"` (si no, los commits no cuentan como suyos).

## Reparto
| | Persona A — Verificación y calidad | Persona B — Infraestructura y despliegue | Persona C — Documentación y defensa |
|---|---|---|---|
| **Hoy (mínimo para entregar)** | 1. Instalar y correr `pytest --cov` y corregir lo que falle. 2. Confirmar cobertura ≥ 80 %. 3. `ruff check .` en verde. 4. `python scripts/ejecutar_casos.py` y subir `docs/evidencias/`. | 1. `docker compose up --build` y probar `/docs`. 2. `docker compose run --rm tests`. 3. Desplegar en Render con el Blueprint. 4. Poner la URL en el README. 5. Guardar `RENDER_DEPLOY_HOOK_URL` en GitHub. 6. `python scripts/export_openapi.py` y subir `docs/api/openapi.json`. | 1. Copiar a `docs/architecture/` los ADR-001…010 y los diagramas UML de U3. 2. Copiar BPMN y glosario a `docs/`. 3. Revisar `docs/BRD.md` y `user_stories_gherkin.md` contra sus documentos originales. 4. Armar el **Reporte final PDF**. 5. Armar la **presentación**. |
| **Si sobra tiempo** | US-16: sustitución de instructor (nueva entidad + endpoint + pruebas) | US-14: cambio de grupo (entidad `CambioDeGrupo`, tabla, endpoint) | Ensayo de demo y de preguntas técnicas |
| **Commits sugeridos** | `test:` `fix:` | `ci:` `chore:` `docs(api):` | `docs:` |

Los tres deben hacer al menos un commit con su nombre y poder explicar todo el sistema en la defensa.

## Preguntas probables de la defensa (preparar respuesta)
1. ¿Dónde está el State Machine y qué pasa si intento saltar un estado? → `src/domain/estados.py`, HTTP 409.
2. ¿Cómo combinan Specifications? → `src/domain/especificaciones.py`, operadores `&`, `|`, `~`.
3. ¿Cómo se relaciona una regla del BRD con el código y la prueba? → `docs/trazabilidad.md`.
4. ¿Qué difiere del paquete del maestro? → `docs/mapeo_maestro.md`.
5. ¿Por qué los permisos no están en el dominio? → ADR-005, `application/permisos.py`.
6. ¿Dónde demuestran SOLID? → `docs/architecture/README.md` §6.
7. ¿Por qué se publican los eventos después del commit? → ADR-007, `servicios._cerrar`.
8. ¿Qué no implementaron? → US-07, US-14, US-16 y concurrencia optimista (declarado en README).

## Checklist final antes de subir
- [ ] CI en verde en GitHub Actions (badge o captura)
- [ ] URL de Render abre `/docs` y funciona el flujo del README
- [ ] README con URL del repo y del despliegue
- [ ] `.env.example` sin secretos; `.env` NO está en el repo
- [ ] `docs/api/openapi.json`, `docs/evidencias/*.csv` subidos
- [ ] Reporte PDF + presentación + ZIP con documentos (si la plataforma lo pide)
- [ ] Commits de los 3 integrantes visibles
