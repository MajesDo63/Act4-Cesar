"""Sesiones de agente con confirmaciones de un solo uso ligadas al usuario."""
from __future__ import annotations

import copy
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable

import jsonschema

from . import trazas

VIGENCIA_PENDIENTE_S = 600
_LOCK = threading.RLock()


@dataclass
class Pendiente:
    id: str
    usuario: str
    herramienta: str
    argumentos: dict
    funcion: Callable
    esquema: dict
    creado: float = field(default_factory=time.time)


_PENDIENTES: dict[str, Pendiente] = {}


def iniciar(tarea: str, usuario: str, herramientas: list, max_pasos: int = 6,
            validador: Callable | None = None, ejecutor: Callable | None = None,
            contexto: str = "") -> dict:
    if ejecutor is None or validador is None:
        raise ValueError("Se requiere ejecutor y validador propios")
    propuestas = []

    def confirmar(h, argumentos):
        propuestas.append((h.nombre, copy.deepcopy(argumentos)))
        return None

    resultado = ejecutor(tarea, herramientas, confirmar=confirmar, max_pasos=max_pasos, contexto=contexto)
    errores = validador(resultado, propuestas)
    pendientes = []
    catalogo = {h.nombre: h for h in herramientas}
    if not errores:
        with _LOCK:
            ahora = time.time()
            for clave in list(_PENDIENTES):
                if ahora - _PENDIENTES[clave].creado > VIGENCIA_PENDIENTE_S:
                    del _PENDIENTES[clave]
            if len(_PENDIENTES) >= 100:
                errores.append("Hay demasiadas confirmaciones pendientes")
            else:
                for nombre, argumentos in propuestas[:1]:
                    h = catalogo[nombre]
                    p = Pendiente(uuid.uuid4().hex, usuario, nombre, copy.deepcopy(argumentos),
                                  h.funcion, copy.deepcopy(h.esquema))
                    _PENDIENTES[p.id] = p
                    pendientes.append({"id": p.id, "herramienta": nombre,
                                       "argumentos": copy.deepcopy(argumentos),
                                       "mensaje": "Revisa los argumentos exactos antes de decidir.",
                                       "expira_en_s": VIGENCIA_PENDIENTE_S})
    trazas.registrar("a4_agente_api", pasos=len(resultado.pasos), validador=errores,
                     propuestas_sensibles=len(propuestas))
    return {"respuesta": resultado.respuesta if not errores else "Respuesta bloqueada por el validador.",
            "fuentes": resultado.fuentes if not errores else [], "terminado": resultado.terminado and not errores,
            "pasos": [{"n": p.n, "accion": p.propuesta.get("accion"),
                       "herramienta": p.propuesta.get("herramienta"), "argumentos": p.propuesta.get("argumentos"),
                       "estado": p.estado, "resultado": p.resultado} for p in resultado.pasos],
            "validador": {"ok": not errores, "hallazgos": errores,
                          "alcance": "SEC existente, linea, evidencia literal, huella y respuesta respaldada"},
            "pendientes": pendientes}


def resolver(id_: str, usuario: str, aprobar: bool, herramientas: list | None = None) -> dict:
    if type(aprobar) is not bool:
        raise ValueError("La decision debe ser un booleano")
    with _LOCK:
        p = _PENDIENTES.get(id_)
        if p is None or p.usuario != usuario:
            raise KeyError("No existe una accion pendiente para este usuario")
        del _PENDIENTES[id_]
    if time.time() - p.creado > VIGENCIA_PENDIENTE_S:
        return {"estado": "expirada", "efecto": False, "validador": {"ok": False, "hallazgos": ["Confirmacion expirada"]}}
    if aprobar is False:
        trazas.registrar("a4_confirmacion", estado="rechazada", herramienta=p.herramienta)
        return {"estado": "rechazada", "efecto": False, "herramienta": p.herramienta,
                "argumentos": p.argumentos, "validador": {"ok": True, "hallazgos": []}}
    try:
        jsonschema.validate(p.argumentos, p.esquema)
        salida = p.funcion(**copy.deepcopy(p.argumentos))
    except Exception as error:
        trazas.registrar("a4_confirmacion", estado="fallida", clase=type(error).__name__)
        return {"estado": "fallida", "efecto": False,
                "validador": {"ok": False, "hallazgos": ["La accion cambio, ya existe el informe o no se pudo guardar"]}}
    trazas.registrar("a4_confirmacion", estado="ejecutada", herramienta=p.herramienta)
    return {"estado": "ejecutada", "herramienta": p.herramienta, "argumentos": p.argumentos,
            "resultado": salida, "validador": {"ok": True, "hallazgos": []}}
