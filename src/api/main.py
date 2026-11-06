"""API REST de EduTechAcademy (FastAPI). Swagger UI en /docs, OpenAPI en /openapi.json."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, Query

from src.api import schemas as sc
from src.api.errores import registrar_manejadores
from src.application.permisos import Permiso, autorizar
from src.application.servicios import SolicitudService
from src.domain.entidades import Programa, Solicitud
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

* Cada endpoint exige el encabezado `X-Rol` (`estudiante`, `instructor`, `control_escolar`,
  `administracion`, `cliente_empresarial`) para aplicar los permisos de **RB-14**.
* Códigos: `200/201` éxito · `400` dato inválido · `403` sin permiso · `404` no existe ·
  `409` transición inválida o cupo agotado · `422` regla de negocio no cumplida.
"""


def _solicitud_out(s: Solicitud) -> sc.SolicitudOut:
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
                  lifespan=lifespan)
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

    @app.get("/health", tags=["Sistema"])
    def health():
        return {"status": "ok", "entorno": settings.app_env}

    @app.post("/admin/seed", tags=["Sistema"], summary="Carga los CSV del maestro si la base está vacía")
    def seed(x_rol: str = Depends(rol)):
        autorizar(x_rol, Permiso.APROBAR)  # solo Control Escolar
        with session_factory() as s:
            return {"sembrada": sembrar_si_vacio(s)}

    # ---- Programas (US-01) ----------------------------------------------
    @app.get("/programas", response_model=list[sc.ProgramaOut], tags=["Programas"])
    def listar_programas(solo_habilitados: bool = False, x_rol: str = Depends(rol),
                         svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_PROGRAMAS)
        return [_programa_out(p) for p in svc.listar_programas(solo_habilitados)]

    @app.get("/programas/{programa_id}", response_model=sc.ProgramaOut, tags=["Programas"])
    def obtener_programa(programa_id: str, x_rol: str = Depends(rol),
                         svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_PROGRAMAS)
        return _programa_out(svc.obtener_programa(programa_id))

    # ---- Solicitudes (US-02, US-03, US-12, US-15, US-18) ------------------
    @app.post("/solicitudes", response_model=sc.SolicitudOut, status_code=201, tags=["Solicitudes"])
    def crear_solicitud(datos: sc.SolicitudIn, x_rol: str = Depends(rol),
                        svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CREAR_SOLICITUD)
        sol = svc.crear(datos.actor_id, [(r.programa_id, r.cantidad) for r in datos.renglones],
                        datos.promocion_activa, datos.autorizado, datos.referencia)
        return _solicitud_out(sol)

    @app.get("/solicitudes", response_model=list[sc.SolicitudOut], tags=["Solicitudes"])
    def listar_solicitudes(actor_id: str | None = None,
                           estado: str | None = Query(default=None, examples=["ACEPTADA"]),
                           x_rol: str = Depends(rol),
                           svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_SOLICITUDES)
        return [_solicitud_out(s) for s in svc.listar(actor_id, estado)]

    @app.get("/solicitudes/{solicitud_id}", response_model=sc.SolicitudOut, tags=["Solicitudes"])
    def obtener_solicitud(solicitud_id: str, x_rol: str = Depends(rol),
                          svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_SOLICITUDES)
        return _solicitud_out(svc.obtener(solicitud_id))

    @app.get("/solicitudes/{solicitud_id}/eventos", response_model=list[sc.EventoOut], tags=["Solicitudes"])
    def eventos(solicitud_id: str, x_rol: str = Depends(rol),
                svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_SOLICITUDES)
        return [sc.EventoOut(evento=e.nombre, solicitud_id=e.solicitud_id,
                             ocurrido_en=e.ocurrido_en.isoformat()) for e in svc.eventos_de(solicitud_id)]

    # ---- Reglas (Specification) ------------------------------------------
    @app.get("/solicitudes/{solicitud_id}/validacion", response_model=sc.ValidacionOut, tags=["Reglas"])
    def validar(solicitud_id: str, x_rol: str = Depends(rol),
                svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.VALIDAR_SOLICITUD)
        r = svc.validar(solicitud_id)
        return sc.ValidacionOut(solicitud_id=r.solicitud_id, cumple=r.cumple, motivos=r.motivos)

    @app.get("/solicitudes/{solicitud_id}/beneficio", response_model=sc.BeneficioOut, tags=["Reglas"])
    def beneficio(solicitud_id: str, x_rol: str = Depends(rol),
                  svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.VALIDAR_SOLICITUD)
        r = svc.evaluar_beneficio(solicitud_id)
        return sc.BeneficioOut(solicitud_id=r.solicitud_id, aplica=r.aplica, total=r.total, motivos=r.motivos)

    # ---- Transiciones (State Machine) ------------------------------------
    @app.post("/solicitudes/{solicitud_id}/aprobar", response_model=sc.SolicitudOut, tags=["Transiciones"])
    def aprobar(solicitud_id: str, x_rol: str = Depends(rol),
                svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.APROBAR)
        return _solicitud_out(svc.aprobar(solicitud_id))

    @app.post("/solicitudes/{solicitud_id}/pago", response_model=sc.SolicitudOut, tags=["Transiciones"])
    def pagar(solicitud_id: str, datos: sc.PagoIn, x_rol: str = Depends(rol),
              svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.REGISTRAR_PAGO)
        return _solicitud_out(svc.inscribir(solicitud_id, datos.monto))

    @app.post("/solicitudes/{solicitud_id}/completar", response_model=sc.SolicitudOut, tags=["Transiciones"])
    def completar(solicitud_id: str, x_rol: str = Depends(rol),
                  svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.COMPLETAR)
        return _solicitud_out(svc.completar(solicitud_id))

    @app.post("/solicitudes/{solicitud_id}/cancelar", response_model=sc.SolicitudOut, tags=["Transiciones"])
    def cancelar(solicitud_id: str, x_rol: str = Depends(rol),
                 svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CANCELAR)
        return _solicitud_out(svc.cancelar(solicitud_id))

    # ---- Resultado académico y certificación (US-06, 09, 10, 13) ----------
    @app.put("/solicitudes/{solicitud_id}/resultado", response_model=sc.SolicitudOut, tags=["Certificación"])
    def resultado(solicitud_id: str, datos: sc.ResultadoAcademicoIn, x_rol: str = Depends(rol),
                  svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.REGISTRAR_RESULTADO)
        return _solicitud_out(svc.registrar_resultado(solicitud_id, datos.calificacion, datos.asistencia))

    @app.get("/solicitudes/{solicitud_id}/certificacion", response_model=sc.CertificacionOut,
             tags=["Certificación"])
    def certificacion(solicitud_id: str, x_rol: str = Depends(rol),
                      svc: SolicitudService = Depends(get_servicio)):
        autorizar(x_rol, Permiso.CONSULTAR_CERTIFICACION)
        r = svc.evaluar_certificacion(solicitud_id)
        return sc.CertificacionOut(solicitud_id=r.solicitud_id, estado=r.estado, motivo=r.motivo)

    return app


app = create_app()
