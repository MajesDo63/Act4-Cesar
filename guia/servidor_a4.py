import os
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(raiz))
sys.path.insert(0, str(raiz / "src"))
os.environ["AUTH_DB"] = str(raiz / "bitacora" / "a4" / "usuarios_local.db")
os.environ["FINNORTE_DIR_TRAZAS"] = str(raiz / "bitacora" / "a4" / "sesion_interfaz")
from finnorte.config import config
import uvicorn

if __name__ == "__main__":
    uvicorn.run("api.producto:app", host="127.0.0.1", port=8004, log_level="info")
