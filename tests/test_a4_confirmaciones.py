import json
import time

import pytest

from finnorte import agente_revisor, agente_servicio, llm
from finnorte.herramientas_revisor import directorio_informes


def guion_guardado(nombre="revision.json"):
    def responder(prompt, sistema):
        datos = json.loads(prompt)
        observaciones = datos["observaciones"]
        if not observaciones:
            return json.dumps({"accion": "usar", "herramienta": "correr_linter", "argumentos": {"ruta": "usuarios.py"}})
        a = observaciones[-1]["resultado"]
        return json.dumps({"accion": "usar", "herramienta": "guardar_informe",
                           "argumentos": {"ruta": a["ruta"], "huella": a["huella"], "nombre": nombre}})
    return responder


@pytest.fixture
def pendiente(tmp_path, monkeypatch):
    monkeypatch.setenv("A4_INFORMES_DIR", str(tmp_path / "informes"))
    agente_servicio._PENDIENTES.clear()
    llm.fake.responder = guion_guardado()
    salida = agente_revisor.iniciar("Revisa usuarios.py y guarda revision.json", "cesar")
    assert salida["validador"]["ok"] and len(salida["pendientes"]) == 1
    assert not (tmp_path / "informes").exists()
    yield salida["pendientes"][0], tmp_path
    agente_servicio._PENDIENTES.clear()


def test_rechazar_no_crea_directorio_ni_archivo(pendiente):
    p, carpeta = pendiente
    r = agente_servicio.resolver(p["id"], "cesar", False)
    assert r["estado"] == "rechazada" and r["efecto"] is False
    assert not (carpeta / "informes").exists()


def test_aprobar_conserva_clausura_y_crea_un_informe(pendiente):
    p, _ = pendiente
    r = agente_servicio.resolver(p["id"], "cesar", True)
    assert r["estado"] == "ejecutada"
    guardado = json.loads((directorio_informes("cesar") / "revision.json").read_text(encoding="utf-8"))
    assert guardado["huella"] == p["argumentos"]["huella"]
    with pytest.raises(KeyError):
        agente_servicio.resolver(p["id"], "cesar", True)


def test_otro_usuario_no_consume_confirmacion(pendiente):
    p, _ = pendiente
    with pytest.raises(KeyError):
        agente_servicio.resolver(p["id"], "intruso", True)
    assert agente_servicio.resolver(p["id"], "cesar", False)["estado"] == "rechazada"


def test_expirada_no_guarda(pendiente):
    p, carpeta = pendiente
    agente_servicio._PENDIENTES[p["id"]].creado = time.time() - 601
    assert agente_servicio.resolver(p["id"], "cesar", True)["estado"] == "expirada"
    assert not (carpeta / "informes").exists()


def test_respuesta_no_permite_cambiar_argumentos_guardados(pendiente):
    p, _ = pendiente
    p["argumentos"]["nombre"] = "cambiado.json"
    r = agente_servicio.resolver(p["id"], "cesar", True)
    assert r["estado"] == "ejecutada" and r["resultado"]["nombre"] == "revision.json"


def test_no_reemplaza_informe_existente(pendiente):
    p, _ = pendiente
    d = directorio_informes("cesar")
    d.mkdir(parents=True)
    (d / "revision.json").write_text("original", encoding="utf-8")
    assert agente_servicio.resolver(p["id"], "cesar", True)["estado"] == "fallida"
    assert (d / "revision.json").read_text(encoding="utf-8") == "original"


def test_cambio_archivo_tras_revision_bloquea_guardado(pendiente, monkeypatch):
    from finnorte import herramientas_revisor as hr
    p, carpeta = pendiente
    ejemplo = carpeta / "ejemplos"
    ejemplo.mkdir()
    (ejemplo / "usuarios.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(hr, "CODIGOS", ejemplo)
    assert agente_servicio.resolver(p["id"], "cesar", True)["estado"] == "fallida"
    assert not (carpeta / "informes").exists()


def test_guardado_sin_consulta_previa_se_bloquea(tmp_path, monkeypatch):
    monkeypatch.setenv("A4_INFORMES_DIR", str(tmp_path / "informes"))
    agente_servicio._PENDIENTES.clear()
    llm.fake.responder = lambda p, s: json.dumps({"accion": "usar", "herramienta": "guardar_informe",
        "argumentos": {"ruta": "usuarios.py", "huella": "0" * 64, "nombre": "revision.json"}})
    r = agente_revisor.iniciar("Guardar sin analizar", "cesar")
    assert not r["validador"]["ok"] and r["pendientes"] == [] and not agente_servicio._PENDIENTES


def test_confirmacion_no_admite_entero(pendiente):
    p, _ = pendiente
    with pytest.raises(ValueError):
        agente_servicio.resolver(p["id"], "cesar", 1)


def test_confirmacion_concurrente_solo_un_efecto(pendiente):
    from concurrent.futures import ThreadPoolExecutor
    p, _ = pendiente
    def decidir(_):
        try:
            return agente_servicio.resolver(p["id"], "cesar", True)["estado"]
        except KeyError:
            return "consumida"
    with ThreadPoolExecutor(max_workers=2) as grupo:
        estados = list(grupo.map(decidir, range(2)))
    assert sorted(estados) == ["consumida", "ejecutada"]
