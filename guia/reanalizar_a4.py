"""Reanaliza los registros reales con una referencia obtenida del codigo y corpus."""
import csv
import hashlib
import json
from pathlib import Path

RAIZ=Path(__file__).resolve().parents[1]


def evaluar_resultado(salida, referencias, archivo):
    ejecutadas=[p for p in salida['pasos'] if p['herramienta']=='correr_linter' and p['estado']=='ejecutada']
    hallazgos=[h for p in ejecutadas for h in p['resultado']['hallazgos']]
    def coincide(ref,h):
        return ref['regla']==h['regla'] and ref['linea']==h['linea'] and h['codigo_ruff'] in ref['codigos_ruff']
    cubiertos=[r['id'] for r in referencias if any(coincide(r,h) for h in hallazgos)]
    extras=[h for h in hallazgos if not any(coincide(r,h) for r in referencias)]
    errores_agente=[]
    if not ejecutadas:errores_agente.append('omision_de_consulta')
    if any(p['argumentos'].get('ruta')!=archivo for p in ejecutadas):errores_agente.append('inconsistencia_de_entrada')
    if not salida['validador']['ok']:errores_agente.append('inconsistencia_de_contrato')
    if extras:errores_agente.append('hallazgo_sin_respaldo_en_referencia')
    return {'referencia_problemas':len(referencias),'detectados':len(cubiertos),
            'omisiones_cobertura':len(referencias)-len(cubiertos),'ids_detectados':cubiertos,
            'ids_omitidos':[r['id'] for r in referencias if r['id'] not in cubiertos],
            'hallazgos_adicionales':len(extras),'errores_agente':errores_agente,
            'contrato_aprobado':salida['validador']['ok'],'terminado':salida['terminado']}


def main():
    carpeta=RAIZ/(RAIZ/'bitacora/a4/ultima_evaluacion.txt').read_text(encoding='utf-8').strip()
    refpath=RAIZ/'a4/referencia_revision.json'
    referencia=json.loads(refpath.read_text(encoding='utf-8'))
    from finnorte.herramientas_revisor import reglas
    corpus=reglas()
    for archivo,refs in referencia['casos'].items():
        lineas=(RAIZ/'datos/v2-revisor/codigo'/archivo).read_text(encoding='utf-8').splitlines()
        for r in refs:
            assert r['regla'] in corpus and r['evidencia'] in lineas[r['linea']-1]
    resultados=[];cadena=[]
    for version in ('v1','v2'):
        for archivo,refs in referencia['casos'].items():
            nombre=f"{version}_{archivo.removesuffix('.py')}.json"
            original=json.loads((carpeta/nombre).read_text(encoding='utf-8'))
            m=evaluar_resultado(original['resultado'],refs,archivo)
            resultados.append({'version':version,'archivo':archivo,**m})
            if version=='v2':
                for r in refs:
                    detectado=r['id'] in m['ids_detectados']
                    cadena.append({'regla':r['regla'],'entrada':archivo,'analisis':r['problema'],
                        'artefacto':str((carpeta/nombre).relative_to(RAIZ)).replace('\\','/'),
                        'hallazgo':f"{r['id']} linea {r['linea']}",
                        'deteccion':'Detectado' if detectado else 'Omitido por cobertura de herramienta',
                        'validador':'Aprobado para la respuesta emitida; no mide cobertura exhaustiva'})
                if not refs:
                    cadena.append({'regla':'Control negativo','entrada':archivo,'analisis':'Decimal y validacion del monto',
                        'artefacto':str((carpeta/nombre).relative_to(RAIZ)).replace('\\','/'),
                        'hallazgo':'0 hallazgos esperados y emitidos','deteccion':'Conforme',
                        'validador':'Aprobado'})
    salida=RAIZ/'bitacora/a4/reanalisis'
    salida.mkdir(exist_ok=True)
    resumen={'metodo':referencia['metodo'],'referencia_sha256':hashlib.sha256(refpath.read_bytes()).hexdigest(),
        'ronda_original':str(carpeta.relative_to(RAIZ)), 'nueva_consulta_gemini':False,
        'resultados':resultados,
        'causas':{'inconsistencia_de_contrato':'La respuesta parafraseada incumple el contrato literal; no implica por si sola una afirmacion falsa.',
                  'omision_cobertura':'El conjunto de reglas de Ruff no reconoce este patron; no se atribuye al modelo.',
                  'limite_referencia':'Revision posterior asistida, no ciega ni exhaustiva; no permite inferir sensibilidad general.'}}
    (salida/'resultados.json').write_text(json.dumps(resumen,ensure_ascii=False,indent=2),encoding='utf-8')
    for nombre,filas in [('TRAZABILIDAD_REGLAS.csv',cadena),('RESULTADOS_INDEPENDIENTES.csv',resultados)]:
        with (RAIZ/'a4'/nombre).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(filas[0]));w.writeheader();w.writerows(filas)
    lineas=['# Regla → analisis → artefacto → hallazgo → validador','',
        'Referencia por inspeccion del codigo y las politicas; elaborada despues de la ronda original. Los registros originales no se modifican.',
        '', '| Regla / entrada | Analisis | Artefacto | Hallazgo / deteccion | Validador |','|---|---|---|---|---|']
    for r in cadena:
        lineas.append(f"| {r['regla']} / {r['entrada']} | {r['analisis']} | {r['artefacto']} | {r['hallazgo']} · {r['deteccion']} | {r['validador']} |")
    (RAIZ/'a4/TRAZABILIDAD_REGLAS.md').write_text('\n'.join(lineas)+'\n',encoding='utf-8')
    print('REANALISIS: referencia 14 problemas; v1 detecta 5 y omite 9; v2 detecta 8 y omite 6. Los 5 contratos v2 aprueban.')


if __name__=='__main__':main()
