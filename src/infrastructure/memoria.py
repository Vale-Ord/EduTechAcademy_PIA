"""Repositorios en memoria: sirven para pruebas unitarias y para ejecutar los casos del maestro."""
from __future__ import annotations

from src.domain.entidades import Alumno, Programa, Solicitud
from src.domain.eventos import EventoDominio


class AlumnoRepoMemoria:
    def __init__(self):
        self._d: dict[str, Alumno] = {}

    def obtener(self, alumno_id):
        return self._d.get(alumno_id)

    def agregar(self, alumno):
        self._d[alumno.id] = alumno


class ProgramaRepoMemoria:
    def __init__(self):
        self._d: dict[str, Programa] = {}

    def obtener(self, programa_id):
        return self._d.get(programa_id)

    def listar(self, solo_habilitados=False):
        return [p for p in self._d.values() if p.habilitado or not solo_habilitados]

    def guardar(self, programa):
        self._d[programa.id] = programa


class SolicitudRepoMemoria:
    def __init__(self):
        self._d: dict[str, Solicitud] = {}
        self._n = 0

    def obtener(self, solicitud_id):
        return self._d.get(solicitud_id)

    def agregar(self, solicitud):
        self._d[solicitud.id] = solicitud

    def guardar(self, solicitud):
        self._d[solicitud.id] = solicitud

    def listar(self, alumno_id=None, estado=None):
        return [
            s for s in self._d.values()
            if (alumno_id is None or s.alumno_id == alumno_id)
            and (estado is None or s.estado.value == estado)
        ]

    def siguiente_id(self):
        self._n += 1
        return f"EDU-N{self._n:04d}"


class PublicadorMemoria:
    def __init__(self):
        self.eventos: list[EventoDominio] = []

    def publicar(self, eventos):
        self.eventos.extend(eventos)

    def listar(self, solicitud_id):
        return [e for e in self.eventos if e.solicitud_id == solicitud_id]
