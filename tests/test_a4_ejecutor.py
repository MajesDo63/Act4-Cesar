import json

import pytest

from finnorte import llm
from finnorte.herramientas import Herramienta, ejecutar_agente

ESQUEMA = {"type": "object", "properties": {"valor": {"type": "integer", "minimum": 1}}, "required": ["valor"]}


def usar(argumentos=None, nombre="efecto"):
    return {"accion": "usar", "herramienta": nombre, "argumentos": argumentos or {"valor": 1}}


@pytest.mark.parametrize("decision", [False, None, 1, "si"])
def test_sensible_exige_true_literal(decision):
    efectos = []
    h = Herramienta("efecto", "Efecto controlado", ESQUEMA, lambda valor: efectos.append(valor), True)
    llm.fake.responder = lambda p, s: json.dumps(usar())
    r = ejecutar_agente("Preparar efecto", [h], confirmar=lambda h, a: decision)
    assert efectos == [] and not r.terminado
    assert r.pasos[0].estado in ("sin_confirmar", "rechazada")


def test_aprobacion_ejecuta_argumentos_validados_no_mutacion_callback():
    efectos = []
    h = Herramienta("efecto", "Efecto", ESQUEMA, lambda valor: efectos.append(valor), True)
    it = iter([usar(), {"accion": "responder", "respuesta": "Listo", "fuentes": []}])
    llm.fake.responder = lambda p, s: json.dumps(next(it))
    def confirmar(h, args):
        args["valor"] = 999
        return True
    ejecutar_agente("Preparar efecto", [h], confirmar=confirmar)
    assert efectos == [1]


@pytest.mark.parametrize("args", [{"valor": "1"}, {"valor": True}, {"valor": 0}, {"valor": 1, "extra": "x"}, {}])
def test_argumentos_invalidos_no_producen_efecto(args):
    efectos = []
    h = Herramienta("efecto", "Efecto", ESQUEMA, lambda **a: efectos.append(a))
    llm.fake.responder = lambda p, s: json.dumps({"accion": "usar", "herramienta": "efecto", "argumentos": args})
    r = ejecutar_agente("Validar argumentos", [h], max_pasos=2)
    assert efectos == [] and all(p.estado == "invalida" for p in r.pasos)


def test_repeticion_no_repite_efecto():
    efectos = []
    h = Herramienta("efecto", "Efecto", ESQUEMA, lambda valor: efectos.append(valor))
    llm.fake.responder = lambda p, s: json.dumps(usar())
    r = ejecutar_agente("Repetir accion", [h])
    assert efectos == [1] and r.pasos[-1].estado == "repetida" and not r.terminado


def test_fallo_no_filtra_excepcion_ni_se_confunde_con_exito():
    def fallo(valor):
        raise FileNotFoundError("C:/ruta/privada/secreto.env")
    h = Herramienta("efecto", "Fallo", ESQUEMA, fallo)
    llm.fake.responder = lambda p, s: json.dumps(usar())
    r = ejecutar_agente("Provocar fallo", [h])
    assert r.pasos[0].estado == "fallida" and not r.terminado
    assert "secreto.env" not in str(r)


@pytest.mark.parametrize("maximo", [0, 9, True, -1])
def test_limite_pasos_obligatorio(maximo):
    with pytest.raises(ValueError):
        ejecutar_agente("tarea", [], max_pasos=maximo)


def test_catalogo_no_admite_nombres_duplicados():
    h = Herramienta("efecto", "Efecto", ESQUEMA, lambda valor: valor)
    with pytest.raises(ValueError):
        ejecutar_agente("tarea", [h, h])


@pytest.mark.parametrize("propuesta", [[], "texto", {"accion": "ejecutar"}, {"accion": "responder", "respuesta": "x", "fuentes": "SEC-01"}])
def test_protocolo_rechaza_estructuras_ajenas(propuesta):
    llm.fake.responder = lambda p, s: json.dumps(propuesta)
    r = ejecutar_agente("tarea", [], max_pasos=1)
    assert not r.terminado and r.pasos[0].estado == "invalida"
