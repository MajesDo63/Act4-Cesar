$ErrorActionPreference='Stop'
$raizA4=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$registroA4=Join-Path $raizA4 'bitacora\a4\sesion_interfaz'
foreach($servicioA4 in @('api','ui')){
    $archivoPidA4=Join-Path $registroA4 ($servicioA4+'.pid')
    if(Test-Path -LiteralPath $archivoPidA4){
        $numeroProcesoA4=0
        if([int]::TryParse([IO.File]::ReadAllText($archivoPidA4),[ref]$numeroProcesoA4)){
            $procesoA4=Get-CimInstance Win32_Process -Filter ('ProcessId='+$numeroProcesoA4) -ErrorAction SilentlyContinue
            if($procesoA4 -and $procesoA4.CommandLine -like ('*'+$raizA4+'*')){
                Stop-Process -Id $numeroProcesoA4 -ErrorAction SilentlyContinue
                Write-Output ('Servicio '+$servicioA4+' cerrado.')
            }
        }
    }
}
