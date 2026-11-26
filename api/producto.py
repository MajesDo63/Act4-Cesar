"""API de A4: base autenticada de A3 y agente propio con herramientas y validador."""
from __future__ import annotations

import os
import sys
import time
import uuid
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator
from starlette.exceptions import HTTPException as ErrorFramework

# La configuración carga .env antes de que auth lea la vigencia.
from finnorte.config import RAIZ, config
from api.auth import VIGENCIA_S, Autenticador, ErrorAuth, validar_token
from finnorte import agente_servicio, agente_revisor, herramientas, llm, trazas, variante
from finnorte.herramientas_revisor import ARCHIVOS, herramientas_revisor
from finnorte.validador_a4 import validar_resultado
from finnorte.caso_guia import asistente as caso_guia

app = FastAPI(title="FinNorte | Actividad 4: revisor con herramientas", version="4.0")
auth = Autenticador(os.getenv("AUTH_DB", str(RAIZ / "bitacora" / "usuarios.db")))
_ventanas: dict[str, list[float]] = {}
_ventanas_lock = threading.Lock()
LIMITE_POR_MINUTO = int(os.getenv("API_LIMITE", "30"))
if not 1 <= LIMITE_POR_MINUTO <= 10_000:
    raise RuntimeError("API_LIMITE debe estar entre 1 y 10000")


@app.middleware("http")
async def cabeceras_seguras(request: Request, siguiente):
    respuesta = await siguiente(request)
    respuesta.headers["Cache-Control"] = "no-store"
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    return respuesta


# ───────────────────────────── errores problem+json (ing-07) ─────────────────────────────
def problema(status: int, title: str, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, media_type="application/problem+json",
                        headers={"Retry-After": "60"} if status == 429 else None,
                        content={"type": f"https://docs.finnorte.mx/errores/{status}", "title": title,
                                 "status": status, "detail": detail, "trace_id": uuid.uuid4().hex[:12]})


class ErrorHTTP(Exception):
    def __init__(self, status, title, detail, retry_after=None):
        self.status, self.title, self.detail = status, title, detail
        self.retry_after = retry_after


@app.exception_handler(ErrorHTTP)
async def _manejar(_: Request, e: ErrorHTTP):
    respuesta = problema(e.status, e.title, e.detail)
    if e.retry_after is not None:
        respuesta.headers["Retry-After"] = str(e.retry_after)
    return respuesta


@app.exception_handler(RequestValidationError)
async def _validacion(_: Request, e: RequestValidationError):
    detalle = "; ".join(f"{'.'.join(str(x) for x in err['loc'][1:])}: {err['msg']}" for err in e.errors())[:300]
    return problema(422, "Entrada inválida", detalle)


@app.exception_handler(NotImplementedError)
async def _pendiente(_: Request, e: NotImplementedError):
    return problema(501, "Pieza pendiente", f"{e} · complétala siguiendo el manual del laboratorio")


@app.exception_handler(ErrorFramework)
async def _error_http(_: Request, e: ErrorFramework):
    return problema(e.status_code, "Solicitud no disponible", "La ruta o el método no están disponibles")


@app.exception_handler(Exception)
async def _error_interno(_: Request, e: Exception):
    trazas.registrar("a3_error", clase=type(e).__name__)
    return problema(500, "Error interno", "No fue posible procesar la solicitud")


def _error_llm(error: Exception) -> ErrorHTTP:
    trazas.registrar("a3_proveedor", clase=type(error).__name__)
    return ErrorHTTP(503, "Proveedor no disponible", "No fue posible consultar el modelo; intenta más tarde")


TITULOS = {401: "No autorizado", 409: "Conflicto", 422: "Entrada inválida", 429: "Demasiadas solicitudes"}


def _de_auth(e: ErrorAuth) -> ErrorHTTP:
    return ErrorHTTP(e.status, TITULOS.get(e.status, "Error"), str(e), 900 if e.status == 429 else None)


# ───────────────────────────── autenticación ─────────────────────────────
class Credenciales(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=5, max_length=120)
    contrasena: str = Field(min_length=1, max_length=128)


@app.post("/auth/registro", status_code=201)
def registro(c: Credenciales):
    try:
        auth.registrar(c.email, c.contrasena)
    except ErrorAuth as e:
        raise _de_auth(e)
    return {"mensaje": "Registro exitoso"}


@app.post("/auth/login")
def login(c: Credenciales):
    try:
        return {"token": auth.login(c.email, c.contrasena), "tipo": "Bearer", "expira_en_s": VIGENCIA_S}
    except ErrorAuth as e:
        raise _de_auth(e)


_bearer = HTTPBearer(auto_error=False, description="Pega aquí SOLO el token de /auth/login (sin la palabra Bearer)")


def usuario_actual(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    """Dependencia: exige 'Authorization: Bearer <token>' válido y aplica el límite por usuario.
    HTTPBearer hace que /docs muestre el botón Authorize (candado)."""
    if cred is None or cred.scheme.lower() != "bearer":
        raise ErrorHTTP(401, "No autorizado", "Falta la cabecera Authorization: Bearer <token>")
    try:
        usuario = validar_token(cred.credentials.strip())
    except ErrorAuth as e:
        raise _de_auth(e)
    ahora = time.time()
    with _ventanas_lock:
        ventana = [t for t in _ventanas.get(usuario, []) if ahora - t < 60]
        if len(ventana) >= LIMITE_POR_MINUTO:
            raise ErrorHTTP(429, "Demasiadas solicitudes", f"Límite de {LIMITE_POR_MINUTO} por minuto")
        _ventanas[usuario] = ventana + [ahora]
    return usuario


# ───────────────────────────── endpoints del producto ─────────────────────────────
@app.get("/salud")
def salud():
    c = config()
    return {"estado": "ok", "llm": f"{c.llm_proveedor}/{c.llm_modelo}", "embeddings": c.emb_proveedor,
            "variante": variante.VARIANTE, "agente": "Ejecutor propio A4", "ejemplos": list(ARCHIVOS)}


class Pregunta(BaseModel):
    pregunta: str = Field(min_length=3, max_length=500)


@app.post("/v1/preguntas")
def preguntar(p: Pregunta, usuario: str = Depends(usuario_actual)):
    try:
        out = caso_guia.responder(p.pregunta)
    except llm.LLMError as e:
        raise _error_llm(e)
    return {k: out[k] for k in ("respuesta", "fuentes", "abstuvo", "latencia_ms", "costo_usd")}


class CodigoRevisor(BaseModel):
    """Entrada específica: se recibe código, nunca una ruta para leer del servidor."""
    model_config = ConfigDict(extra="forbid")
    codigo: str = Field(min_length=1, max_length=20_000, description="Código Python a revisar; no se ejecuta")

    @field_validator("codigo")
    @classmethod
    def comprobar_codigo(cls, valor: str) -> str:
        if not valor.strip() or "\x00" in valor:
            raise ValueError("El código debe contener texto y no puede incluir caracteres nulos")
        return valor


class SalidaRevisor(BaseModel):
    model_config = ConfigDict(extra="allow")
    respuesta: str
    fuentes: list[str]
    abstuvo: bool
    errores_citas: list[str]
    artefacto: dict
    costo_usd: float = Field(ge=0)
    latencia_ms: float = Field(ge=0)


@app.post("/v1/revisor", response_model=SalidaRevisor, tags=["Actividad 3"])
def revisar_codigo(entrada: CodigoRevisor, usuario: str = Depends(usuario_actual)):
    """Revisa código con el motor v2-revisor del Avance 1 del equipo."""
    try:
        return variante.sistema({"codigo": entrada.codigo})
    except ValueError:
        raise ErrorHTTP(422, "Entrada inválida", "El motor no pudo interpretar la entrada") from None
    except llm.LLMError as error:
        raise _error_llm(error) from None


class Tarea(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tarea: str = Field(min_length=5, max_length=800)


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    aprobar: StrictBool


def _herramientas(usuario):
    return herramientas_revisor(usuario)


@app.post("/v1/agente")
def agente(t: Tarea, usuario: str = Depends(usuario_actual)):
    try:
        return agente_servicio.iniciar(t.tarea, usuario, _herramientas(usuario),
                                      ejecutor=herramientas.ejecutar_agente, validador=validar_resultado,
                                      contexto=agente_revisor.CONTEXTO_V2)
    except llm.LLMError as e:
        raise _error_llm(e)


@app.post("/v1/agente/confirmar/{id_}")
def confirmar(id_: str, d: Decision, usuario: str = Depends(usuario_actual)):
    try:
        return agente_servicio.resolver(id_, usuario, d.aprobar)
    except KeyError as e:
        raise ErrorHTTP(404, "Acción no encontrada", str(e))
