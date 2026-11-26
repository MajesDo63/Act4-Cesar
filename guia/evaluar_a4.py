"""Pruebas completas y dos rondas reales de cinco entradas; conserva cada intento."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ))
os.environ["LLM_PROVIDER"] = "gemini"
os.environ["EMB_PROVIDER"] = "hash"
os.environ["LLM_RETRIES"] = "1"
os.environ["LLM_TIMEOUT"] = "60"
from finnorte import agente_revisor, llm
from finnorte.config import config
from finnorte.herramientas_revisor import correr_linter

CASOS = ["usuarios.py", "limites.py", "tokens.py", "reportes.py", "transferencias.py"]


def guardar(ruta, datos):
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def huellas():
    rutas = []
    for carpeta in ("src", "api", "app", "tests", "corpus", "datos"):
        rutas.extend(p for p in (RAIZ / carpeta).rglob("*") if p.is_file() and
                      "__pycache__" not in p.parts and p.suffix in (".py", ".md", ".json", ".txt"))
    rutas.extend(RAIZ / n for n in ("requirements.txt", "pyproject.toml"))
    return {str(p.relative_to(RAIZ)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(rutas)}


def clasificar(salida, esperado):
    estados = [p["estado"] for p in salida["pasos"]]
    errores = []
    if not salida["validador"]["ok"]:
        errores.append("inconsistencia")
    analisis = [p["resultado"] for p in salida["pasos"] if p["herramienta"] == "correr_linter" and p["estado"] == "ejecutada"]
    detectados = {(h["codigo_ruff"], h["linea"]) for a in analisis for h in a["hallazgos"]}
    referencia = {(h["codigo_ruff"], h["linea"]) for h in esperado["hallazgos"]}
    if referencia - detectados or not analisis:
        errores.append("omision")
    if detectados - referencia:
        errores.append("alucinacion")
    if not salida["terminado"] and not errores:
        errores.append("generico")
    return {"clasificacion": errores or ["sin_error_en_alcance"],
            "hallazgos_detectados": len(detectados), "hallazgos_referencia_ruff_v2": len(referencia),
            "omisiones_en_alcance": len(referencia - detectados), "estados": estados,
            "correcto_en_alcance": salida["terminado"] and salida["validador"]["ok"] and detectados == referencia}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reanudar", action="store_true")
    opciones = ap.parse_args()
    base = RAIZ / "bitacora" / "a4"
    base.mkdir(parents=True, exist_ok=True)
    actual = base / "ultima_evaluacion.txt"
    if opciones.reanudar and actual.exists():
        salida = RAIZ / actual.read_text(encoding="utf-8").strip()
        if json.loads((salida / "huellas.json").read_text(encoding="utf-8")) != huellas():
            raise RuntimeError("El codigo cambio desde esa ronda. Debe iniciarse una evaluacion nueva.")
    else:
        salida = base / ("evaluacion_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        salida.mkdir()
        guardar(salida / "huellas.json", huellas())
        actual.write_text(str(salida.relative_to(RAIZ)), encoding="utf-8")
    os.environ["FINNORTE_DIR_TRAZAS"] = str(salida)
    guardar(salida / "ejecucion.json", {"fecha_utc": datetime.now(timezone.utc).isoformat(),
        "directorio": str(RAIZ), "interprete": sys.executable, "sistema": platform.platform(),
        "comando": "guia/evaluar_a4.py" + (" --reanudar" if opciones.reanudar else ""),
        "proveedor": config().llm_proveedor, "modelo": config().llm_modelo, "casos": CASOS})
    try:
        pruebas = salida / "pruebas.json"
        if not pruebas.exists():
            entorno = dict(os.environ, LLM_PROVIDER="fake", EMB_PROVIDER="hash", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                           AUTH_DB=str(salida / "auth_pruebas.db"))
            comando = [sys.executable, "-m", "pytest", "tests", "-q", "--junitxml=" + str(salida / "pytest.xml")]
            proceso = subprocess.run(comando, cwd=RAIZ, env=entorno, capture_output=True, timeout=180)
            texto = proceso.stdout.decode("utf-8", errors="replace") + proceso.stderr.decode("utf-8", errors="replace")
            (salida / "pytest.txt").write_text(texto, encoding="utf-8")
            print(texto, flush=True)
            if proceso.returncode != 0:
                raise RuntimeError("La suite no aprobo; consulta pytest.txt")
            nodos = ET.parse(salida / "pytest.xml").findall(".//testcase")
            omitidas = sum(n.find("skipped") is not None for n in nodos)
            if omitidas:
                raise RuntimeError("Hay pruebas omitidas")
            guardar(pruebas, {"aprobadas": len(nodos), "omitidas": omitidas, "comando": comando})
        print("PRUEBAS APROBADAS. Iniciando comparacion real con Gemini.", flush=True)
        resumen = []
        generar_original = llm.generar
        for version in ("v1", "v2"):
            for archivo in CASOS:
                destino = salida / f"{version}_{archivo.removesuffix('.py')}.json"
                if destino.exists():
                    datos = json.loads(destino.read_text(encoding="utf-8"))
                    print(f"{version} {archivo}: resultado conservado", flush=True)
                else:
                    esperado = correr_linter(archivo)
                    intentos = []
                    datos = None
                    for intento in range(1, 4):
                        llamadas = []
                        def registrar(prompt, sistema=None, **kwargs):
                            r = generar_original(prompt, sistema=sistema, **kwargs)
                            llamadas.append({"prompt": prompt, "sistema": sistema, "respuesta": r.texto,
                                "json": r.datos, "modelo": r.modelo, "proveedor": r.proveedor,
                                "tokens_entrada": r.tokens_entrada, "tokens_salida": r.tokens_salida,
                                "latencia_ms": r.latencia_ms, "intentos": r.intentos})
                            return r
                        llm.generar = registrar
                        inicio = time.perf_counter()
                        try:
                            resultado = agente_revisor.iniciar(f"Revisa {archivo} con correr_linter.", "evaluacion-a4", version)
                            datos = {"version": version, "archivo": archivo, "resultado": resultado,
                                     "metricas": clasificar(resultado, esperado), "llamadas": llamadas,
                                     "latencia_ms": round((time.perf_counter() - inicio) * 1000, 1),
                                     "intentos_previos": intentos}
                            guardar(destino, datos)
                            break
                        except llm.LLMError as error:
                            # Solo se persiste el tipo: una excepcion de red puede incluir datos de conexion.
                            intento_datos = {"version": version, "archivo": archivo, "intento": intento,
                                             "error": type(error).__name__, "llamadas_completadas": llamadas}
                            intentos.append(intento_datos)
                            guardar(salida / f"intento_{version}_{archivo}_{intento}.json", intento_datos)
                            print(f"{version} {archivo}: proveedor no disponible, intento {intento}/3", flush=True)
                            if intento < 3:
                                time.sleep(5)
                        finally:
                            llm.generar = generar_original
                    if datos is None:
                        raise RuntimeError("Proveedor no disponible; reanuda para conservar lo aprobado")
                    print(f"{version} {archivo}: {', '.join(datos['metricas']['clasificacion'])}", flush=True)
                resumen.append({k: datos[k] for k in ("version", "archivo", "metricas", "latencia_ms")})
        if huellas() != json.loads((salida / "huellas.json").read_text(encoding="utf-8")):
            raise RuntimeError("Cambio el codigo durante la evaluacion")
        guardar(salida / "resumen.json", resumen)
        guardar(salida / "estado.json", {"estado": "completo", "fecha_utc": datetime.now(timezone.utc).isoformat()})
        print("EVALUACION A4 COMPLETA: " + str(salida), flush=True)
    except (Exception, KeyboardInterrupt) as error:
        guardar(salida / "estado.json", {"estado": "interrumpido", "clase": type(error).__name__})
        print("PROCESO INTERRUMPIDO. Los resultados completos se conservan en " + str(salida), flush=True)
        print(str(error) if not isinstance(error, llm.LLMError) else "Fallo del proveedor", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
