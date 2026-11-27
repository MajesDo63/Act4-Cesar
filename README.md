# Actividad 4 — Cesar Eduardo Valdez Pinto

Desarrollé un agente para revisar ejemplos de código Python de FinNorte con Ruff. Retomé la API autenticada de mi Actividad 3 e integré dos modos en la interfaz: **Mi variante** y **Agente**. El modelo propone las acciones y el ejecutor comprueba los argumentos antes de usar cada herramienta.

Repositorio: https://github.com/MajesDo63/Act4-Cesar

## Organización del proyecto

| Parte | Archivo principal | Función |
|---|---|---|
| Ejecutor | `src/finnorte/herramientas.py` | Valida el JSON, limita los pasos y detecta acciones repetidas. |
| Herramientas | `src/finnorte/herramientas_revisor.py` | Analiza con `correr_linter` y permite `guardar_informe`. |
| Validador | `src/finnorte/validador_a4.py` | Comprueba reglas SEC, fuentes, líneas, evidencias y huellas. |
| Confirmaciones | `src/finnorte/agente_servicio.py` | Controla los argumentos, el usuario, la vigencia y el uso único. |
| API | `api/producto.py` | Autentica las solicitudes y expone los endpoints. |
| Interfaz | `app/cliente_api.py` | Presenta los dos modos, los resultados y la decisión de guardado. |
| Evaluación | `guia/evaluar_a4.py` | Compara las mismas cinco entradas con v1 y v2. |
| Evidencias | `bitacora/a4/` y `evidencias/` | Conserva las ejecuciones, las capturas y la demo. |

Partí de mi entrega A3 en `MajesDo63/Act3`, commit `e80daefcce32d31af562c7ac5c65f998d409009f`. Implementé el agente de A4 en este repositorio; `/v1/agente` utiliza mi ejecutor y mis herramientas. El código del caso guía queda como referencia del curso.

## Instalación y ejecución

En Windows preparo el entorno con Python 3.12 o superior:

```powershell
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.\.venv\Scripts\python.exe' -m pip install -e .
```

Copio `.env.example` como `.env` y configuro mi llave de Gemini y un `TOKEN_SECRET` aleatorio de al menos 32 caracteres. Guardo las credenciales únicamente en mi equipo. Para esta actividad utilizo Gemini y servicios locales; no necesito AWS.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File '.\guia\VALIDAR_A4.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File '.\guia\ABRIR_A4.ps1'
```

Accedo a la interfaz en **http://127.0.0.1:8504** y a Swagger en **http://127.0.0.1:8004/docs**. Creo una cuenta de prueba e inicio sesión. El token permanece en la sesión.

En **Mi variante**, envío código a `/v1/revisor` y consulto el artefacto, las fuentes y la validación del flujo de A3. En **Agente**, selecciono un ejemplo para `/v1/agente` y consulto los hallazgos, las herramientas y la confirmación del informe. `app/interfaz_a4.py` también abre esta misma interfaz.

Si Gemini interrumpe una ronda, reanudo los casos pendientes con:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File '.\guia\VALIDAR_A4.ps1' -Continuar
```

La reanudación verifica las huellas del código. Cuando modifico el código evaluado, inicio una ronda nueva.

## Pruebas y resultados

La suite actual tiene **120 pruebas aprobadas y ninguna omitida**. Para ejecutarla sin consultar Gemini uso:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests -q
```

Para comprobar los dos modos de la interfaz y repetir el análisis de los registros guardados:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File '.\guia\VALIDAR_CORRECCION_A4.ps1'
```

Conservé las diez respuestas de Gemini de la ronda original y comprobé las huellas del motor, la API, los prompts, el corpus y las entradas. Después revisé el código y las políticas SEC para anotar 14 problemas: v1 detectó 5 y v2 detectó 8. La referencia se elaboró después de la ronda, por lo que esta comparación no es ciega. En `a4/TRAZABILIDAD.md` relaciono cada regla con su análisis, artefacto, hallazgo y resultado del validador.

## Controles y alcance

Configuré Ruff con argumentos fijos, `shell=False`, `--isolated`, sin caché ni `--fix`, con entrada por stdin y un tiempo máximo de diez segundos. El agente acepta únicamente los nombres del catálogo y analiza el contenido sin ejecutarlo.

Relacioné S311 y S324 con SEC-06, S608 con SEC-02, y S301, S307, S602 y S506 con SEC-09. Estas reglas cubren los patrones descritos en `a4/RESULTADOS.md`. Quedan seis problemas de la referencia fuera de su cobertura; interpreto un resultado de cero hallazgos dentro de ese alcance.

El validador comprueba las referencias y la coincidencia con el resumen autorizado. Así controlo la integridad de la respuesta, aunque la herramienta puede omitir riesgos que no cubren sus reglas. Cuando falla una herramienta, el servicio registra el error y detiene la revisión.

Para guardar un informe exijo un análisis previo de la misma ruta y huella. La confirmación pertenece al usuario, dura diez minutos y tiene un solo uso. Al rechazarla no se crea el informe ni su directorio. Al aprobarla vuelvo a comprobar la huella y creo un archivo nuevo, sin reemplazar archivos existentes.

Para cerrar los servicios locales ejecuto `guia/CERRAR_A4.ps1`.

## Entrega

- [Informe PDF, siete páginas](entrega/Actividad4_Cesar_Informe.pdf).
- [Documento editable](entrega/Actividad4_Cesar_Informe.docx).
- [Demo, 2 min 13 s](https://github.com/MajesDo63/Act4-Cesar/raw/refs/tags/a4-MajesDo63/evidencias/demo/Actividad4_Cesar.mp4).
- [Resultados](a4/RESULTADOS.md) y [matriz de trazabilidad](a4/TRAZABILIDAD.md).
- [Registro de uso de IA](ai_log.md).

Tomé seis capturas en mi computadora y grabé la demostración desde la interfaz. En `guia/MIS_CAPTURAS_Y_DEMO.md` describo las acciones que mostré. Conservé el video completo, sin narración ni rótulos añadidos, y preparé una copia comprimida para compartirlo.
