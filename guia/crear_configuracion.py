"""Configuracion interactiva para una copia nueva; nunca imprime credenciales."""
from getpass import getpass
from pathlib import Path
import secrets

destino = Path(__file__).resolve().parents[1] / ".env"
if destino.exists():
    raise SystemExit("Ya existe .env. Se conserva la configuracion local.")
llave = getpass("Llave de Gemini (entrada oculta): ").strip()
if len(llave) < 20 or any(c in llave for c in "\r\n\x00"):
    raise SystemExit("La llave tiene un formato no valido. No se guardo.")
texto = ("LLM_PROVIDER=gemini\nLLM_MODEL=gemini-3.1-flash-lite\nGEMINI_API_KEY=" + llave +
         "\nTOKEN_SECRET=" + secrets.token_urlsafe(48) + "\nEMB_PROVIDER=hash\nAPI_URL=http://127.0.0.1:8004\n"
         "LLM_TIMEOUT=60\nLLM_RETRIES=1\nLLM_INTERVALO_SEG=6\n")
with destino.open("x", encoding="utf-8") as archivo:
    archivo.write(texto)
print("Configuracion local creada. No se mostraron credenciales.")
