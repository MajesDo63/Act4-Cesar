"""Comprobaciones locales antes de preparar el commit de entrega."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

RAIZ=Path(__file__).resolve().parents[1]
GIT=Path("C:/Program Files/Git/cmd/git.exe")
if not GIT.exists():GIT=Path("git")


def main():
    carpeta=RAIZ/(RAIZ/"bitacora/a4/ultima_evaluacion.txt").read_text(encoding="utf-8").strip()
    assert json.loads((carpeta/"estado.json").read_text(encoding="utf-8"))["estado"]=="completo", "La evaluacion esta incompleta"
    huellas=json.loads((carpeta/"huellas.json").read_text(encoding="utf-8"))
    for nombre,huella in huellas.items():
        if nombre not in ('app/cliente_api.py','app/interfaz_a4.py'):
            assert hashlib.sha256((RAIZ/nombre).read_bytes()).hexdigest()==huella, "Cambio el motor o los datos medidos: "+nombre
    pruebas=ET.parse(carpeta/"pytest.xml").findall(".//testcase")
    assert len(pruebas)==109 and all(x.find("failure") is None and x.find("error") is None and x.find("skipped") is None for x in pruebas)
    correccion_dir=RAIZ/(RAIZ/'bitacora/a4/ultima_correccion.txt').read_text(encoding='utf-8').strip()
    correccion=json.loads((correccion_dir/'validacion.json').read_text(encoding='utf-8'))
    assert correccion['estado']=='completo' and correccion['aprobadas']==120 and correccion['omitidas']==0
    for nombre,huella in correccion['huellas_actuales'].items():
        assert hashlib.sha256((RAIZ/nombre).read_bytes()).hexdigest()==huella,'Cambio una fuente de la correccion: '+nombre
    actuales=ET.parse(correccion_dir/'pytest.xml').findall('.//testcase')
    assert len(actuales)==120 and all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in actuales)
    informe=json.loads((RAIZ/"entrega/informe_estado.json").read_text(encoding="utf-8"))
    assert informe["borrador"] is False and informe["paginas_pdf"]==7, "Falta cerrar el informe final"
    pdf=RAIZ/"entrega"/informe["pdf"]
    assert hashlib.sha256(pdf.read_bytes()).hexdigest()==informe["sha256_pdf"]
    assert (RAIZ/"entrega"/informe["word"]).is_file()
    video=json.loads((RAIZ/"evidencias/demo/video_verificado.json").read_text(encoding="utf-8"))
    demo=RAIZ/"evidencias/demo/Actividad4_Cesar.mp4"
    assert demo.is_file() and demo.stat().st_size<95_000_000, "El video falta o es demasiado grande"
    assert 115<=video["duracion_final_s"]<=150, "Revisa la duracion de la demo"
    assert hashlib.sha256(demo.read_bytes()).hexdigest()==video["sha256_final"]
    for captura in json.loads((RAIZ/"evidencias/capturas/procedencia_capturas.json").read_text(encoding="utf-8")):
        assert hashlib.sha256((RAIZ/"evidencias/capturas"/captura["archivo"]).read_bytes()).hexdigest()==captura["sha256"]
    remoto=subprocess.check_output([str(GIT),"-C",str(RAIZ),"remote","get-url","origin"],text=True).strip()
    assert remoto.lower().removesuffix(".git")=="https://github.com/majesdo63/act4-cesar", "Destino de Git incorrecto"
    rutas=subprocess.check_output([str(GIT),"-C",str(RAIZ),"ls-files","--cached","--others","--exclude-standard","-z"]).decode("utf-8").split("\0")
    secretos=[]
    for linea in (RAIZ/".env").read_text(encoding="utf-8").splitlines():
        if "=" in linea:
            k,v=linea.split("=",1)
            if k in ("GEMINI_API_KEY","TOKEN_SECRET") and len(v.strip())>=20:secretos.append(v.strip().encode())
    assert len(secretos)==2, "No se pudo comprobar la exclusion de las dos credenciales locales"
    archivos=0
    for ruta in sorted(set(rutas)):
        if not ruta:continue
        p=RAIZ/ruta
        assert p.name!=".env" and ".venv" not in p.parts and p.suffix.lower() not in (".db",".sqlite",".sqlite3"), "Archivo privado en entrega: "+ruta
        assert not p.name.startswith("Borrador_"), "Un borrador quedo incluido"
        b=p.read_bytes()
        assert len(b)<100_000_000, "Archivo demasiado grande: "+ruta
        assert all(s not in b for s in secretos), "Credencial local detectada: "+ruta
        archivos+=1
    print(f"ENTREGA A4 COMPROBADA: {archivos} archivos; 120 pruebas actuales; Gemini original conservado; referencia y matriz; PDF 7 paginas; demo {video['duracion_final_s']:.2f} s; credenciales excluidas.")


if __name__=="__main__":
    try:main()
    except Exception as error:
        print("REVISION NECESARIA: "+str(error))
        raise SystemExit(1)
