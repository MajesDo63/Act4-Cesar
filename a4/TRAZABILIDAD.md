# Regla → analisis → artefacto → hallazgo → validador

Referencia por inspeccion del codigo y las politicas; elaborada despues de la ronda original. Los registros originales no se modifican.

| Regla / entrada | Analisis | Artefacto | Hallazgo / deteccion | Validador |
|---|---|---|---|---|
| SEC-06 / usuarios.py | Hash de contrasena con MD5 | bitacora/a4/evaluacion_20261126T221709Z/v2_usuarios.json | U01 linea 6 · Detectado | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-06 / usuarios.py | Codigo de un solo uso generado con random | bitacora/a4/evaluacion_20261126T221709Z/v2_usuarios.json | U02 linea 8 · Detectado | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-06 / usuarios.py | Verificacion mediante MD5 | bitacora/a4/evaluacion_20261126T221709Z/v2_usuarios.json | U03 linea 14 · Detectado | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-06 / usuarios.py | Comparacion de secreto con igualdad ordinaria | bitacora/a4/evaluacion_20261126T221709Z/v2_usuarios.json | U04 linea 14 · Omitido por cobertura de herramienta | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| Control negativo / limites.py | Decimal y validacion del monto | bitacora/a4/evaluacion_20261126T221709Z/v2_limites.json | 0 hallazgos esperados y emitidos · Conforme | Aprobado |
| SEC-09 / tokens.py | Carga YAML sin SafeLoader | bitacora/a4/evaluacion_20261126T221709Z/v2_tokens.json | T01 linea 6 · Detectado | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-06 / tokens.py | Comparacion de token sin compare_digest | bitacora/a4/evaluacion_20261126T221709Z/v2_tokens.json | T02 linea 10 · Omitido por cobertura de herramienta | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-09 / reportes.py | Deserializacion de entrada con pickle | bitacora/a4/evaluacion_20261126T221709Z/v2_reportes.json | R01 linea 9 · Detectado | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-09 / reportes.py | Comando shell con nombre de archivo externo | bitacora/a4/evaluacion_20261126T221709Z/v2_reportes.json | R02 linea 13 · Detectado | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-03 / reportes.py | Registro de CURP y CLABE sin enmascarar | bitacora/a4/evaluacion_20261126T221709Z/v2_reportes.json | R03 linea 17 · Omitido por cobertura de herramienta | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-01 / transferencias.py | Secreto de ejemplo escrito en codigo | bitacora/a4/evaluacion_20261126T221709Z/v2_transferencias.json | F01 linea 3 · Omitido por cobertura de herramienta | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-02 / transferencias.py | SELECT con interpolacion de identificador externo | bitacora/a4/evaluacion_20261126T221709Z/v2_transferencias.json | F02 linea 8 · Detectado | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-07 / transferencias.py | Monto de dinero convertido a float | bitacora/a4/evaluacion_20261126T221709Z/v2_transferencias.json | F03 linea 10 · Omitido por cobertura de herramienta | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-02 / transferencias.py | UPDATE con concatenacion de valores externos | bitacora/a4/evaluacion_20261126T221709Z/v2_transferencias.json | F04 linea 11 · Detectado | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
| SEC-03 / transferencias.py | CLABE completa enviada a print | bitacora/a4/evaluacion_20261126T221709Z/v2_transferencias.json | F05 linea 12 · Omitido por cobertura de herramienta | Aprobado para la respuesta emitida; no mide cobertura exhaustiva |
