"""Valida la interfaz corregida y registra la reutilizacion trazable de la ronda Gemini."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ));sys.path.insert(0,str(RAIZ/'src'))
os.environ['LLM_PROVIDER']='fake';os.environ['EMB_PROVIDER']='hash'
from guia.reanalizar_a4 import main as reanalizar


def huellas_actuales():
    archivos=[]
    for directorio in ('src','api','app','tests','corpus','datos'):
        archivos.extend(p for p in (RAIZ/directorio).rglob('*') if p.is_file() and
                        '__pycache__' not in p.parts and p.suffix in ('.py','.md','.json','.txt'))
    archivos.extend(RAIZ/n for n in ('requirements.txt','pyproject.toml','a4/referencia_revision.json','guia/reanalizar_a4.py'))
    return {str(p.relative_to(RAIZ)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(archivos)}


def main():
    anterior=RAIZ/(RAIZ/'bitacora/a4/ultima_evaluacion.txt').read_text(encoding='utf-8').strip()
    originales=json.loads((anterior/'huellas.json').read_text(encoding='utf-8'))
    cambios=[n for n,h in originales.items() if hashlib.sha256((RAIZ/n).read_bytes()).hexdigest()!=h]
    assert set(cambios)<={'app/cliente_api.py','app/interfaz_a4.py'},'Cambio el motor o las entradas de la ronda original'
    salida=RAIZ/'bitacora/a4'/('correccion_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    salida.mkdir()
    (RAIZ/'bitacora/a4/ultima_correccion.txt').write_text(str(salida.relative_to(RAIZ)),encoding='utf-8')
    huellas=huellas_actuales()
    entorno=dict(os.environ,LLM_PROVIDER='fake',EMB_PROVIDER='hash',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                 AUTH_DB=str(salida/'auth_pruebas.db'),FINNORTE_DIR_TRAZAS=str(salida))
    comando=[sys.executable,'-m','pytest','tests','-q','--junitxml='+str(salida/'pytest.xml')]
    print('Validando la suite completa y los dos modos de la interfaz. No se consulta Gemini.',flush=True)
    p=subprocess.run(comando,cwd=RAIZ,env=entorno,capture_output=True,timeout=240)
    texto=p.stdout.decode('utf-8',errors='replace')+p.stderr.decode('utf-8',errors='replace')
    (salida/'pytest.txt').write_text(texto,encoding='utf-8');print(texto,flush=True)
    if p.returncode:raise RuntimeError('Las pruebas necesitan revision; consulta pytest.txt')
    casos=ET.parse(salida/'pytest.xml').findall('.//testcase')
    assert not any(c.find('skipped') is not None or c.find('failure') is not None or c.find('error') is not None for c in casos)
    reanalizar()
    assert huellas_actuales()==huellas,'Cambio el codigo durante la validacion'
    registro={'estado':'completo','fecha_utc':datetime.now(timezone.utc).isoformat(),'aprobadas':len(casos),
              'omitidas':0,'comando':comando,'interprete':sys.executable,'directorio':str(RAIZ),
              'ronda_gemini_original':str(anterior.relative_to(RAIZ)),'motor_y_entradas_originales_intactos':True,
              'cambios_en_fuentes_preexistentes':cambios,'nuevas_consultas_gemini':False,'huellas_actuales':huellas}
    (salida/'validacion.json').write_text(json.dumps(registro,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"CORRECCION A4 VALIDADA: {len(casos)} pruebas aprobadas; Gemini original conservado; matriz y referencia comprobadas.",flush=True)
    print('EVIDENCIAS: '+str(salida),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as e:
        print('VALIDACION INTERRUMPIDA: '+str(e),flush=True)
        raise SystemExit(1)
