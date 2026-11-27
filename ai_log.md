# Registro de uso de IA · Actividad 4

**Alumno:** Cesar Eduardo Valdez Pinto · **Usuario:** MajesDo63

Utilicé ChatGPT para preparar la implementación, las pruebas y la documentación de A4. Utilicé Gemini como modelo del agente durante la comparación y la interfaz. Distingo la asistencia para desarrollar el proyecto de las respuestas del modelo que mi aplicación debe controlar.

| Solicitud o propuesta | Decisión | Aplicación y verificación |
|---|---|---|
| Continuar desde la API autenticada de A3 en un repositorio independiente. | Aceptada. | Conservé la base de autenticación e incorporé el agente propio. La procedencia se registra con el commit y las huellas. |
| Usar Ruff para analizar código Python sin ejecutarlo. | Aceptada con controles. | Catálogo de ejemplos, entrada por stdin, argumentos fijos, `shell=False`, tiempo y tamaño máximos. |
| Permitir rutas libres o ejecutar comandos propuestos por el modelo. | Rechazada como alternativa de diseño. | La herramienta no admite rutas arbitrarias, opciones adicionales ni ejecución del código revisado. |
| Resumir libremente la salida de las herramientas. | Modificada. | La versión inicial permite observar la incompatibilidad con el validador. En v2 solicité copiar el resumen autorizado y las fuentes exactas. Las respuestas reales se conservan en la evaluación. |
| Limitar el análisis a criptografía y SQL. | Modificada. | En v2 añadí reglas para pickle, YAML, eval y `shell=True`. Comparé las mismas cinco entradas. |
| Guardar el informe cuando lo sugiera el modelo. | Modificada. | Separé propuesta y confirmación. El guardado exige un análisis previo y la misma huella; solo se ejecuta tras aprobar los argumentos exactos. |
| Preparar evidencias visuales a partir de registros. | Rechazada para esta entrega. | Las capturas y la grabación se toman manualmente desde las ventanas de la aplicación y PowerShell. Los JSON y XML se conservan como registros, no como sustitutos de capturas. |

## Comprobaciones y cambios

- Las tres pruebas oficiales de A4 se conservaron como `tests/test_a4_oficial.py`. Una pieza sin implementar se considera un fallo; no se oculta como prueba omitida.
- La primera ronda local detectó una expectativa incorrecta: se esperaba S608 en `cuentas_api.py`, que contiene un problema de autorización y no una consulta SQL. Corregí la expectativa y usé `transferencias.py` como caso SQL. No atribuí a Ruff una cobertura que no tiene.
- El último paso del instalador inicial falló por el paso de comillas entre PowerShell y Python. Lo sustituí por `guia/comprobar_entorno.py`; las dependencias instaladas se conservaron.
- Las pruebas distinguen proveedor `fake` para contratos y seguridad de las llamadas reales a Gemini para la comparación del agente.
- Las respuestas íntegras de Gemini, sus prompts, metadatos y resultados por caso se guardan en `bitacora/a4/evaluacion_*/`. La comparación conserva fallos y no reemplaza respuestas reales por resultados simulados.

## Qué reviso antes de entregar

Compruebo el resultado de las pruebas, las diferencias entre v1 y v2, mis capturas, la demo y el destino del repositorio. Mantengo explícitas las limitaciones de las reglas estáticas y del validador. Las credenciales y las bases de datos locales no forman parte de la entrega.

## Capturas y grabación

Tomé las seis capturas originales en mi computadora: revisión de usuarios.py, caso limites.py, confirmación pendiente, rechazo, archivo inexistente y pytest. Se conservaron sus bytes y huellas. No incluí la imagen del acceso con la contraseña visible.

Grabé la interfaz sin narración. Elegí utilizar mi propia grabación, sin rótulos ni presentación añadidos. Conservé el archivo original y mostré los pasos directamente en la aplicación.

## Corrección de interfaz, trazabilidad y evaluación

Integré Mi variante y Agente en `app/cliente_api.py`: el primer modo utiliza el endpoint de la A3 y el segundo las herramientas de la A4. El mensaje de control de un fallo se distingue de una revisión aprobada. Añadí pruebas de interacción de Streamlit con HTTP simulado.

Con asistencia de ChatGPT revisé el código y el corpus para anotar 14 problemas, independientemente de ejecutar Ruff. La referencia se elaboró después de la ronda original y no es ciega ni exhaustiva. Reanalicé las diez respuestas reales guardadas: el perfil final detecta ocho problemas y deja seis sin cubrir. Separé estas omisiones de las inconsistencias del contrato de respuesta y construí la matriz regla → análisis → artefacto → hallazgo → validador. La grabación y las seis capturas originales se conservaron.
