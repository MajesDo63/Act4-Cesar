$ErrorActionPreference='Stop'
$raizA4=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pythonBaseA4=Join-Path ([IO.Path]::GetFullPath((Join-Path $raizA4 '..\actividad3_cesar'))) '.venv\Scripts\python.exe'
if(-not (Test-Path -LiteralPath $pythonBaseA4)){throw 'No se encontro el interprete que utilizamos en la A3.'}
$pythonA4=Join-Path $raizA4 '.venv\Scripts\python.exe'
if(-not (Test-Path -LiteralPath $pythonA4)){
    Write-Output 'Creando el entorno independiente de Actividad 4.'
    & $pythonBaseA4 -m venv --system-site-packages (Join-Path $raizA4 '.venv')
    if($LASTEXITCODE -ne 0){throw 'No se pudo crear el entorno A4.'}
}
Write-Output 'Instalando Streamlit, Ruff y las dependencias del proyecto.'
& $pythonA4 -m pip install -r (Join-Path $raizA4 'requirements.txt')
if($LASTEXITCODE -ne 0){throw 'La instalacion no termino; conserva el mensaje de error.'}
& $pythonA4 -m pip install -e $raizA4
if($LASTEXITCODE -ne 0){throw 'No se pudo registrar el proyecto local.'}
$rutasA4=@($raizA4,(Join-Path $raizA4 'src'))
[IO.File]::WriteAllLines((Join-Path $raizA4 '.venv\Lib\site-packages\a4-local.pth'),$rutasA4,(New-Object Text.UTF8Encoding($false)))
& $pythonA4 (Join-Path $PSScriptRoot 'comprobar_entorno.py')
if($LASTEXITCODE -ne 0){throw 'No se pudo comprobar el entorno.'}
Write-Output 'ENTORNO A4 LISTO. Las credenciales permanecen en la configuracion local.'
