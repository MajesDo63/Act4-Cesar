"""Comportamiento de la interfaz real; HTTP simulado para no consumir Gemini."""
from pathlib import Path

import requests
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app" / "cliente_api.py"


class Respuesta:
    def __init__(self, cuerpo, estado=200):
        self.cuerpo, self.status_code = cuerpo, estado
    def json(self):
        return self.cuerpo


def interfaz():
    app = AppTest.from_file(str(APP), default_timeout=15)
    app.session_state["token"] = "token-sintetico-ui"
    return app.run()


def boton(app, nombre):
    return next(b for b in app.button if b.label == nombre)


def test_mi_variante_envia_codigo_y_token_a_endpoint_a3(monkeypatch):
    recibidas=[]
    def solicitud(metodo, url, **kw):
        recibidas.append((metodo,url,kw))
        return Respuesta({"respuesta":"Revisión del ejemplo", "fuentes":["sec-06"], "abstuvo":False,
            "errores_citas":[],"artefacto":{"hallazgos":[]},"latencia_ms":1,"costo_usd":0})
    monkeypatch.setattr(requests,"request",solicitud)
    app=interfaz()
    app.sidebar.radio[0].set_value("Mi variante").run()
    app.text_area[0].set_value("def sumar(a,b):\n    return a+b\n").run()
    boton(app,"Ejecutar mi variante").click().run()
    assert not app.exception and len(recibidas)==1
    metodo,url,kw=recibidas[0]
    assert metodo=="POST" and url.endswith("/v1/revisor")
    assert kw["json"]=={"codigo":"def sumar(a,b):\n    return a+b\n"}
    assert kw["headers"]["Authorization"]=="Bearer token-sintetico-ui"
    assert any("Validador de revisión: aprobado" in x.value for x in app.success)
    assert any(x.label=="Fuentes de mi variante" for x in app.expander)


def test_mi_variante_muestra_errores_de_validacion(monkeypatch):
    monkeypatch.setattr(requests,"request",lambda *a,**k: Respuesta({"respuesta":"Revisión detenida",
        "fuentes":[],"abstuvo":True,"errores_citas":["Fuente inválida"],"artefacto":{}}))
    app=interfaz()
    app.sidebar.radio[0].set_value("Mi variante").run()
    app.text_area[0].set_value("x=1").run()
    boton(app,"Ejecutar mi variante").click().run()
    assert not app.exception and any("referencias con problemas" in x.value for x in app.error)
    assert not any("aprobado" in x.value for x in app.success)


def test_agente_envia_tarea_y_fallo_no_se_presenta_como_revision_aprobada(monkeypatch):
    recibidas=[]
    def solicitud(metodo,url,**kw):
        recibidas.append((url,kw))
        return Respuesta({"respuesta":"La herramienta fallo; no se emitio una revision.",
            "fuentes":[],"terminado":False,"pendientes":[],"validador":{"ok":True,"hallazgos":[]},
            "pasos":[{"n":1,"herramienta":"correr_linter","estado":"fallida",
                "argumentos":{"ruta":"inexistente.py"},"resultado":{"clase":"FileNotFoundError"}}]})
    monkeypatch.setattr(requests,"request",solicitud)
    app=interfaz()
    boton(app,"Probar archivo inexistente").click().run()
    assert not app.exception and recibidas[0][0].endswith("/v1/agente")
    assert "inexistente.py" in recibidas[0][1]["json"]["tarea"]
    assert any("Mensaje de fallo validado" in x.value for x in app.info)
    assert any("Herramienta fallida" in x.value for x in app.error)
    assert not any("Validador: aprobado" in x.value for x in app.success)


def test_sin_sesion_no_se_consulta_la_api(monkeypatch):
    llamadas=[]
    monkeypatch.setattr(requests,"request",lambda *a,**k: llamadas.append(1))
    app=AppTest.from_file(str(APP),default_timeout=15).run()
    assert not app.exception and llamadas==[]
    assert any("inicia sesión" in x.value for x in app.info)


def test_error_de_red_visible_en_mi_variante(monkeypatch):
    def solicitud(*a,**k):
        raise requests.ConnectionError("fallo-de-prueba")
    monkeypatch.setattr(requests,"request",solicitud)
    app=interfaz()
    app.sidebar.radio[0].set_value("Mi variante").run()
    app.text_area[0].set_value("x=1").run()
    boton(app,"Ejecutar mi variante").click().run()
    assert not app.exception
    assert any("No se pudo conectar con la API" in x.value for x in app.error)
