"""Fija la dependencia transitiva usada en Windows, sin incluir herramientas ajenas."""
from importlib.metadata import distribution
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

pendientes = ["numpy", "requests", "jsonschema", "pyyaml", "pytest", "fastapi", "starlette", "uvicorn", "httpx", "streamlit", "ruff"]
versiones = {}
while pendientes:
    nombre = canonicalize_name(pendientes.pop())
    if nombre in versiones:
        continue
    dist = distribution(nombre)
    versiones[nombre] = dist.version
    for texto in dist.requires or []:
        req = Requirement(texto)
        if req.marker is None or req.marker.evaluate({"extra": ""}):
            pendientes.append(req.name)
salida = Path(__file__).resolve().parents[1] / "requirements-windows.lock.txt"
salida.write_text("# Windows, Python 3.14.7; dependencias de la ejecucion verificada.\n" +
                  "\n".join(f"{n}=={v}" for n, v in sorted(versiones.items())) + "\n", encoding="utf-8")
print(f"Dependencias registradas: {len(versiones)}")
