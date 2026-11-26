"""Prepara un ZIP del commit revisado y el comando de publicacion para PowerShell."""
import hashlib
import json
from pathlib import Path
import subprocess

raiz=Path(__file__).resolve().parents[1]
git=Path("C:/Program Files/Git/cmd/git.exe")
salida=raiz.parent/"output/actividad4_entrega"
salida.mkdir(parents=True,exist_ok=True)


def ejecutar(*args):
    return subprocess.check_output([str(git),"-C",str(raiz),*args],text=True).strip()


commit=ejecutar("rev-parse","HEAD")
if ejecutar("status","--porcelain"):
    raise SystemExit("Hay cambios sin incluir en el commit revisado")
if ejecutar("rev-parse","a4-MajesDo63^{}")!=commit:
    raise SystemExit("La etiqueta no apunta al commit revisado")
zip_path=salida/"Actividad4_Cesar_Entrega.zip"
subprocess.run([str(git),"-C",str(raiz),"archive","--format=zip","--prefix=Act4-Cesar/",str("--output="+str(zip_path)),"HEAD"],check=True)
plantilla=r'''$ErrorActionPreference='Stop'
$repoA4='__REPO__'
$gitA4='__GIT__'
$commitEsperadoA4='__COMMIT__'
function Ejecutar-GitA4 {
    param([string[]]$Argumentos)
    $anteriorA4=$ErrorActionPreference
    $ErrorActionPreference='Continue'
    try {
        $salidaGitA4=& $gitA4 -C $repoA4 @Argumentos 2>&1
        $codigoGitA4=$LASTEXITCODE
    } finally {$ErrorActionPreference=$anteriorA4}
    if($codigoGitA4 -ne 0){throw (($salidaGitA4 | ForEach-Object {$_.ToString()}) -join [Environment]::NewLine)}
    return @($salidaGitA4 | ForEach-Object {$_.ToString()})
}
$remotoA4=((Ejecutar-GitA4 -Argumentos @('remote','get-url','origin')) -join '').Trim()
if($remotoA4 -ne 'https://github.com/MajesDo63/Act4-Cesar.git'){throw 'El repositorio de destino no coincide.'}
$revisionA4=((Ejecutar-GitA4 -Argumentos @('rev-parse','HEAD')) -join '').Trim()
if($revisionA4 -ne $commitEsperadoA4){throw 'La revision local cambio; revisala antes de publicar.'}
$etiquetaA4=((Ejecutar-GitA4 -Argumentos @('rev-parse','a4-MajesDo63^{}')) -join '').Trim()
if($etiquetaA4 -ne $commitEsperadoA4){throw 'La etiqueta no coincide con la entrega revisada.'}
$cambiosA4=(Ejecutar-GitA4 -Argumentos @('status','--porcelain')) -join ''
if($cambiosA4.Trim()){throw 'Hay cambios locales fuera del commit revisado.'}
Write-Output 'Publicando exclusivamente en MajesDo63/Act4-Cesar. Git puede solicitar iniciar sesion.'
Ejecutar-GitA4 -Argumentos @('push','--atomic','origin','main','refs/tags/a4-MajesDo63') | ForEach-Object {Write-Output $_}
$referenciasA4=Ejecutar-GitA4 -Argumentos @('ls-remote','origin','refs/heads/main','refs/tags/a4-MajesDo63','refs/tags/a4-MajesDo63^{}')
$tablaA4=@{}
foreach($lineaA4 in $referenciasA4){$partesA4=$lineaA4 -split '\s+'; if($partesA4.Count -ge 2){$tablaA4[$partesA4[1]]=$partesA4[0]}}
if($tablaA4['refs/heads/main'] -ne $commitEsperadoA4 -or $tablaA4['refs/tags/a4-MajesDo63^{}'] -ne $commitEsperadoA4){throw 'No se pudo comprobar la revision publicada y la etiqueta.'}
$registroA4=@{repositorio=$remotoA4;commit=$commitEsperadoA4;main_verificado=$true;etiqueta='a4-MajesDo63';etiqueta_verificada=$true;fecha_utc=[DateTime]::UtcNow.ToString('o')}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'verificacion_publicacion.json'),(ConvertTo-Json $registroA4),(New-Object Text.UTF8Encoding($false)))
Write-Output 'PUBLICACION COMPLETA Y VERIFICADA: https://github.com/MajesDo63/Act4-Cesar/tree/a4-MajesDo63'
'''
script=plantilla.replace("__REPO__",str(raiz)).replace("__GIT__",str(git)).replace("__COMMIT__",commit)
(salida/"PUBLICAR_ACT4.ps1").write_text(script,encoding="utf-8-sig")
registro={"repositorio":"https://github.com/MajesDo63/Act4-Cesar","commit":commit,"etiqueta":"a4-MajesDo63",
          "zip":zip_path.name,"bytes_zip":zip_path.stat().st_size,"sha256_zip":hashlib.sha256(zip_path.read_bytes()).hexdigest(),
          "publicado":False,"script_publicacion":"PUBLICAR_ACT4.ps1"}
(salida/"preparacion_entrega.json").write_text(json.dumps(registro,ensure_ascii=False,indent=2),encoding="utf-8")
print("PAQUETE PREPARADO: "+str(zip_path))
print("PUBLICACION PREPARADA: "+str(salida/"PUBLICAR_ACT4.ps1"))
print("REVISION: "+commit)
