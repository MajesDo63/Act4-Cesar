import json

from test_api_base import servicio, cabeceras, comprobar_problema
from test_a4_confirmaciones import guion_guardado
from finnorte import llm, agente_servicio


def guion_revision(archivo="limites.py"):
    def responder(prompt, sistema):
        entrada = json.loads(prompt)
        if not entrada["observaciones"]:
            return json.dumps({"accion": "usar", "herramienta": "correr_linter", "argumentos": {"ruta": archivo}})
        r = entrada["observaciones"][-1]["resultado"]
        return json.dumps({"accion": "responder", "respuesta": r["respuesta_autorizada"], "fuentes": r["fuentes"]})
    return responder


def test_agente_exige_token(servicio):
    _, c = servicio
    comprobar_problema(c.post("/v1/agente", json={"tarea": "Revisa limites.py"}), 401)


def test_api_agente_propio_y_validador_cero_hallazgos(servicio):
    _, c = servicio
    llm.fake.responder = guion_revision()
    r = c.post("/v1/agente", json={"tarea": "Revisa limites.py"}, headers=cabeceras(c))
    assert r.status_code == 200
    d = r.json()
    assert d["terminado"] and d["validador"]["ok"] and d["pendientes"] == []
    assert d["pasos"][0]["herramienta"] == "correr_linter"
    assert d["pasos"][0]["resultado"]["hallazgos"] == []


def test_api_fallo_archivo_inexistente_visible_sin_ruta_privada(servicio):
    _, c = servicio
    llm.fake.responder = guion_revision("inexistente.py")
    r = c.post("/v1/agente", json={"tarea": "Revisa inexistente.py"}, headers=cabeceras(c))
    d = r.json()
    assert r.status_code == 200 and d["pasos"][0]["estado"] == "fallida" and not d["terminado"]
    assert d["pasos"][0]["resultado"]["clase"] == "FileNotFoundError"
    assert "OneDrive" not in r.text and "TOKEN_SECRET" not in r.text


def test_api_rechazo_no_crea_informe(servicio, tmp_path, monkeypatch):
    _, c = servicio
    destino = tmp_path / "informes"
    monkeypatch.setenv("A4_INFORMES_DIR", str(destino))
    llm.fake.responder = guion_guardado()
    h = cabeceras(c)
    r = c.post("/v1/agente", json={"tarea": "Revisa usuarios.py y guarda revision.json"}, headers=h).json()
    assert r["validador"]["ok"] and len(r["pendientes"]) == 1 and not destino.exists()
    identificador = r["pendientes"][0]["id"]
    rechazo = c.post("/v1/agente/confirmar/" + identificador, json={"aprobar": False}, headers=h)
    assert rechazo.status_code == 200 and rechazo.json()["estado"] == "rechazada" and not destino.exists()
    comprobar_problema(c.post("/v1/agente/confirmar/" + identificador, json={"aprobar": True}, headers=h), 404)


def test_api_bloquea_respuesta_inventada(servicio):
    _, c = servicio
    llm.fake.responder = lambda p, s: json.dumps({"accion": "responder", "respuesta": "SEC-99 linea 999", "fuentes": ["inventada"]})
    d = c.post("/v1/agente", json={"tarea": "Revisa usuarios.py"}, headers=cabeceras(c)).json()
    assert not d["validador"]["ok"] and d["fuentes"] == []
    assert d["respuesta"] == "Respuesta bloqueada por el validador."


def test_api_decision_estricta_y_sin_campos_extras(servicio):
    _, c = servicio
    h = cabeceras(c)
    for cuerpo in ({"aprobar": 1}, {"aprobar": "true"}, {"aprobar": True, "nombre": "otro.json"}):
        comprobar_problema(c.post("/v1/agente/confirmar/noexiste", json=cuerpo, headers=h), 422)
    comprobar_problema(c.post("/v1/agente", json={"tarea": "Revisar", "archivo": "../.env"}, headers=h), 422)
