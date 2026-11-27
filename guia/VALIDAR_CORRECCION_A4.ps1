$ErrorActionPreference='Stop'
$raizA4=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
& (Join-Path $raizA4 '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'validar_correccion_a4.py')
if($LASTEXITCODE -ne 0){throw 'Las pruebas requieren revision. Conserva el mensaje final.'}
Write-Output 'CORRECCION COMPROBADA. El informe y la publicacion se preparan con estos resultados.'
