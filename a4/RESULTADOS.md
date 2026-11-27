# Resultados de mi evaluación

La suite final aprobó **120 pruebas y no omitió ninguna**. Tomé la captura de PowerShell durante la ejecución inicial de 109 casos.

Revisé el código y las políticas del corpus para anotar 14 problemas. Preparé esta referencia después de la ronda de Gemini, sin basarme en la salida de Ruff. Por ese orden de trabajo, la comparación no es ciega; la lista tampoco cubre todos los posibles riesgos.

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

## Qué cambió entre las versiones

- Al ampliar el perfil de Ruff pasé de 5 a 8 problemas detectados. Quedaron seis sin cubrir: dos comparaciones de secretos, dos registros sensibles, una llave de ejemplo escrita en código y un monto convertido a float.
- Ajusté las instrucciones del agente para conservar el resumen y las fuentes autorizadas. Las cinco respuestas v1 incumplieron ese contrato y las cinco v2 lo cumplieron. Evalué esa coincidencia por separado de la cobertura de seguridad; una paráfrasis puede fallar el contrato aunque su contenido sea correcto.
- En las diez respuestas no observé hallazgos adicionales ni respuestas genéricas. Con las pruebas negativas comprobé el bloqueo de información sin respaldo; esas entradas manipuladas pertenecen a las pruebas, no a los resultados observados de Gemini.
- Después integré los dos modos de la interfaz, aclaré el mensaje de fallo y añadí la referencia y la matriz de trazabilidad.

## Evidencias

Guardé las diez respuestas originales de Gemini en `bitacora/a4/evaluacion_20261126T221709Z/`. Conservé sus métricas originales y `RESULTADOS.csv` como registro de la comparación con el perfil final de Ruff. Para medir los problemas de las políticas SEC utilicé la referencia anotada.
Para el reanálisis utilicé `referencia_revision.json`, `RESULTADOS_INDEPENDIENTES.csv` y `bitacora/a4/reanalisis/resultados.json`. En `TRAZABILIDAD.md` relacioné cada regla con su análisis, artefacto, hallazgo y validador.
Registré la validación final y las huellas de la interfaz en `bitacora\a4\correccion_20261127T002609Z`. Comprobé que el motor, la API, el corpus y las cinco entradas conservaran sus huellas. Para esta revisión reutilicé las respuestas guardadas de Gemini.
