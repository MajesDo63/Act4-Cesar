$ErrorActionPreference='Stop'
$raizA4=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pythonA4=Join-Path $raizA4 '.venv\Scripts\python.exe'
& $pythonA4 -m pip install imageio-ffmpeg==0.8.1
if($LASTEXITCODE -ne 0){throw 'No se pudo instalar la herramienta de video.'}
$videoOrigenA4=Join-Path ([Environment]::GetFolderPath('MyVideos')) 'act4_Cesar.mp4'
if(-not (Test-Path -LiteralPath $videoOrigenA4)){throw 'No se encontro la grabacion en Videos.'}
& $pythonA4 (Join-Path $PSScriptRoot 'inspeccionar_video_a4.py') $videoOrigenA4
if($LASTEXITCODE -ne 0){throw 'No se pudo leer la grabacion.'}
Write-Output 'VIDEO LISTO PARA REVISAR. La grabacion original sigue intacta.'
