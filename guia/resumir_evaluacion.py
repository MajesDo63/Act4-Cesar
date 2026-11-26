"""Tabla legible obtenida de los registros reales de la ultima evaluacion."""
import csv
import json
from pathlib import Path

raiz = Path(__file__).resolve().parents[1]
carpeta = raiz / (raiz / "bitacora/a4/ultima_evaluacion.txt").read_text(encoding="utf-8").strip()
if json.loads((carpeta / "estado.json").read_text(encoding="utf-8"))["estado"] != "completo":
    raise SystemExit("La evaluacion aun no esta completa")
resultados = json.loads((carpeta / "resumen.json").read_text(encoding="utf-8"))
pruebas = json.loads((carpeta / "pruebas.json").read_text(encoding="utf-8"))
filas = []
for fila in resultados:
    m = fila["metricas"]
    filas.append({"version": fila["version"], "archivo": fila["archivo"],
                  "hallazgos": m["hallazgos_detectados"], "referencia_ruff_v2": m["hallazgos_referencia_ruff_v2"],
                  "omisiones": m["omisiones_en_alcance"], "correcto_en_alcance": m["correcto_en_alcance"],
                  "clasificacion": ", ".join(m["clasificacion"]), "latencia_ms": fila["latencia_ms"]})
destino = raiz / "a4/RESULTADOS.csv"
with destino.open("w", newline="", encoding="utf-8-sig") as archivo:
    w = csv.DictWriter(archivo, fieldnames=list(filas[0]))
    w.writeheader()
    w.writerows(filas)
tabla = ["# Resultados de ejecucion", "", f"Suite actual: **{pruebas['aprobadas']} aprobadas; {pruebas['omitidas']} omitidas**.", "",
         "| Version | Entrada | Hallazgos | Referencia Ruff v2 | Omisiones | Clasificacion |", "|---|---|---:|---:|---:|---|"]
for fila in filas:
    tabla.append(f"| {fila['version']} | {fila['archivo']} | {fila['hallazgos']} | {fila['referencia_ruff_v2']} | {fila['omisiones']} | {fila['clasificacion']} |")
tabla.extend(["", "La clasificacion inconsistencia se refiere al contrato exacto del resumen y las fuentes: no demuestra por si sola que la respuesta contenga datos falsos.",
              "Las omisiones se cuentan respecto de las reglas de Ruff del perfil final, no de todas las politicas SEC.",
              "Esta ronda contiene una ejecucion por entrada y version; no demuestra estabilidad estadistica ni cobertura general.",
              "", f"Registros originales: `{carpeta.relative_to(raiz)}`.", ""])
(raiz / "a4/RESULTADOS.md").write_text("\n".join(tabla), encoding="utf-8")
print("Resultados consolidados: " + str(destino))
