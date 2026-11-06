"""API REST de EduTechAcademy (FastAPI). Swagger UI en /docs, OpenAPI en /openapi.json."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, Query

from src.api import schemas as sc
from src.api.errores import registrar_manejadores
from src.application.permisos import Permiso, autorizar
from src.application.servicios import SolicitudService
from src.domain.entidades import Programa, Solicitud
from src.domain.estados import EstadoSolicitud
from src.infrastructure.config import Settings
from src.infrastructure.db import (
    crear_engine,
    crear_session_factory,
    crear_tablas,
    sembrar_si_vacio,
)
from src.infrastructure.repositorio_sql import (
    AlumnoRepoSQL,
    ProgramaRepoSQL,
    PublicadorSQL,
    SolicitudRepoSQL,
    UnidadDeTrabajoSQL,
)

DESCRIPCION = """
Sistema de **inscripción, seguimiento y certificación** de EduTechAcademy.

### Cómo usar esta documentación
1. Elige tu rol en el encabezado `X-Rol` (`estudiante`, `instructor`, `control_escolar`,
   `administracion`, `cliente_empresarial`). Cada rol puede hacer solo algunas acciones (**RB-14**).
2. Sigue el recorrido de una inscripción: **consultar programas → crear solicitud → aprobar →
   registrar pago → completar → certificación**.
3. Cada respuesta incluye un campo `mensaje` que explica, en lenguaje claro, qué proceso se realizó
   y cuál es el siguiente paso.

### Códigos de respuesta
`200/201` éxito · `400` dato inválido · `403` sin permiso · `404` no existe ·
`409` acción no válida en el estado actual o cupo agotado · `422` regla de negocio no cumplida.
"""

T_SISTEMA = "Estado del sistema"
T_PROGRAMAS = "Programas disponibles"
T_SOLICITUDES = "Solicitudes de inscripción"
T_REGLAS = "Validación de reglas"
T_TRANSICIONES = "Avance de la inscripción"
T_CERTIFICACION = "Resultados y certificación"

TAGS_METADATA = [
    {"name": T_SISTEMA,
     "description": "Comprueba que el servicio esté funcionando y carga los datos iniciales."},
    {"name": T_PROGRAMAS,
     "description": "Consulta los programas académicos, su precio y los lugares disponibles."},
    {"name": T_SOLICITUDES,
     "description": "Registra una solicitud de inscripción y consulta su estado y su historial."},
    {"name": T_REGLAS,
     "description": "Revisa si una solicitud cumple las reglas del negocio antes de procesarla."},
    {"name": T_TRANSICIONES,
     "description": "Mueve la inscripción de un paso al siguiente: aprobar, pagar, completar o cancelar."},
    {"name": T_CERTIFICACION,
     "description": "Registra calificación y asistencia, y consulta si el alumno puede certificarse."},
]

MENSAJES_ESTADO = {
    EstadoSolicitud.SOLICITADA: "Solicitud registrada. Está pendiente de aprobación por Control Escolar.",
    EstadoSolicitud.ACEPTADA: ("Solicitud aprobada y cupo reservado. Siguiente paso: registrar el pago "
                               "por el monto exacto del total."),
    EstadoSolicitud.INSCRITA: "Pago recibido. La inscripción quedó confirmada.",
    EstadoSolicitud.FINALIZADA: "El programa terminó. Ya se puede consultar la certificación.",
    EstadoSolicitud.CANCELADA: "Solicitud cancelada. El cupo reservado, si lo había, fue liberado.",
}

DESC_ERROR = {
    400: "Dato fuera de rango.",
    403: "Sin permiso: el rol indicado en `X-Rol` no puede realizar esta acción.",
    404: "No existe el recurso solicitado (programa, alumno o solicitud).",
    409: "La acción no es válida en el estado actual de la solicitud, o el cupo está agotado.",
    422: "Datos inválidos o regla de negocio no cumplida (ver `motivos`).",
}


def _errores(*codigos: int) -> dict:
    """Documenta en Swagger los errores posibles de un endpoint."""
    docs: dict = {}
    for codigo in codigos:
        docs[codigo] = {"description": DESC_ERROR[codigo]}
        if codigo != 422:  # el 422 también lo produce FastAPI con su propio formato
            docs[codigo]["model"] = sc.ErrorOut
    return docs


def _solicitud_out(s: Solicitud, mensaje: str | None = None) -> sc.SolicitudOut:
    return sc.SolicitudOut(
        id=s.id, actor_id=s.alumno_id, estado=s.estado.value, fecha_solicitud=s.fecha_solicitud,
        total=s.total.monto, promocion_activa=s.promocion_activa, autorizado=s.autorizado,
        referencia=s.referencia,
        renglones=[sc.RenglonOut(programa_id=ln.programa_id, cantidad=ln.cantidad,
                                 precio_unitario=ln.precio_unitario.monto, subtotal=ln.subtotal.monto)
                   for ln in s.lineas],
        acciones_permitidas=[a.value for a in s.acciones_permitidas()],
        calificacion_final=None if s.calificacion_final is None else s.calificacion_final.valor,
        asistencia=None if s.asistencia is None else s.asistencia.valor,
        mensaje=mensaje or MENSAJES_ESTADO[s.estado],
    )


def _programa_out(p: Programa) -> sc.ProgramaOut:
    return sc.ProgramaOut(id=p.id, descripcion=p.descripcion, precio_mxn=p.precio.monto,
                          capacidad=p.cupo.capacidad, ocupados=p.cupo.ocupados,
                          disponibles=p.cupo.disponibles, habilitado=p.habilitado)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.desde_entorno()
    engine = crear_engine(settings.database_url)
    session_factory = crear_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        crear_tablas(engine)
        if settings.seed_on_startup:
            with session_factory() as s:
                sembrar_si_vacio(s)
        yield

    app = FastAPI(title="EduTechAcademy API", version="1.0.0", description=DESCRIPCION,
                  openapi_tags=TAGS_METADATA, lifespan=lifespan)
    registrar_manejadores(app)

    def get_servicio():
        session = session_factory()
        try:
            yield SolicitudService(
                AlumnoRepoSQL(session), ProgramaRepoSQL(session), SolicitudRepoSQL(session),
                PublicadorSQL(session), UnidadDeTrabajoSQL(session),
            )
        finally:
            session.rollback()
            session.close()

    def rol(x_rol: str = Header(default="control_escolar", description="Rol del usuario (RB-14)")):
        return x_rol

    # ---- Sistema ---------------------------------------------------------
    @app.get("/health", tags=[T_SISTEMA], response_model=sc.HealthOut,
             summary="Verificar que el servicio funciona",
             description="Responde `ok` si la API está en línea. No requiere permisos especiales.")
    def health():
        return {"status": "ok", "entorno": settings.app_env,
                "mensaje": "El servicio está funcionando correctamente."}

    @app.post("/admin/seed", tags=[T_SISTEMA], response_model=sc.SeedOut,
              summary="Cargar los datos iniciales (solo si la base está vacía)",
              description="Carga los CSV del maestro (alumnos, programas y operaciones). "
                          "Si la base ya tiene datos, no hace nada. Solo Control Escolar.",
              responses=_errores(403))
    def seed(x_rol: str = Depends(rol)):
        autorizar(x_rol, Permiso.APROBAR)  # solo Control Escolar
        with session_factory() as s:
            sembrada = sembrar_si_vacio(s)
        mensaje = ("Datos iniciales cargados correctamente." if sembrada
                   else "La base de datos ya tenía información; no se cargó nada.")
        return {"sembrada": sembrada, "mensaje": mensaje}

    # ---- Programas (US-01) ----------------------------------------------
    @app.get("/programas", response_model=list[sc.ProgramaOut], tags=[T_PROGRAMAS],
             summary="Ver todos los programas",
             description="Lista el catálogo con precio y lugares disponibles. "
                         "Usa `solo_habilitados=true` para ocultar los programas cerrados.",
             responses=_errores(403))
    def listar_programas(solo_habilitados: bool = False, x_rol: str = Depends(rol),
                         svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_PROGRAMAS)
        return [_programa_out(p) for p in svc.listar_programas(solo_habilitados)]

    @app.get("/programas/{programa_id}", response_model=sc.ProgramaOut, tags=[T_PROGRAMAS],
             summary="Ver el detalle de un programa",
             description="Muestra el precio, la capacidad y los lugares que quedan de un programa.",
             responses=_errores(403, 404))
    def obtener_programa(programa_id: str, x_rol: str = Depends(rol),
                         svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_PROGRAMAS)
        return _programa_out(svc.obtener_programa(programa_id))

    # ---- Solicitudes (US-02, US-03, US-12, US-15, US-18) ------------------
    @app.post("/solicitudes", response_model=sc.SolicitudOut, status_code=201, tags=[T_SOLICITUDES],
              summary="Crear una solicitud de inscripción",
              description="Registra la solicitud de un alumno a uno o más programas. Queda en estado "
                          "`SOLICITADA` hasta que Control Escolar la apruebe. El precio se fija al "
                          "momento de solicitar.",
              responses=_errores(403, 404, 422))
    def crear_solicitud(datos: sc.SolicitudIn, x_rol: str = Depends(rol),
                        svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CREAR_SOLICITUD)
        sol = svc.crear(datos.actor_id, [(r.programa_id, r.cantidad) for r in datos.renglones],
                        datos.promocion_activa, datos.autorizado, datos.referencia)
        return _solicitud_out(
            sol, f"Solicitud {sol.id} registrada con éxito. Guarda este número para darle seguimiento; "
                 "ahora está pendiente de aprobación por Control Escolar.")

    @app.get("/solicitudes", response_model=list[sc.SolicitudOut], tags=[T_SOLICITUDES],
             summary="Ver solicitudes",
             description="Lista las solicitudes. Puedes filtrar por alumno (`actor_id`) o por estado "
                         "(`SOLICITADA`, `ACEPTADA`, `INSCRITA`, `FINALIZADA`, `CANCELADA`). "
                         "Por ejemplo, `estado=ACEPTADA` muestra los pagos pendientes.",
             responses=_errores(403))
    def listar_solicitudes(actor_id: str | None = None,
                           estado: str | None = Query(default=None, examples=["ACEPTADA"]),
                           x_rol: str = Depends(rol),
                           svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_SOLICITUDES)
        return [_solicitud_out(s) for s in svc.listar(actor_id, estado)]

    @app.get("/solicitudes/{solicitud_id}", response_model=sc.SolicitudOut, tags=[T_SOLICITUDES],
             summary="Ver el detalle y el estado de una solicitud",
             description="Muestra el estado actual, el total, los renglones y las acciones permitidas "
                         "(`acciones_permitidas`) para saber cuál es el siguiente paso.",
             responses=_errores(403, 404))
    def obtener_solicitud(solicitud_id: str, x_rol: str = Depends(rol),
                          svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_SOLICITUDES)
        return _solicitud_out(svc.obtener(solicitud_id))

    @app.get("/solicitudes/{solicitud_id}/eventos", response_model=list[sc.EventoOut],
             tags=[T_SOLICITUDES], summary="Ver el historial de una solicitud",
             description="Lista, en orden, los hechos que han ocurrido en la solicitud "
                         "(creada, aceptada, inscrita, etc.).",
             responses=_errores(403, 404))
    def eventos(solicitud_id: str, x_rol: str = Depends(rol),
                svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_SOLICITUDES)
        return [sc.EventoOut(evento=e.nombre, solicitud_id=e.solicitud_id,
                             ocurrido_en=e.ocurrido_en.isoformat()) for e in svc.eventos_de(solicitud_id)]

    # ---- Reglas (Specification) ------------------------------------------
    @app.get("/solicitudes/{solicitud_id}/validacion", response_model=sc.ValidacionOut, tags=[T_REGLAS],
             summary="Revisar si la solicitud cumple las reglas",
             description="Comprueba, sin modificar nada, si la solicitud puede procesarse "
                         "(alumno activo, programa habilitado, etc.) y explica los motivos si no.",
             responses=_errores(403, 404))
    def validar(solicitud_id: str, x_rol: str = Depends(rol),
                svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.VALIDAR_SOLICITUD)
        r = svc.validar(solicitud_id)
        mensaje = ("La solicitud cumple todas las reglas y puede procesarse." if r.cumple
                   else "La solicitud no cumple las reglas para procesarse. Revisa los motivos.")
        return sc.ValidacionOut(solicitud_id=r.solicitud_id, cumple=r.cumple, motivos=r.motivos,
                                mensaje=mensaje)

    @app.get("/solicitudes/{solicitud_id}/beneficio", response_model=sc.BeneficioOut, tags=[T_REGLAS],
             summary="Consultar si aplica el beneficio por referencia",
             description="Indica si la solicitud califica para el beneficio de referencia, "
                         "sin modificar nada.",
             responses=_errores(403, 404))
    def beneficio(solicitud_id: str, x_rol: str = Depends(rol),
                  svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.VALIDAR_SOLICITUD)
        r = svc.evaluar_beneficio(solicitud_id)
        mensaje = ("La solicitud califica para el beneficio por referencia." if r.aplica
                   else "La solicitud no califica para el beneficio por referencia. Revisa los motivos.")
        return sc.BeneficioOut(solicitud_id=r.solicitud_id, aplica=r.aplica, total=r.total,
                               motivos=r.motivos, mensaje=mensaje)

    # ---- Transiciones (State Machine) ------------------------------------
    @app.post("/solicitudes/{solicitud_id}/aprobar", response_model=sc.SolicitudOut,
              tags=[T_TRANSICIONES], summary="Aprobar la solicitud y reservar lugares",
              description="Paso 1: Control Escolar valida las reglas y reserva los lugares. "
                          "La solicitud pasa de `SOLICITADA` a `ACEPTADA`.",
              responses=_errores(403, 404, 409, 422))
    def aprobar(solicitud_id: str, x_rol: str = Depends(rol),
                svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.APROBAR)
        sol = svc.aprobar(solicitud_id)
        return _solicitud_out(
            sol, f"Solicitud aprobada y lugares reservados. Siguiente paso: registrar el pago de "
                 f"{sol.total.monto} MXN.")

    @app.post("/solicitudes/{solicitud_id}/pago", response_model=sc.SolicitudOut,
              tags=[T_TRANSICIONES], summary="Registrar el pago y confirmar la inscripción",
              description="Paso 2: el monto debe ser exactamente igual al total. "
                          "La solicitud pasa de `ACEPTADA` a `INSCRITA`.",
              responses=_errores(403, 404, 409, 422))
    def pagar(solicitud_id: str, datos: sc.PagoIn, x_rol: str = Depends(rol),
              svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.REGISTRAR_PAGO)
        sol = svc.inscribir(solicitud_id, datos.monto)
        return _solicitud_out(
            sol, f"Pago de {datos.monto} MXN recibido. Inscripción confirmada.")

    @app.post("/solicitudes/{solicitud_id}/completar", response_model=sc.SolicitudOut,
              tags=[T_TRANSICIONES], summary="Marcar el programa como terminado",
              description="Paso 3: se usa cuando el grupo terminó. La solicitud pasa de `INSCRITA` a "
                          "`FINALIZADA` y ya puede evaluarse la certificación.",
              responses=_errores(403, 404, 409))
    def completar(solicitud_id: str, x_rol: str = Depends(rol),
                  svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.COMPLETAR)
        return _solicitud_out(svc.completar(solicitud_id))

    @app.post("/solicitudes/{solicitud_id}/cancelar", response_model=sc.SolicitudOut,
              tags=[T_TRANSICIONES], summary="Cancelar la solicitud",
              description="Cancela la solicitud desde `SOLICITADA`, `ACEPTADA` o `INSCRITA` y libera "
                          "los lugares reservados. No se puede cancelar una solicitud finalizada.",
              responses=_errores(403, 404, 409))
    def cancelar(solicitud_id: str, x_rol: str = Depends(rol),
                 svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CANCELAR)
        return _solicitud_out(svc.cancelar(solicitud_id))

    # ---- Resultado académico y certificación (US-06, 09, 10, 13) ----------
    @app.put("/solicitudes/{solicitud_id}/resultado", response_model=sc.SolicitudOut,
             tags=[T_CERTIFICACION], summary="Registrar calificación y asistencia",
             description="Lo registra el instructor una vez que el alumno está inscrito. "
                         "Ambos valores van de 0 a 100.",
             responses=_errores(403, 404, 422))
    def resultado(solicitud_id: str, datos: sc.ResultadoAcademicoIn, x_rol: str = Depends(rol),
                  svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.REGISTRAR_RESULTADO)
        sol = svc.registrar_resultado(solicitud_id, datos.calificacion, datos.asistencia)
        return _solicitud_out(
            sol, f"Resultado registrado: calificación {datos.calificacion} y asistencia "
                 f"{datos.asistencia}%.")

    @app.get("/solicitudes/{solicitud_id}/certificacion", response_model=sc.CertificacionOut,
             tags=[T_CERTIFICACION], summary="Consultar si el alumno puede certificarse",
             description="Resultado posible: `Pendiente` (aún no se puede evaluar), `Elegible` o "
                         "`No elegible` (con el motivo: calificación, asistencia o ambos).",
             responses=_errores(403, 404))
    def certificacion(solicitud_id: str, x_rol: str = Depends(rol),
                      svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_CERTIFICACION)
        r = svc.evaluar_certificacion(solicitud_id)
        if r.estado == "Elegible":
            mensaje = "¡Felicidades! El alumno cumple los requisitos y es elegible para certificarse."
        elif r.estado == "No elegible":
            mensaje = f"El alumno no es elegible para certificarse. Motivo: {r.motivo}."
        else:
            mensaje = ("Aún no se puede evaluar: la solicitud debe estar finalizada y tener "
                       "calificación registrada.")
        return sc.CertificacionOut(solicitud_id=r.solicitud_id, estado=r.estado, motivo=r.motivo,
                                   mensaje=mensaje)

    return app


app = create_app()
