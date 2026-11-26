$ErrorActionPreference='Stop'
$raizA4=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pythonA4=Join-Path $raizA4 '.venv\Scripts\python.exe'
$registroA4=Join-Path $raizA4 'bitacora\a4\sesion_interfaz'
New-Item -ItemType Directory -Path $registroA4 -Force | Out-Null

function Estado-A4([string]$Url){
    try{return Invoke-RestMethod -Uri $Url -TimeoutSec 2}catch{return $null}
}
$saludA4=Estado-A4 'http://127.0.0.1:8004/salud'
if($saludA4 -and $saludA4.agente -ne 'Ejecutor propio A4'){throw 'El puerto 8004 esta ocupado por otro servicio.'}
if(-not $saludA4){
    Write-Output 'Iniciando la API local de Actividad 4.'
    $argumentosApiA4='"'+(Join-Path $PSScriptRoot 'servidor_a4.py')+'"'
    $apiA4=Start-Process -FilePath $pythonA4 -ArgumentList $argumentosApiA4 -WorkingDirectory $raizA4 -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $registroA4 'api_stdout.txt') -RedirectStandardError (Join-Path $registroA4 'api_stderr.txt')
    [IO.File]::WriteAllText((Join-Path $registroA4 'api.pid'),[string]$apiA4.Id)
    for($intentoA4=0;$intentoA4 -lt 20;$intentoA4++){
        $saludA4=Estado-A4 'http://127.0.0.1:8004/salud'
        if($saludA4){break}
        Start-Sleep -Milliseconds 500
    }
}
if(-not $saludA4){throw ('La API no inicio. Revisa '+(Join-Path $registroA4 'api_stderr.txt'))}
$uiA4=Estado-A4 'http://127.0.0.1:8504/_stcore/health'
if(-not $uiA4){
    Write-Output 'Iniciando la interfaz de Actividad 4.'
    $argumentosUiA4='-m streamlit run "'+(Join-Path $raizA4 'app\interfaz_a4.py')+'" --server.address 127.0.0.1 --server.port 8504 --server.headless true --browser.gatherUsageStats false'
    $interfazA4=Start-Process -FilePath $pythonA4 -ArgumentList $argumentosUiA4 -WorkingDirectory $raizA4 -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $registroA4 'ui_stdout.txt') -RedirectStandardError (Join-Path $registroA4 'ui_stderr.txt')
    [IO.File]::WriteAllText((Join-Path $registroA4 'ui.pid'),[string]$interfazA4.Id)
    for($intentoA4=0;$intentoA4 -lt 30;$intentoA4++){
        $uiA4=Estado-A4 'http://127.0.0.1:8504/_stcore/health'
        if($uiA4){break}
        Start-Sleep -Milliseconds 500
    }
}
if(-not $uiA4){throw ('La interfaz no inicio. Revisa '+(Join-Path $registroA4 'ui_stderr.txt'))}
Write-Output 'A4 ABIERTA: http://127.0.0.1:8504'
Write-Output 'Crea una cuenta en la interfaz. El token no se muestra ni se copia.'
Start-Process 'http://127.0.0.1:8504'
