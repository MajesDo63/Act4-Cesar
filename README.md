# Actividad 4 · Cesar Eduardo Valdez Pinto

Implementé un agente para revisar ejemplos Python de FinNorte con Ruff y una interfaz sobre la API autenticada de la Actividad 3. El modelo propone acciones; el ejecutor comprueba el catálogo y los argumentos antes de llamar a una herramienta. El código analizado nunca se ejecuta.

Repositorio de esta actividad: https://github.com/MajesDo63/Act4-Cesar

## Qué contiene

| Parte | Archivo principal | Función |
|---|---|---|
| Ejecutor propio | `src/finnorte/herramientas.py` | Protocolo JSON, validación, máximo de pasos y detección de repeticiones. |
| Herramientas | `src/finnorte/herramientas_revisor.py` | `correr_linter` y `guardar_informe`. |
| Validador | `src/finnorte/validador_a4.py` | SEC, fuente, línea, evidencia, huella y respuesta respaldada. |
| Confirmaciones | `src/finnorte/agente_servicio.py` | Acción exacta, usuario, vigencia, rechazo y un solo uso. |
| API | `api/producto.py` | Token de A3, errores `problem+json` y endpoints del agente. |
| Interfaz | `app/interfaz_a4.py` | Acceso, revisión, fuentes, validador, bitácora y decisión. |
| Evaluación | `guia/evaluar_a4.py` | Las mismas cinco entradas en v1 y v2; conserva prompts y respuestas reales. |
| Evidencias | `bitacora/a4/` y `evidencias/` | Registros de ejecución y archivos originales de las capturas y demo. |

La base proviene de mi entrega A3 en `MajesDo63/Act3`, commit `e80daefcce32d31af562c7ac5c65f998d409009f`. Los cambios de A4 están separados de esa entrega. Las funciones del caso guía que permanecen en la base son material de referencia; el endpoint `/v1/agente` usa mi ejecutor y mis herramientas, no el ejecutor de referencia.

## Ejecutar en Windows

En mi computadora el entorno se encuentra en `.venv`. Para instalar desde otra copia, creo un entorno Python 3.12 o superior e instalo el proyecto:

```powershell
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.\.venv\Scripts\python.exe' -m pip install -e .
```

Copio `.env.example` como `.env`, configuro mi llave de Gemini y un `TOKEN_SECRET` aleatorio de al menos 32 caracteres. Las credenciales permanecen en mi equipo y están excluidas de Git. El proyecto no necesita AWS.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File '.\guia\VALIDAR_A4.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File '.\guia\ABRIR_A4.ps1'
```

La interfaz se abre en **http://127.0.0.1:8504** y la documentación de la API en **http://127.0.0.1:8004/docs**. Creo una cuenta de prueba e inicio sesión en la interfaz. El token se conserva en la sesión y no se muestra.

Si el proveedor interrumpe la evaluación, conservo los resultados terminados y reanudo con:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File '.\guia\VALIDAR_A4.ps1' -Continuar
```

La reanudación verifica las huellas del código. Si cambio el código, inicio una ronda nueva.

Para ejecutar solo las pruebas, sin consultar Gemini:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests -q
```

Para cerrar los servicios locales uso `guia/CERRAR_A4.ps1`.

## Alcance y límites

Ruff se invoca con argumentos fijos, `shell=False`, `--isolated`, sin caché ni `--fix`, con el contenido por stdin y un límite de diez segundos. Solo se admiten los nombres del catálogo: no hay rutas libres ni lectura de `.env` mediante el agente.

La versión final utiliza S311, S324, S608, S301, S307, S602 y S506. Las relacioné con SEC-02, SEC-06 y SEC-09 del corpus. No cubren todas las políticas SEC: por ejemplo, `cuentas_api.py` requiere una revisión de autorización que estas reglas no realizan. Cero hallazgos significa cero coincidencias dentro de este alcance.

El validador comprueba referencias y exige que la respuesta coincida con el resumen autorizado por la herramienta. No es una demostración semántica de seguridad ni sustituye una auditoría. Un archivo inexistente produce un paso fallido y detiene la revisión.

`guardar_informe` es sensible: requiere que esa misma solicitud haya analizado la misma ruta y huella. Antes de guardar se verifica otra vez la huella. La confirmación dura diez minutos, pertenece al usuario y se consume una sola vez. Rechazarla no crea el informe ni su directorio. Aprobarla permite crear un archivo nuevo; nunca reemplaza uno existente.

## Capturas y demo

Sigo la secuencia de `guia/MIS_CAPTURAS_Y_DEMO.md`. Las capturas se toman desde la ventana real del navegador y PowerShell. La guía distingue las ejecuciones automáticas de las acciones que realizo en la interfaz.

Las fuentes y decisiones sobre el uso de asistentes se registran en `ai_log.md`.

## Entregables

- [Informe PDF, siete páginas](entrega/Actividad4_Cesar_Informe.pdf).
- [Documento editable](entrega/Actividad4_Cesar_Informe.docx).
- [Demo de la actividad · 2 min 13 s](https://github.com/MajesDo63/Act4-Cesar/raw/refs/tags/a4-MajesDo63/evidencias/demo/Actividad4_Cesar.mp4).
- [Resultados de la comparación](a4/RESULTADOS.md) y [matriz de trazabilidad](a4/TRAZABILIDAD.md).

La demo es mi grabación de la interfaz, sin narración, rótulos ni presentación añadidos. Conservé el archivo original en su ubicación local. La duración y la huella de la copia de entrega se registran en `evidencias/demo/video_verificado.json`.
