# Resultados de ejecucion

Suite actual: **109 aprobadas; 0 omitidas**.

| Version | Entrada | Hallazgos | Referencia Ruff v2 | Omisiones | Clasificacion |
|---|---|---:|---:|---:|---|
| v1 | usuarios.py | 3 | 3 | 0 | inconsistencia |
| v1 | limites.py | 0 | 0 | 0 | inconsistencia |
| v1 | tokens.py | 0 | 1 | 1 | inconsistencia, omision |
| v1 | reportes.py | 0 | 2 | 2 | inconsistencia, omision |
| v1 | transferencias.py | 2 | 2 | 0 | inconsistencia |
| v2 | usuarios.py | 3 | 3 | 0 | sin_error_en_alcance |
| v2 | limites.py | 0 | 0 | 0 | sin_error_en_alcance |
| v2 | tokens.py | 1 | 1 | 0 | sin_error_en_alcance |
| v2 | reportes.py | 2 | 2 | 0 | sin_error_en_alcance |
| v2 | transferencias.py | 2 | 2 | 0 | sin_error_en_alcance |

La clasificacion inconsistencia se refiere al contrato exacto del resumen y las fuentes: no demuestra por si sola que la respuesta contenga datos falsos.
Las omisiones se cuentan respecto de las reglas de Ruff del perfil final, no de todas las politicas SEC.
Esta ronda contiene una ejecucion por entrada y version; no demuestra estabilidad estadistica ni cobertura general.

Registros originales: `bitacora\a4\evaluacion_20261126T221709Z`.
