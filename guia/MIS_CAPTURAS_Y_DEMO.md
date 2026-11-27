# Mis capturas y la demo

Tomé seis capturas de la Actividad 4 desde el navegador y PowerShell. Las guardé en `evidencias/capturas/`; sus nombres y huellas están en `procedencia_capturas.json`.

## Acciones que mostré

| Captura | Lo que hice | Resultado |
|---|---|---|
| `01_revision_usuarios.png` | Seleccioné `usuarios.py` y pulsé **Revisar ejemplo**. | Consulté tres hallazgos SEC-06, sus líneas y las fuentes del corpus. |
| `02_limites_sin_hallazgos.png` | Revisé `limites.py`. | Obtuve cero hallazgos dentro de las reglas configuradas y consulté la bitácora. |
| `03_confirmacion_pendiente.png` | Revisé `usuarios.py` y preparé `revision_cesar.json`. | Vi la herramienta, la ruta, la huella y el nombre antes de decidir el guardado. |
| `04_confirmacion_rechazada.png` | Pulsé **Rechazar · no guardar**. | La respuesta indicó `rechazada` y `efecto: false`. |
| `05_fallo_herramienta.png` | Pulsé **Probar archivo inexistente**. | El servicio registró `FileNotFoundError` y detuvo la revisión. |
| `06_pruebas_powershell.png` | Capturé el resultado de pytest en PowerShell. | En esa ejecución aprobaron los 109 casos iniciales. Después de ampliar las pruebas, la suite actual aprobó 120. |

En la captura del fallo aparece el indicador de la primera interfaz. Después lo cambié por **Mensaje de fallo validado · El análisis no se completó** para distinguir la comprobación del mensaje de una revisión terminada.

## Cómo repito la demostración

Inicio los servicios con `guia/ABRIR_A4.ps1`, abro `http://127.0.0.1:8504` e inicio sesión con mi cuenta de prueba. En el modo **Agente** repito las acciones de la tabla. En **Mi variante** puedo enviar código al revisor de A3 y consultar sus fuentes.

Para ejecutar solamente las pruebas, sin volver a consultar Gemini:

```powershell
$a4 = 'C:\Users\cesar\OneDrive\Documentos\ChatGPT\Estudiar\actividad4_cesar'
Push-Location $a4
& "$a4\.venv\Scripts\python.exe" -m pytest tests -q
Pop-Location
```

## Grabación

Grabé la demostración desde el navegador y la guardé como `evidencias/demo/Actividad4_Cesar.mp4`. Muestro la revisión de `usuarios.py`, el caso `limites.py`, la preparación y el rechazo de un informe, el archivo inexistente y la bitácora.

La grabación dura 2 min 13 s. La conservé completa, sin narración ni rótulos añadidos. El archivo que comparto es una copia comprimida; conservé también el original. Su duración y huella están en `evidencias/demo/video_verificado.json`.
