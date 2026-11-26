"""Pruebas propias A3: límites, persistencia, firmas, concurrencia y privacidad."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import json

import pytest

from api import auth

CRED = ("ana@finnorte.mx", "Segura123!")


@pytest.fixture
def autenticador(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_SECRET", "s" * 64)
    servicio = auth.Autenticador(str(tmp_path / "auth.db"))
    servicio.registrar(*CRED)
    yield servicio
    servicio.cerrar()


def test_hash_sal_aleatoria_y_comprobacion_constante():
    primero = auth.hash_contrasena(CRED[1])
    segundo = auth.hash_contrasena(CRED[1])
    assert primero != segundo
    assert auth.verificar_contrasena(CRED[1], primero)
    assert not auth.verificar_contrasena("Incorrecta123", primero)
    assert not auth.verificar_contrasena(CRED[1], "pbkdf2$1$abc$def")


def test_no_contrasena_ni_token_en_registros(autenticador):
    token = autenticador.login(*CRED)
    assert CRED[1] not in repr(autenticador.db.execute("SELECT * FROM usuarios").fetchall())
    intentos = repr(autenticador.db.execute("SELECT * FROM intentos").fetchall())
    assert CRED[1] not in intentos and token not in intentos


def test_normalizacion_y_correo_duplicado(autenticador):
    with pytest.raises(auth.ErrorAuth) as error:
        autenticador.registrar(" ANA@FINNORTE.MX ", "OtraSegura123")
    assert error.value.status == 409
    assert autenticador.login(" ANA@FINNORTE.MX ", CRED[1])


@pytest.mark.parametrize("correo,clave", [("sin-arroba", "Segura123!"), ("x@y.mx", "1234567"), ("x@y.mx", "x" * 129)])
def test_registro_rechaza_datos_invalidos(autenticador, correo, clave):
    with pytest.raises(auth.ErrorAuth) as error:
        autenticador.registrar(correo, clave)
    assert error.value.status == 422


def test_credenciales_incorrectas_mensaje_uniforme(autenticador):
    errores = []
    for correo, clave in [(CRED[0], "Incorrecta123"), ("no-existe@finnorte.mx", CRED[1])]:
        with pytest.raises(auth.ErrorAuth) as error:
            autenticador.login(correo, clave)
        errores.append((error.value.status, str(error.value)))
    assert errores == [(401, auth.MENSAJE_CREDENCIALES)] * 2


def test_inyeccion_sql_no_autentica(autenticador):
    with pytest.raises(auth.ErrorAuth) as error:
        autenticador.login("' OR 1=1 --", CRED[1])
    assert error.value.status == 401
    assert autenticador.db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 1


def test_bloqueo_y_desbloqueo_con_reloj_controlado(autenticador):
    for instante in range(1000, 1005):
        with pytest.raises(auth.ErrorAuth) as error:
            autenticador.login(CRED[0], "Incorrecta123", ahora=instante)
        assert error.value.status == 401
    with pytest.raises(auth.ErrorAuth) as error:
        autenticador.login(*CRED, ahora=1005)
    assert error.value.status == 429
    assert autenticador.login(*CRED, ahora=1905)


def test_exito_interrumpe_la_racha_de_fallos(autenticador):
    for instante in range(4):
        with pytest.raises(auth.ErrorAuth):
            autenticador.login(CRED[0], "Incorrecta123", ahora=instante)
    autenticador.login(*CRED, ahora=4)
    for instante in range(5, 9):
        with pytest.raises(auth.ErrorAuth) as error:
            autenticador.login(CRED[0], "Incorrecta123", ahora=instante)
        assert error.value.status == 401
    assert autenticador.login(*CRED, ahora=9)


def test_bloqueo_persiste_al_reabrir_la_base(autenticador):
    for _ in range(5):
        with pytest.raises(auth.ErrorAuth):
            autenticador.login(CRED[0], "Incorrecta123")
    otro = auth.Autenticador(autenticador.ruta_db)
    try:
        with pytest.raises(auth.ErrorAuth) as error:
            otro.login(*CRED)
        assert error.value.status == 429
    finally:
        otro.cerrar()


def test_intentos_concurrentes_no_eluden_el_bloqueo(autenticador):
    def intento(_):
        try:
            autenticador.login(CRED[0], "Incorrecta123", ahora=100)
        except auth.ErrorAuth as error:
            return error.status
    with ThreadPoolExecutor(max_workers=8) as hilos:
        estados = list(hilos.map(intento, range(10)))
    assert estados.count(401) == 5 and estados.count(429) == 5


def test_token_limites_de_expiracion_y_ahora_cero(monkeypatch):
    monkeypatch.setenv("TOKEN_SECRET", "s" * 64)
    token = auth.emitir_token(CRED[0], ahora=0)
    assert auth.validar_token(token, ahora=0) == CRED[0]
    assert auth.validar_token(token, ahora=auth.VIGENCIA_S - 0.001) == CRED[0]
    with pytest.raises(auth.ErrorAuth, match="expirado"):
        auth.validar_token(token, ahora=auth.VIGENCIA_S)


def test_token_alterado_y_emitido_en_el_futuro(monkeypatch):
    monkeypatch.setenv("TOKEN_SECRET", "s" * 64)
    token = auth.emitir_token(CRED[0], ahora=1000)
    alterado = token[:-1] + ("A" if token[-1] != "A" else "B")
    for valor, reloj in [(alterado, 1000), (token, 999)]:
        with pytest.raises(auth.ErrorAuth) as error:
            auth.validar_token(valor, ahora=reloj)
        assert error.value.status == 401


def test_cambiar_bits_no_significativos_tambien_invalida_token(monkeypatch):
    monkeypatch.setenv("TOKEN_SECRET", "s" * 64)
    token = auth.emitir_token(CRED[0], ahora=1000)
    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    alterado = token[:-1] + alfabeto[alfabeto.index(token[-1]) + 1]
    with pytest.raises(auth.ErrorAuth):
        auth.validar_token(alterado, ahora=1000)


@pytest.mark.parametrize("token", [None, "", "abc", "a.b.c", "a.====", "x" * 4097])
def test_token_malformado_siempre_es_401(monkeypatch, token):
    monkeypatch.setenv("TOKEN_SECRET", "s" * 64)
    with pytest.raises(auth.ErrorAuth) as error:
        auth.validar_token(token)
    assert error.value.status == 401


def test_claims_duplicados_aun_con_firma_correcta_se_rechazan(monkeypatch):
    monkeypatch.setenv("TOKEN_SECRET", "s" * 64)
    cuerpo = b'{"sub":"ana@finnorte.mx","iat":0,"exp":900,"exp":999999}'
    payload = base64.urlsafe_b64encode(cuerpo).rstrip(b"=").decode()
    firma = base64.urlsafe_b64encode(hmac.new(b"s" * 64, payload.encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
    with pytest.raises(auth.ErrorAuth):
        auth.validar_token(payload + "." + firma, ahora=1)


def test_secreto_ausente_impide_emitir_token(monkeypatch):
    monkeypatch.delenv("TOKEN_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="TOKEN_SECRET"):
        auth.emitir_token(CRED[0])
