"""Autenticación A3: PBKDF2, tokens HMAC y bloqueo persistente de intentos.

Las firmas públicas del kit se conservan. El token es payload.firma, no un JWT.
Las contraseñas y los tokens nunca se registran en la bitácora de intentos.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass, field

ITERACIONES = 200_000
VIGENCIA_S = int(os.getenv("TOKEN_VIGENCIA_S", "900"))
if not 1 <= VIGENCIA_S <= 900:
    raise RuntimeError("TOKEN_VIGENCIA_S debe estar entre 1 y 900 segundos")
MAX_FALLOS, VENTANA_FALLOS_S = 5, 900
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos"


class ErrorAuth(Exception):
    def __init__(self, status: int, mensaje: str):
        super().__init__(mensaje)
        self.status = status


def _secreto() -> bytes:
    valor = os.getenv("TOKEN_SECRET", "")
    if len(valor) < 32:
        raise RuntimeError("Define TOKEN_SECRET con al menos 32 caracteres en .env")
    return valor.encode("utf8")


def _b64(valor: bytes) -> str:
    return base64.urlsafe_b64encode(valor).rstrip(b"=").decode("ascii")


def _unb64(valor: str) -> bytes:
    if not isinstance(valor, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", valor):
        raise ValueError("Base64url inválido")
    resultado = base64.b64decode(valor + "=" * (-len(valor) % 4), altchars=b"-_", validate=True)
    if _b64(resultado) != valor:
        raise ValueError("Base64url no canónico")
    return resultado


def _hora(ahora: float | None) -> float:
    valor = time.time() if ahora is None else ahora
    if isinstance(valor, bool) or not isinstance(valor, (float, int)) or not math.isfinite(valor):
        raise ValueError("Tiempo inválido")
    return float(valor)


def hash_contrasena(contrasena: str, sal: bytes | None = None) -> str:
    """Devuelve pbkdf2$iteraciones$sal$hash, con sal aleatoria de 16 bytes."""
    if not isinstance(contrasena, str) or not 1 <= len(contrasena) <= 128:
        raise ValueError("Contraseña fuera de los límites admitidos")
    sal = os.urandom(16) if sal is None else sal
    if not isinstance(sal, bytes) or len(sal) < 16:
        raise ValueError("La sal debe tener al menos 16 bytes")
    derivado = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf8"), sal, ITERACIONES)
    return f"pbkdf2${ITERACIONES}${_b64(sal)}${_b64(derivado)}"


def verificar_contrasena(contrasena: str, guardado: str) -> bool:
    """Comprueba el formato y compara el derivado mediante compare_digest."""
    if not isinstance(contrasena, str) or not 1 <= len(contrasena) <= 128:
        return False
    try:
        algoritmo, iteraciones, sal, esperado = guardado.split("$")
        n = int(iteraciones)
        if algoritmo != "pbkdf2" or not ITERACIONES <= n <= 2_000_000:
            return False
        sal_bytes, hash_bytes = _unb64(sal), _unb64(esperado)
        if len(sal_bytes) < 16 or len(hash_bytes) != 32:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf8"), sal_bytes, n)
        return hmac.compare_digest(actual, hash_bytes)
    except (ValueError, TypeError, AttributeError, binascii.Error):
        return False


def emitir_token(usuario: str, ahora: float | None = None) -> str:
    """Firma sub, iat y exp con un secreto externo; vigencia máxima de 900 s."""
    if not isinstance(usuario, str) or not usuario.strip() or len(usuario) > 120:
        raise ValueError("Identidad inválida")
    instante = _hora(ahora)
    datos = {"sub": usuario, "iat": instante, "exp": instante + VIGENCIA_S}
    payload = _b64(json.dumps(datos, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf8"))
    firma = hmac.new(_secreto(), payload.encode("ascii"), hashlib.sha256).digest()
    return payload + "." + _b64(firma)


def _objeto_sin_duplicados(pares):
    obj = {}
    for clave, valor in pares:
        if clave in obj:
            raise ValueError("Claim duplicado")
        obj[clave] = valor
    return obj


def validar_token(token: str, ahora: float | None = None) -> str:
    """Verifica formato, firma, tipos y tiempos; devuelve únicamente la identidad."""
    try:
        if not isinstance(token, str) or len(token) > 4096:
            raise ValueError("Formato")
        payload, firma = token.split(".")
        crudo, recibida = _unb64(payload), _unb64(firma)
        esperada = hmac.new(_secreto(), payload.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(esperada, recibida):
            raise ValueError("Firma")
        datos = json.loads(crudo.decode("utf8"), object_pairs_hook=_objeto_sin_duplicados)
        if not isinstance(datos, dict) or set(datos) != {"sub", "iat", "exp"}:
            raise ValueError("Claims")
        usuario, inicio, fin = datos["sub"], datos["iat"], datos["exp"]
        if not isinstance(usuario, str) or not usuario.strip() or len(usuario) > 120:
            raise ValueError("Identidad")
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in (inicio, fin)):
            raise ValueError("Fechas")
        instante = _hora(ahora)
        if not 0 < fin - inicio <= 900 or inicio > instante:
            raise ValueError("Vigencia")
        if instante >= fin:
            raise ErrorAuth(401, "Token expirado")
        return usuario
    except ErrorAuth:
        raise
    except (ValueError, TypeError, UnicodeError, binascii.Error, OverflowError):
        raise ErrorAuth(401, "Token inválido") from None


@dataclass
class Autenticador:
    ruta_db: str = ":memory:"
    _lock: threading.RLock = field(init=False, repr=False)

    def __post_init__(self):
        self._lock = threading.RLock()
        self.db = sqlite3.connect(self.ruta_db, check_same_thread=False, timeout=10)
        with self.db:
            self.db.execute("CREATE TABLE IF NOT EXISTS usuarios (email TEXT PRIMARY KEY, hash TEXT NOT NULL)")
            self.db.execute("CREATE TABLE IF NOT EXISTS intentos (email TEXT, ts REAL, ok INTEGER)")
            self.db.execute("CREATE INDEX IF NOT EXISTS intentos_email_ts ON intentos(email, ts)")
        # Se genera fuera de las solicitudes: un correo inexistente también verifica un PBKDF2.
        self._hash_ficticio = hash_contrasena(secrets.token_urlsafe(24))

    def registrar(self, email: str, contrasena: str) -> None:
        if not isinstance(email, str) or not isinstance(contrasena, str):
            raise ErrorAuth(422, "Credenciales inválidas")
        email = email.strip().lower()
        if len(email) > 120 or not EMAIL.fullmatch(email):
            raise ErrorAuth(422, "Correo inválido")
        if not 8 <= len(contrasena) <= 128:
            raise ErrorAuth(422, "La contraseña debe tener entre 8 y 128 caracteres")
        guardado = hash_contrasena(contrasena)
        try:
            with self._lock, self.db:
                self.db.execute("INSERT INTO usuarios VALUES (?, ?)", (email, guardado))
        except sqlite3.IntegrityError:
            raise ErrorAuth(409, "El correo ya está registrado") from None

    def login(self, email: str, contrasena: str, ahora: float | None = None) -> str:
        if not isinstance(email, str) or not isinstance(contrasena, str):
            raise ErrorAuth(401, MENSAJE_CREDENCIALES)
        email, instante = email.strip().lower(), _hora(ahora)
        with self._lock, self.db:
            fallos = self.db.execute(
                "SELECT COUNT(*) FROM intentos WHERE email=? AND ok=0 AND ts>=? "
                "AND rowid>COALESCE((SELECT MAX(rowid) FROM intentos WHERE email=? AND ok=1),0)",
                (email, instante - VENTANA_FALLOS_S, email),
            ).fetchone()[0]
            if fallos >= MAX_FALLOS:
                self.db.execute("INSERT INTO intentos VALUES (?,?,2)", (email, instante))
                error = ErrorAuth(429, "Demasiados intentos. Intenta más tarde")
                token = None
            else:
                fila = self.db.execute("SELECT hash FROM usuarios WHERE email=?", (email,)).fetchone()
                coincide = verificar_contrasena(contrasena, fila[0] if fila else self._hash_ficticio)
                ok = fila is not None and coincide
                token = emitir_token(email, instante) if ok else None
                self.db.execute("INSERT INTO intentos VALUES (?,?,?)", (email, instante, int(ok)))
                error = None if ok else ErrorAuth(401, MENSAJE_CREDENCIALES)
        # El intento se confirma antes de propagar el error: un rollback no borra los fallos.
        if error is not None:
            raise error
        return token

    def cerrar(self) -> None:
        with self._lock:
            self.db.close()
