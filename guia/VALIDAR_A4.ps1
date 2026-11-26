param([switch]$Continuar)
$ErrorActionPreference='Stop'
$raizA4=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pythonA4=Join-Path $raizA4 '.venv\Scripts\python.exe'
& $pythonA4 (Join-Path $PSScriptRoot 'comprobar_entorno.py')
if($LASTEXITCODE -ne 0){throw 'No se pudo comprobar el entorno.'}
$argumentosA4=@((Join-Path $PSScriptRoot 'evaluar_a4.py'))
if($Continuar){$argumentosA4+='--reanudar'}
& $pythonA4 @argumentosA4
if($LASTEXITCODE -ne 0){throw 'La evaluacion no termino. Conserva el mensaje para revisar o reanudar.'}
Write-Output 'VALIDACION A4 COMPLETA. Los resultados son reales; las capturas y el video se toman por separado.'
