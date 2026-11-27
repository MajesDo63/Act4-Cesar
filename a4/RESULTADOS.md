# Resultados y causas de la evaluacion

Suite corregida: **120 aprobadas; 0 omitidas**. La captura original corresponde a la suite previa de 109 casos.

La referencia por inspeccion del codigo y corpus documenta 14 problemas. Se elaboro despues de la ronda de Gemini; no es ciega ni exhaustiva. No se usa la salida de Ruff para definir los problemas esperados.

| Version | Entrada | Problemas de referencia | Detectados | Omitidos por cobertura | Contrato de respuesta |
|---|---|---:|---:|---:|---|
| v1 | usuarios.py | 4 | 3 | 1 | Bloqueado |
| v1 | limites.py | 0 | 0 | 0 | Bloqueado |
| v1 | tokens.py | 2 | 0 | 2 | Bloqueado |
| v1 | reportes.py | 3 | 0 | 3 | Bloqueado |
| v1 | transferencias.py | 5 | 2 | 3 | Bloqueado |
| v2 | usuarios.py | 4 | 3 | 1 | Aprobado |
| v2 | limites.py | 0 | 0 | 0 | Aprobado |
| v2 | tokens.py | 2 | 1 | 1 | Aprobado |
| v2 | reportes.py | 3 | 2 | 1 | Aprobado |
| v2 | transferencias.py | 5 | 2 | 3 | Aprobado |

## Separacion de causas

- Herramienta: v1 detecta 5 de los 14 problemas anotados; v2 detecta 8. Las seis omisiones restantes de v2 son dos comparaciones de secretos, dos registros sensibles, la llave sintetica escrita en codigo y el uso de float para dinero.
- Agente: las cinco respuestas v1 incumplieron el contrato literal; las cinco v2 lo cumplieron tras precisar las instrucciones. Esto mide conformidad del formato y las fuentes; no demuestra razonamiento general ni convierte cada parafrasis v1 en falsa.
- No se observaron hallazgos adicionales ni respuestas genericas en estos diez registros. Las pruebas negativas que inyectan datos sin respaldo comprueban el bloqueo; no se cuentan como alucinaciones reales de Gemini.
- Las dos mejoras historicas fueron ampliar el perfil de Ruff y precisar el contrato de respuesta. La correccion posterior unifica los modos de interfaz, aclara el fallo y agrega la referencia y la matriz solicitadas.

## Evidencias

Las diez respuestas originales de Gemini se conservan en `bitacora/a4/evaluacion_20261126T221709Z/`. Sus metricas originales y `RESULTADOS.csv` comparan con el perfil final de Ruff y se mantienen como registro historico, no como cobertura completa de las politicas SEC.
El reanalisis usa `referencia_revision.json`, `RESULTADOS_INDEPENDIENTES.csv` y `bitacora/a4/reanalisis/resultados.json`. La matriz `TRAZABILIDAD.md` liga regla, analisis, artefacto, hallazgo y validador.
La validacion actual y las huellas de la interfaz corregida estan en `bitacora\a4\correccion_20261127T002609Z`. El motor, la API, el corpus y las cinco entradas originales mantienen sus bytes. No se realizaron consultas nuevas a Gemini.
