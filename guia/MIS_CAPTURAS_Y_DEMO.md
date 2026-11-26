# Mis evidencias de la Actividad 4

Las capturas corresponden a acciones que realizo en la interfaz y en PowerShell. Conservo los PNG originales; no sustituyo resultados ni agrego ventanas dibujadas.

## Preparación

1. Ejecuto `guia/VALIDAR_A4.ps1` en PowerShell y espero a que termine.
2. Ejecuto `guia/ABRIR_A4.ps1`. Se abre `http://127.0.0.1:8504` en el navegador.
3. Creo una cuenta de prueba e inicio sesión. Uso una contraseña exclusiva para esta práctica.
4. Amplío la ventana del navegador y dejo visible la dirección local. Puedo usar un zoom de 80–90 % para que los resultados y la bitácora quepan.

## Capturas que tomo

Para cada captura uso **Win + Mayús + S**, selecciono **Ventana** o **Rectángulo** e incluyo la ventana y su barra de direcciones. Guardo los archivos originales en `evidencias/capturas/`.

| Archivo | Acción que realizo | Qué debe verse |
|---|---|---|
| `01_revision_usuarios.png` | Elijo `usuarios.py` y pulso **Revisar ejemplo**. | Resultado, validador, hallazgos con SEC y líneas, fuentes del corpus. |
| `02_limites_sin_hallazgos.png` | Elijo `limites.py` y pulso **Revisar ejemplo**. | Cero hallazgos, validador y aviso de alcance. |
| `03_confirmacion_pendiente.png` | Elijo `usuarios.py`, escribo `revision_cesar.json` y pulso **Revisar y preparar informe**. | Herramienta, ruta, huella, nombre y botones de decisión; todavía no se ha guardado. |
| `04_confirmacion_rechazada.png` | Pulso **Rechazar · no guardar**. | Mensaje de rechazo, `efecto: false`, bitácora y validador. |
| `05_fallo_herramienta.png` | Abro **Comprobar un fallo de herramienta** y pulso **Probar archivo inexistente**. | Error `FileNotFoundError`, paso `fallida`, sin revisión final. |
| `06_pruebas_powershell.png` | Tomo la ventana de PowerShell después de la validación. | Comando ejecutado y resultado real de pytest. Si quedó muy arriba, uso la instrucción de abajo para repetir solo las pruebas. |

No incluyo la contraseña, el archivo `.env` ni el token en las capturas.

Para ver el resultado de las pruebas en una ventana real sin volver a consultar Gemini:

```powershell
$a4 = 'C:\Users\cesar\OneDrive\Documentos\ChatGPT\Estudiar\actividad4_cesar'
Push-Location $a4
& "$a4\.venv\Scripts\python.exe" -m pytest tests -q
Pop-Location
```

Si una sesión caduca, inicio sesión otra vez y repito la acción. No edito el resultado para que parezca aprobado.

## Demo de dos minutos

Antes de grabar dejo la sesión iniciada. Puedo usar **Recortes → Grabar** para seleccionar la ventana del navegador y conservar también la dirección local. Las esperas de Gemini pueden alargar la toma: puedo grabar las acciones primero y recortar únicamente las esperas, indicándolo en el video. No cambio el orden ni los resultados.

| Tiempo aproximado | Lo que muestro | Guion orientativo |
|---|---|---|
| 0:00–0:15 | Interfaz y archivo seleccionado. | «Soy Cesar Eduardo Valdez Pinto. Mi Actividad 4 es un revisor de código con una API autenticada, un agente y herramientas controladas». |
| 0:15–0:45 | Revisión de `usuarios.py`, hallazgos y fuentes. | «El modelo propone llamar a Ruff. Mi ejecutor valida los argumentos y analiza el archivo sin ejecutarlo. Cada hallazgo muestra una regla SEC, una línea y su fuente». |
| 0:45–1:00 | `limites.py`, cero hallazgos y validador. | «Este es el caso de control. El validador comprueba las referencias y bloquea respuestas sin respaldo. Cero hallazgos solo aplica al alcance de las reglas configuradas». |
| 1:00–1:30 | Argumentos pendientes y rechazo de guardado. | «Guardar un informe requiere una confirmación independiente. Rechazo esta acción: no se crea el informe. La confirmación pertenece al usuario y solo puede utilizarse una vez». |
| 1:30–1:45 | Archivo inexistente y paso fallido. | «Cuando la herramienta falla, el servicio muestra el error y detiene la revisión; no inventa un análisis exitoso». |
| 1:45–2:00 | Bitácora y conclusión breve. | «Comparé las mismas cinco entradas antes y después de dos mejoras: ampliar las reglas de análisis y precisar el formato de respuesta y las fuentes. La bitácora conserva los resultados». |

Guardo la grabación como `evidencias/demo/Actividad4_Cesar.mp4`. La reviso antes de compartirla y agrego su enlace accesible en el documento final. El enlace debe poder abrirlo el profesor.
