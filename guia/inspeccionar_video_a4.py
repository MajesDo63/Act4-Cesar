"""Lee la grabacion original y extrae fotogramas para revisar la demo."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import imageio_ffmpeg

raiz=Path(__file__).resolve().parents[1]
origen=Path(sys.argv[1])
salida=raiz/"bitacora/a4/revision_video"
salida.mkdir(parents=True,exist_ok=True)
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
r=subprocess.run([ffmpeg,"-hide_banner","-i",str(origen)],capture_output=True,text=True,timeout=20)
texto=r.stderr
m=re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)",texto)
if not m:raise SystemExit("No se pudo leer la duracion del video")
duracion=int(m[1])*3600+int(m[2])*60+float(m[3])
registro={"origen":str(origen),"bytes_original":origen.stat().st_size,
          "sha256_original":hashlib.sha256(origen.read_bytes()).hexdigest(),"duracion_s":duracion,
          "tiene_audio":"Audio:" in texto,"ffmpeg":ffmpeg,"fotogramas":[]}
for tiempo in [0,10,20,30,40,50,60,70,80,min(87,duracion-0.5)]:
    if tiempo>=duracion:continue
    destino=salida/f"segundo_{tiempo:05.1f}.png"
    comando=[ffmpeg,"-hide_banner","-loglevel","error","-y","-ss",str(tiempo),"-i",str(origen),
             "-frames:v","1","-vf","scale=1280:-2",str(destino)]
    p=subprocess.run(comando,capture_output=True,timeout=30)
    if p.returncode:raise SystemExit("No se pudo extraer un fotograma")
    registro["fotogramas"].append({"tiempo_s":tiempo,"archivo":destino.name})
(salida/"video_original.json").write_text(json.dumps(registro,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"GRABACION LEIDA: {duracion:.2f} segundos; audio: {registro['tiene_audio']}")
print("REVISION DEL VIDEO PREPARADA: "+str(salida))
