"""Comprobaciones deterministas de citas, codigo de entrada y acciones pendientes."""
from __future__ import annotations

import hashlib

from .herramientas_revisor import MAPA, MENSAJES, archivo_autorizado, reglas, resumen_autorizado

CONTROLES = {
    "Informe pendiente de confirmacion; todavia no se guardo.",
    "Accion rechazada; no se guardo ningun informe.",
    "Se detuvo una accion repetida.",
    "Se alcanzo el limite de pasos sin una respuesta final valida.",
    "La herramienta fallo; no se emitio una revision.",
}


def validar_analisis(resultado: dict) -> list[str]:
    errores = []
    try:
        contenido = archivo_autorizado(resultado["ruta"]).read_bytes()
        lineas = contenido.decode("utf-8").splitlines()
        corpus = reglas()
        if resultado["huella"] != hashlib.sha256(contenido).hexdigest():
            errores.append("La huella no corresponde a la entrada")
        vistos = set()
        for h in resultado["hallazgos"]:
            linea, regla = h["linea"], h["regla"]
            if type(linea) is not int or not 1 <= linea <= len(lineas):
                errores.append("Linea inexistente")
                continue
            if regla not in corpus or h["fuente"] != corpus[regla]["fuente"]:
                errores.append("Regla o fuente inexistente")
            if h["evidencia"] != lineas[linea - 1]:
                errores.append("La evidencia no coincide con el codigo")
            if MAPA.get(h["codigo_ruff"]) != regla or MENSAJES.get(h["codigo_ruff"]) != h["detalle"]:
                errores.append("Hallazgo fuera de las reglas del analizador")
            clave = (linea, h["codigo_ruff"], h["columna"])
            if clave in vistos:
                errores.append("Hallazgo duplicado")
            vistos.add(clave)
        fuentes = sorted({h["fuente"] for h in resultado["hallazgos"]})
        if resultado["fuentes"] != fuentes:
            errores.append("Fuentes no respaldadas por los hallazgos")
        if resultado["respuesta_autorizada"] != resumen_autorizado(resultado["ruta"], resultado["hallazgos"]):
            errores.append("El resumen agrega informacion ajena a los hallazgos")
        if resultado["ruta"] == "limites.py" and resultado["hallazgos"]:
            errores.append("El caso de control limites.py debe tener cero hallazgos")
    except (KeyError, TypeError, ValueError, OSError, UnicodeError):
        errores.append("Estructura de analisis o archivo invalido")
    return errores


def validar_resultado(resultado, propuestas) -> list[str]:
    errores = []
    analisis = []
    for paso in resultado.pasos:
        if paso.estado == "ejecutada" and paso.propuesta.get("herramienta") == "correr_linter":
            if not isinstance(paso.resultado, dict):
                errores.append("La herramienta no devolvio un objeto")
            else:
                errores.extend(validar_analisis(paso.resultado))
                analisis.append(paso.resultado)
    for nombre, args in propuestas:
        if nombre != "guardar_informe" or not any(a["ruta"] == args.get("ruta") and
                a["huella"] == args.get("huella") for a in analisis):
            errores.append("El guardado no esta respaldado por el analisis de esta solicitud")
    if resultado.respuesta in CONTROLES and not resultado.terminado:
        if resultado.fuentes:
            errores.append("El mensaje de control no admite fuentes")
        return errores
    if not analisis:
        errores.append("Falta un analisis ejecutado que respalde la respuesta")
    elif not any(resultado.respuesta == a["respuesta_autorizada"] and
                 sorted(resultado.fuentes) == a["fuentes"] for a in analisis):
        errores.append("La respuesta o sus fuentes agregan informacion no respaldada")
    return errores
