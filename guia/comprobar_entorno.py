import importlib
import importlib.metadata as m
import json
import sys
from pathlib import Path

NOMBRES = ["fastapi", "starlette", "pydantic", "streamlit", "ruff", "pytest", "requests", "jsonschema"]
for nombre in NOMBRES:
    importlib.import_module(nombre)
datos = {"python": sys.version, "paquetes": {n: m.version(n) for n in NOMBRES}}
destino = Path(__file__).resolve().parents[1] / "bitacora" / "a4" / "entorno_inicial.json"
destino.parent.mkdir(parents=True, exist_ok=True)
destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(datos, ensure_ascii=False, indent=2))
