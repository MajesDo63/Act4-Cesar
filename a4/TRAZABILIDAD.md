# Matriz de trazabilidad

| Requisito de A4 | Implementación | Prueba o registro |
|---|---|---|
| Herramienta propia `correr_linter(ruta)` | `herramientas_revisor.py`, Ruff sin ejecutar código. | `test_a4_linter_validador.py`; resultados de cinco entradas. |
| Catálogo y JSON Schema | `Herramienta`, esquemas cerrados para ruta y guardado. | Tipos, campos extra, ruta absoluta, traversal y opciones de comando. |
| Ejecutor propio | `herramientas.ejecutar_agente`. | Las tres pruebas oficiales y `test_a4_ejecutor.py`. |
| Confirmación obligatoria | `agente_servicio.iniciar` devuelve una acción pendiente. | False, None, entero y cadena no ejecutan efectos. |
| Rechazo sin efecto | `resolver(..., aprobar=False)`. | Prueba de directorio ausente; captura de rechazo desde la interfaz. |
| Mismos argumentos aprobados | Copia de argumentos y función ligada a la solicitud; revisión de la huella. | Mutación del retorno, cambio del archivo y confirmación concurrente. |
| Usuario, vigencia y un solo uso | Pendiente con propietario y TTL de 600 s. | Otro usuario, expiración y segunda confirmación. |
| Límite de pasos y repeticiones | Máximo configurable de 1 a 8; API usa 6. | Herramienta desconocida y acción repetida. |
| Fallo de herramienta | Archivo inexistente; estado fallida sin revisión final. | Prueba HTTP y captura de `FileNotFoundError`. |
| Validador tradicional | SEC y fuente existentes, línea, evidencia, huella y respuesta autorizada. | Manipulación de regla, línea, evidencia, fuente, resumen y huella. |
| `limites.py` sin hallazgos | Control negativo en cada versión. | Ruff real y API; captura de cero hallazgos. |
| Interfaz sobre API con token | Streamlit llama `/auth/*` y `/v1/agente*`. | Pruebas HTTP de token, entrada y confirmación; uso manual en navegador. |
| Fuentes, carga y errores visibles | Interfaz con spinner, fuentes, validador y tabla de pasos. | Capturas originales y demo. |
| Cinco entradas, dos rondas | usuarios, limites, tokens, reportes y transferencias. | Archivos v1/v2, prompts y respuestas en la evaluación. |
| Dos mejoras | Ampliación de reglas; contrato explícito del resumen y fuentes. | Mismos cinco archivos, métricas y huellas. |
| Clasificación de errores | Alucinación, omisión, inconsistencia y genérico dentro del alcance definido. | `metricas` por entrada; lectura crítica en el informe. |
| Bitácora de IA | `ai_log.md`. | Decisiones aceptadas, modificadas y rechazadas; registros reales de Gemini. |
| Entrega | PDF de 5–7 páginas, repositorio con etiqueta `a4-MajesDo63` y demo de dos minutos. | Se comprueban al cerrar la entrega; crear los archivos no equivale a verificar la publicación. |

La referencia automática de la comparación es Ruff con el perfil v2. No se presenta como un inventario exhaustivo de todas las vulnerabilidades del corpus. Los riesgos fuera de esas reglas permanecen como limitaciones de cobertura.
