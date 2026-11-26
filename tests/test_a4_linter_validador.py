from copy import deepcopy

import pytest

from finnorte import herramientas_revisor as modulo
from finnorte.herramientas import Paso, ResultadoAgente
from finnorte.herramientas_revisor import correr_linter
from finnorte.validador_a4 import validar_analisis, validar_resultado


@pytest.mark.parametrize("archivo,codigos", [("usuarios.py", {"S324", "S311"}), ("limites.py", set()),
    ("tokens.py", {"S506"}), ("reportes.py", {"S301", "S602"}), ("transferencias.py", {"S608"}), ("cuentas_api.py", set())])
def test_ruff_real_y_referencias_validas(archivo, codigos):
    a = correr_linter(archivo)
    assert {h["codigo_ruff"] for h in a["hallazgos"]} == codigos
    assert not validar_analisis(a)


@pytest.mark.parametrize("ruta", ["../.env", "/tmp/secreto.py", "C:\\Windows\\win.ini", ".env", "usuarios.py --fix", "sub/usuarios.py", "\\\\server\\share"])
def test_linter_bloquea_rutas_y_opciones(ruta):
    with pytest.raises(ValueError):
        correr_linter(ruta)


def test_archivo_inexistente_es_un_fallo_explicito():
    with pytest.raises(FileNotFoundError):
        correr_linter("inexistente.py")


def test_no_ejecuta_codigo_imports_ni_efectos(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo, "CODIGOS", tmp_path)
    (tmp_path / "usuarios.py").write_text("raise RuntimeError('Este codigo no debe ejecutarse')\n", encoding="utf-8")
    a = correr_linter("usuarios.py")
    assert a["hallazgos"] == [] and a["alcance"]["ejecuta_codigo"] is False


def test_limite_tamano(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo, "CODIGOS", tmp_path)
    (tmp_path / "usuarios.py").write_bytes(b"x" * 20001)
    with pytest.raises(ValueError):
        correr_linter("usuarios.py")


@pytest.mark.parametrize("campo,valor", [("regla", "SEC-99"), ("linea", 999), ("linea", True),
    ("evidencia", "codigo inventado"), ("fuente", "https://ajena.example"),
    ("detalle", "Aprobado para produccion"), ("codigo_ruff", "S999")])
def test_validador_rechaza_hallazgos_manipulados(campo, valor):
    a = correr_linter("usuarios.py")
    a["hallazgos"][0][campo] = valor
    assert validar_analisis(a)


def test_validador_rechaza_resumen_y_huella_modificados():
    a = correr_linter("usuarios.py")
    a["respuesta_autorizada"] += " Publica sin riesgos."
    a["huella"] = "0" * 64
    assert len(validar_analisis(a)) >= 2


def test_respuesta_sin_respaldo_y_fuente_ajena_se_bloquean():
    a = correr_linter("usuarios.py")
    p = Paso(1, {"herramienta": "correr_linter"}, a, "ejecutada")
    r = ResultadoAgente(a["respuesta_autorizada"], a["fuentes"], [p])
    assert not validar_resultado(r, [])
    r.respuesta += " SEC-99 en linea 999."
    assert validar_resultado(r, [])
    r.respuesta = a["respuesta_autorizada"]
    r.fuentes = ["sitio-ajeno"]
    assert validar_resultado(r, [])


def test_no_se_ofrece_guardado_sin_analizar_misma_huella():
    r = ResultadoAgente("Informe pendiente de confirmacion; todavia no se guardo.", [], [], False)
    assert validar_resultado(r, [("guardar_informe", {"ruta": "usuarios.py", "huella": "0" * 64})])


def test_mejora_cobertura_sobre_mismos_archivos():
    assert correr_linter("reportes.py", "v1")["hallazgos"] == []
    assert {h["codigo_ruff"] for h in correr_linter("reportes.py", "v2")["hallazgos"]} == {"S301", "S602"}
    assert correr_linter("tokens.py", "v1")["hallazgos"] == []
    assert len(correr_linter("tokens.py", "v2")["hallazgos"]) == 1
