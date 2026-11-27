# Registro de uso de IA — Actividad 4

**Cesar Eduardo Valdez Pinto — MajesDo63**

Utilicé ChatGPT como apoyo para preparar el código, las pruebas y la documentación. Integré Gemini como modelo del agente y conservé los prompts y sus respuestas durante la evaluación. En esta bitácora registro las decisiones del proyecto.

| Propuesta o decisión de diseño | Decisión | Cómo quedó en el proyecto |
|---|---|---|
| Continuar desde mi API autenticada de A3. | Aceptada. | Conservé la autenticación e incorporé el agente en un repositorio independiente. Registré el commit de origen y las huellas. |
| Analizar Python con Ruff. | Aceptada con controles. | Limité los ejemplos al catálogo, envié el contenido por stdin y fijé los argumentos, el tiempo y el tamaño máximo. |
| Admitir rutas libres o comandos elegidos por el modelo. | Rechazada. | Elegí nombres del catálogo y argumentos cerrados. El agente analiza el código sin ejecutarlo. |
| Permitir un resumen libre de los resultados. | Modificada. | En v1 observé respuestas incompatibles con el validador. En v2 precisé la copia del resumen autorizado y de sus fuentes. |
| Revisar únicamente criptografía y SQL. | Modificada. | Amplié el perfil con reglas para pickle, YAML, eval y `shell=True`. Comparé las mismas cinco entradas. |
| Guardar el informe al recibir la propuesta del modelo. | Modificada. | Separé la propuesta de la confirmación. Exigí un análisis previo, la misma huella y la aprobación de los argumentos exactos. |
| Usar imágenes generadas a partir de los registros como capturas. | Rechazada para la entrega. | Tomé las capturas y grabé la demo en mi computadora. Conservé aparte los JSON y XML de las ejecuciones. |

## Ajustes durante el desarrollo

Conservé las tres pruebas oficiales en `tests/test_a4_oficial.py` y añadí casos del ejecutor, las herramientas, el validador y las confirmaciones. En la primera ronda corregí una expectativa de prueba: `cuentas_api.py` tiene un problema de autorización, por lo que usé `transferencias.py` para comprobar S608 y la construcción de SQL.

También corregí el paso de comillas entre PowerShell y Python en el instalador. Pasé la comprobación del entorno a `guia/comprobar_entorno.py` y conservé las dependencias ya instaladas.

Utilicé `fake` para comprobar contratos y controles de seguridad, y Gemini para comparar el comportamiento del agente. Guardé sus diez respuestas completas, prompts y metadatos en `bitacora/a4/evaluacion_20261126T221709Z/`.

## Revisión de resultados

Con apoyo de ChatGPT revisé los ejemplos y las políticas SEC para anotar 14 problemas sin tomar la salida de Ruff como referencia. Preparé esta lista después de la ronda original; por eso la comparación no es ciega ni exhaustiva.

Reanalicé las respuestas guardadas: v1 detectó cinco problemas y v2 detectó ocho. Separé las seis omisiones de cobertura de v2 de los errores del contrato de respuesta. Después armé la matriz regla → análisis → artefacto → hallazgo → validador.

Integré **Mi variante** y **Agente** en `app/cliente_api.py`, distinguí el mensaje de fallo de una revisión aprobada y añadí pruebas de interacción de Streamlit. La suite final aprobó **120 pruebas, sin casos omitidos**.

## Capturas, video y documentación

Tomé las seis capturas desde mi computadora y grabé la interfaz. Conservé los archivos originales y sus huellas. Elegí compartir el video completo, sin narración ni rótulos añadidos, mediante una copia comprimida.

Para la versión final del informe utilicé apoyo de ChatGPT en la redacción y la organización. Mantuve los resultados medidos, las fuentes y las limitaciones del análisis. Las credenciales y las bases de datos locales quedaron fuera de la entrega.
