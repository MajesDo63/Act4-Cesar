"""Contrato HTTP de A3: endpoint específico, token, límites y errores sin secretos."""
import pytest
from fastapi.testclient import TestClient

from api.auth import Autenticador

CRED = {"email": "ana@finnorte.mx", "contrasena": "Segura123!"}
SALIDA = dict(respuesta="sin hallazgos", fuentes=[], abstuvo=False, errores_citas=[], artefacto={}, costo_usd=0, latencia_ms=1)


@pytest.fixture
def servicio(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_SECRET", "s" * 64)
    import api.producto as modulo
    anterior = modulo.auth
    actual = Autenticador(str(tmp_path / "usuarios.db"))
    monkeypatch.setattr(modulo, "auth", actual)
    modulo._ventanas.clear()
    with TestClient(modulo.app, raise_server_exceptions=False) as cliente:
        yield modulo, cliente
    actual.cerrar()


def cabeceras(cliente):
    assert cliente.post("/auth/registro", json=CRED).status_code == 201
    r = cliente.post("/auth/login", json=CRED)
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    return {"Authorization": "Bearer " + r.json()["token"]}


def comprobar_problema(respuesta, estado):
    assert respuesta.status_code == estado
    assert respuesta.headers["content-type"].startswith("application/problem+json")
    assert {"type", "title", "status", "detail", "trace_id"} <= set(respuesta.json())
    assert respuesta.json()["status"] == estado


def test_a3_endpoint_exige_token(servicio):
    _, c = servicio
    comprobar_problema(c.post("/v1/revisor", json={"codigo": "print(1)"}), 401)


def test_a3_endpoint_llama_motor_del_equipo_con_codigo(monkeypatch, servicio):
    m, c = servicio
    recibidos = []
    def motor(entrada):
        recibidos.append(entrada)
        return dict(SALIDA)
    monkeypatch.setattr(m.variante, "sistema", motor)
    entrada = {"codigo": "def sumar(a, b):\n    return a+b\n"}
    r = c.post("/v1/revisor", json=entrada, headers=cabeceras(c))
    assert r.status_code == 200 and recibidos == [entrada]
    assert r.json()["respuesta"] == "sin hallazgos"
    assert r.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("entrada", [{"codigo": " "}, {"codigo": "x\0y"}, {"codigo": "a" * 20001}, {"archivo": "C:/Windows/win.ini"}, {"codigo": "x=1", "archivo": "cualquier-ruta"}])
def test_a3_entrada_especifica_rechaza_vacios_rutas_y_extras(servicio, entrada):
    _, c = servicio
    comprobar_problema(c.post("/v1/revisor", json=entrada, headers=cabeceras(c)), 422)


def test_a3_token_alterado_no_invoca_motor(monkeypatch, servicio):
    m, c = servicio
    h = cabeceras(c)
    h["Authorization"] += "x"
    def prohibido(_):
        pytest.fail("No debe invocarse el motor sin autenticación válida")
    monkeypatch.setattr(m.variante, "sistema", prohibido)
    comprobar_problema(c.post("/v1/revisor", json={"codigo": "x=1"}, headers=h), 401)


def test_a3_limite_por_usuario_y_retry_after(monkeypatch, servicio):
    m, c = servicio
    monkeypatch.setattr(m, "LIMITE_POR_MINUTO", 2)
    monkeypatch.setattr(m.variante, "sistema", lambda _: dict(SALIDA))
    h = cabeceras(c)
    assert [c.post("/v1/revisor", json={"codigo": "x=1"}, headers=h).status_code for _ in range(2)] == [200, 200]
    r = c.post("/v1/revisor", json={"codigo": "x=1"}, headers=h)
    comprobar_problema(r, 429)
    assert r.headers["Retry-After"] == "60"


def test_a3_fallo_de_proveedor_no_filtra_detalles(monkeypatch, servicio):
    m, c = servicio
    def fallo(_):
        raise m.llm.LLMError("secreto-de-prueba-que-no-debe-publicarse")
    monkeypatch.setattr(m.variante, "sistema", fallo)
    r = c.post("/v1/revisor", json={"codigo": "x=1"}, headers=cabeceras(c))
    comprobar_problema(r, 503)
    assert "secreto-de-prueba" not in r.text


def test_a3_no_sustituye_motor_pendiente_por_demo(monkeypatch, servicio):
    m, c = servicio
    def pendiente(_):
        raise NotImplementedError("Pendiente: motor")
    monkeypatch.setattr(m.variante, "sistema", pendiente)
    comprobar_problema(c.post("/v1/revisor", json={"codigo": "x=1"}, headers=cabeceras(c)), 501)


def test_a3_error_interno_y_ruta_ausente_tienen_problem_json(monkeypatch, servicio):
    m, c = servicio
    def fallo(_):
        raise RuntimeError("dato-interno-reservado")
    monkeypatch.setattr(m.variante, "sistema", fallo)
    r = c.post("/v1/revisor", json={"codigo": "x=1"}, headers=cabeceras(c))
    comprobar_problema(r, 500)
    assert "dato-interno-reservado" not in r.text
    comprobar_problema(c.get("/no-existe"), 404)


def test_a3_openapi_documenta_entrada_y_salida_propias(servicio):
    _, c = servicio
    esquema = c.get("/openapi.json").json()
    assert "/v1/variante" not in esquema["paths"]
    assert "EntradaVariante" not in esquema["components"]["schemas"]
    endpoint = esquema["paths"]["/v1/revisor"]["post"]
    assert endpoint["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("CodigoRevisor")
    assert endpoint["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("SalidaRevisor")


@pytest.mark.parametrize("archivo", [".env", "../.env", "/tmp/no-existe-a3", "C:/Windows/win.ini", "C:/ruta-inexistente-a3"])
def test_a3_ruta_generica_eliminada_no_invoca_motor(monkeypatch, servicio, archivo):
    m, c = servicio
    h = cabeceras(c)
    def prohibido(_):
        pytest.fail("La ruta retirada no debe enviar ninguna entrada al motor")
    monkeypatch.setattr(m.variante, "sistema", prohibido)
    respuesta = c.post("/v1/variante", json={"entrada": {"archivo": archivo}}, headers=h)
    comprobar_problema(respuesta, 404)


def test_a3_archivo_real_del_servidor_no_se_lee_por_http(monkeypatch, servicio, tmp_path):
    from pathlib import Path
    m, c = servicio
    h = cabeceras(c)
    privado = tmp_path / "credencial-sintetica.env"
    privado.write_text("MARCADOR_PRIVADO_NO_ENVIAR_AL_MODELO", encoding="utf8")
    leer_original = Path.read_text
    def leer_controlado(path, *args, **kwargs):
        if path == privado:
            pytest.fail("Ningún endpoint debe abrir el archivo sintético del servidor")
        return leer_original(path, *args, **kwargs)
    def motor_prohibido(_):
        pytest.fail("No se debe invocar el motor con una ruta de archivo HTTP")
    monkeypatch.setattr(Path, "read_text", leer_controlado)
    monkeypatch.setattr(m.variante, "sistema", motor_prohibido)
    for endpoint, cuerpo, estado in [
        ("/v1/variante", {"entrada": {"archivo": str(privado)}}, 404),
        ("/v1/revisor", {"archivo": str(privado)}, 422),
        ("/v1/revisor", {"codigo": "x=1", "archivo": str(privado)}, 422),
    ]:
        respuesta = c.post(endpoint, json=cuerpo, headers=h)
        comprobar_problema(respuesta, estado)
        assert "MARCADOR_PRIVADO" not in respuesta.text
