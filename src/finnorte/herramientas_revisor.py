"""Herramientas propias de A4: analisis estatico y guardado sujeto a confirmacion."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from .config import RAIZ
from .herramientas import Herramienta

CODIGOS = RAIZ / "datos" / "v2-revisor" / "codigo"
ARCHIVOS = ("usuarios.py", "limites.py", "tokens.py", "reportes.py", "cuentas_api.py",
            "comisiones.py", "transferencias.py", "notificador.py")
MAPA = {"S311": "SEC-06", "S324": "SEC-06", "S608": "SEC-02", "S301": "SEC-09",
        "S307": "SEC-09", "S602": "SEC-09", "S506": "SEC-09"}
MENSAJES = {"S311": "Aleatoriedad no criptografica.", "S324": "Algoritmo criptografico debil.",
            "S608": "Consulta SQL construida como cadena.", "S301": "Deserializacion con pickle.",
            "S307": "Evaluacion dinamica con eval.", "S602": "Comando con shell=True.",
            "S506": "Carga YAML sin SafeLoader."}
ESQUEMA_RUTA = {"type": "string", "enum": [*ARCHIVOS, "inexistente.py"]}
ESQUEMA_LINTER = {"type": "object", "properties": {"ruta": ESQUEMA_RUTA},
                  "required": ["ruta"], "additionalProperties": False}
ESQUEMA_GUARDAR = {"type": "object", "properties": {
    "ruta": {"type": "string", "enum": list(ARCHIVOS)},
    "huella": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
    "nombre": {"type": "string", "pattern": "^[a-zA-Z0-9_-]{1,40}\\.json$"}},
    "required": ["ruta", "huella", "nombre"], "additionalProperties": False}


def archivo_autorizado(ruta: str) -> Path:
    if not isinstance(ruta, str) or ruta not in (*ARCHIVOS, "inexistente.py"):
        raise ValueError("Solo se admiten nombres del catalogo de ejemplos")
    archivo = CODIGOS / ruta
    if archivo.is_symlink() or archivo.resolve().parent != CODIGOS.resolve():
        raise ValueError("Ruta fuera del directorio permitido")
    if not archivo.is_file():
        raise FileNotFoundError("El ejemplo solicitado no existe")
    if archivo.stat().st_size > 20000:
        raise ValueError("El ejemplo supera 20000 bytes")
    return archivo


def reglas() -> dict[str, dict]:
    salida = {}
    for archivo in sorted((RAIZ / "corpus" / "v2-revisor").glob("*.md")):
        texto = archivo.read_text(encoding="utf-8")
        match = re.search(r"Regla (SEC-\d\d): ([^\n]+)", texto)
        if match:
            salida[match[1]] = {"fuente": f"corpus/v2-revisor/{archivo.name}", "texto": match[0]}
    return salida


def resumen_autorizado(ruta, hallazgos):
    resumen = f"{ruta}: {len(hallazgos)} hallazgo(s) dentro del alcance de Ruff."
    if hallazgos:
        return resumen + " " + " ".join(f"{h['regla']} linea {h['linea']}: {h['detalle']}" for h in hallazgos)
    return resumen + " Este resultado no acredita la ausencia de todos los riesgos de seguridad."


def correr_linter(ruta: str, perfil: str = "v2") -> dict:
    if perfil not in ("v1", "v2"):
        raise ValueError("Perfil no disponible")
    archivo = archivo_autorizado(ruta)
    contenido = archivo.read_bytes()
    # Se pasa el contenido por stdin: Ruff no sigue imports ni ejecuta el codigo.
    seleccion = ["S311", "S324", "S608"] if perfil == "v1" else list(MAPA)
    comando = [sys.executable, "-m", "ruff", "check", "--isolated", "--no-cache",
               "--output-format", "json", "--select", ",".join(seleccion), "--stdin-filename", ruta, "-"]
    proceso = subprocess.run(comando, input=contenido, capture_output=True, timeout=10, shell=False)
    if proceso.returncode not in (0, 1) or len(proceso.stdout) > 250000:
        raise RuntimeError("Ruff no produjo un resultado valido")
    crudos = json.loads(proceso.stdout)
    corpus = reglas()
    lineas = contenido.decode("utf-8").splitlines()
    hallazgos = []
    for item in crudos:
        identificador = MAPA[item["code"]]
        linea = item["location"]["row"]
        if not 1 <= linea <= len(lineas) or identificador not in corpus:
            raise ValueError("Referencia de analisis invalida")
        hallazgos.append({"regla": identificador, "linea": linea, "columna": item["location"]["column"],
                          "codigo_ruff": item["code"], "detalle": MENSAJES[item["code"]],
                          "evidencia": lineas[linea - 1], "fuente": corpus[identificador]["fuente"]})
    fuentes = sorted({h["fuente"] for h in hallazgos})
    resumen = resumen_autorizado(ruta, hallazgos)
    return {"ruta": ruta, "huella": hashlib.sha256(contenido).hexdigest(), "hallazgos": hallazgos,
            "fuentes": fuentes, "respuesta_autorizada": resumen,
            "alcance": {"motor": "Ruff", "reglas": seleccion, "perfil": perfil, "ejecuta_codigo": False},
            "reglas_citadas": {k: corpus[k] for k in sorted({h["regla"] for h in hallazgos})}}


def directorio_informes(usuario: str) -> Path:
    base = Path(os.getenv("A4_INFORMES_DIR", str(RAIZ / "bitacora" / "a4" / "informes")))
    return base / hashlib.sha256(usuario.encode()).hexdigest()[:24]


def herramientas_revisor(usuario: str, version: str = "v2") -> list[Herramienta]:
    analisis: dict[tuple[str, str], dict] = {}

    def analizar(ruta):
        resultado = correr_linter(ruta, perfil=version)
        analisis[(ruta, resultado["huella"])] = resultado
        return resultado

    def guardar(ruta, huella, nombre):
        # Esta clausura se crea por solicitud. La confirmacion revalida el analisis guardado.
        import jsonschema
        jsonschema.validate({"ruta": ruta, "huella": huella, "nombre": nombre}, ESQUEMA_GUARDAR)
        archivo = archivo_autorizado(ruta)
        if hashlib.sha256(archivo.read_bytes()).hexdigest() != huella:
            raise ValueError("El archivo cambio despues de la revision")
        resultado = analisis.get((ruta, huella))
        if resultado is None:
            raise ValueError("Falta el analisis de esta misma solicitud")
        destino = directorio_informes(usuario)
        destino.mkdir(parents=True, exist_ok=True)
        if destino.is_symlink():
            raise ValueError("Directorio no permitido")
        with (destino / nombre).open("x", encoding="utf-8") as salida:
            json.dump(resultado, salida, ensure_ascii=False, indent=2)
        return {"guardado": True, "nombre": nombre, "huella": huella}

    return [Herramienta("correr_linter", "Analiza un ejemplo del catalogo sin ejecutarlo.", ESQUEMA_LINTER, analizar),
            Herramienta("guardar_informe", "Guarda el analisis de esta solicitud, con su huella exacta; requiere confirmacion.",
                        ESQUEMA_GUARDAR, guardar, sensible=True)]
