import json
from pathlib import Path

from guia.reanalizar_a4 import evaluar_resultado

RAIZ=Path(__file__).resolve().parents[1]
REF=json.loads((RAIZ/'a4/referencia_revision.json').read_text(encoding='utf-8'))['casos']
RONDA=RAIZ/'bitacora/a4/evaluacion_20261126T221709Z'


def resultado(version,archivo):
    return json.loads((RONDA/f"{version}_{archivo.removesuffix('.py')}.json").read_text(encoding='utf-8'))['resultado']


def test_referencia_distingue_dos_riesgos_en_misma_regla_y_linea():
    m=evaluar_resultado(resultado('v2','usuarios.py'),REF['usuarios.py'],'usuarios.py')
    assert m['detectados']==3 and m['ids_omitidos']==['U04']
    assert m['contrato_aprobado'] and m['omisiones_cobertura']==1


def test_validador_aprobado_no_equivale_a_cobertura_total():
    m=evaluar_resultado(resultado('v2','transferencias.py'),REF['transferencias.py'],'transferencias.py')
    assert m['contrato_aprobado'] and m['detectados']==2 and m['omisiones_cobertura']==3


def test_configuracion_linter_no_se_atribuye_como_alucinacion_del_modelo():
    m=evaluar_resultado(resultado('v1','reportes.py'),REF['reportes.py'],'reportes.py')
    assert m['omisiones_cobertura']==3 and m['hallazgos_adicionales']==0
    assert m['errores_agente']==['inconsistencia_de_contrato']


def test_control_negativo_con_cero_problemas():
    m=evaluar_resultado(resultado('v2','limites.py'),REF['limites.py'],'limites.py')
    assert m['detectados']==m['omisiones_cobertura']==0 and m['contrato_aprobado']


def test_sin_herramienta_es_omision_de_consulta():
    salida={'pasos':[],'terminado':False,'validador':{'ok':False}}
    m=evaluar_resultado(salida,REF['tokens.py'],'tokens.py')
    assert 'omision_de_consulta' in m['errores_agente'] and m['omisiones_cobertura']==2


def test_hallazgo_ajeno_a_referencia_se_identifica():
    salida=resultado('v2','limites.py')
    salida['pasos'][0]['resultado']['hallazgos'].append({'regla':'SEC-99','linea':1,'codigo_ruff':'S999'})
    m=evaluar_resultado(salida,[], 'limites.py')
    assert m['hallazgos_adicionales']==1 and 'hallazgo_sin_respaldo_en_referencia' in m['errores_agente']
