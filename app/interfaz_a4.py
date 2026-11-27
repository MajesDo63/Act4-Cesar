"""Entrada compatible para abrir la interfaz unificada de la Actividad 4."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("cliente_api.py")), run_name="__main__")
