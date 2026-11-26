"""Prepara una copia publicable de la grabacion, sin recortes ni elementos anadidos."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import imageio_ffmpeg


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("origen",type=Path)
    args=ap.parse_args()
    raiz=Path(__file__).resolve().parents[1]
    origen=args.origen.resolve()
    destino=raiz/"evidencias/demo/Actividad4_Cesar.mp4"
    trabajo=raiz/"bitacora/a4/revision_video"
    trabajo.mkdir(parents=True,exist_ok=True)
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    def duracion(archivo):
        r=subprocess.run([ffmpeg,"-hide_banner","-i",str(archivo)],capture_output=True,text=True,timeout=20)
        m=re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)",r.stderr)
        if m is None:raise RuntimeError("No se pudo leer el video")
        return int(m[1])*3600+int(m[2])*60+float(m[3])
    segundos=duracion(origen)
    # La consigna indica una demo de dos minutos, sin establecer un maximo exacto.
    # Conservo completa la grabacion elegida por el alumno (2 min 13 s).
    if not 115<=segundos<=150:
        raise SystemExit(f"La grabacion dura {segundos:.2f} s. Revisa la duracion de la demo.")
    hash_origen=hashlib.sha256(origen.read_bytes()).hexdigest()
    destino.parent.mkdir(parents=True,exist_ok=True)
    temporal=trabajo/"copia_publicable.mp4"
    comprimido=origen.stat().st_size>=95_000_000
    if comprimido:
        comando=[ffmpeg,"-hide_banner","-y","-i",str(origen),"-map","0:v:0","-map","0:a?",
                 "-c:v","libx264","-preset","fast","-crf","20","-threads","2","-c:a","copy",
                 "-movflags","+faststart",str(temporal)]
        r=subprocess.run(comando,capture_output=True,timeout=300)
        (trabajo/"compresion_sin_edicion.log").write_bytes(r.stderr)
        if r.returncode:raise RuntimeError("La copia para distribucion no termino")
    else:
        shutil.copy2(origen,temporal)
    duracion_final=duracion(temporal)
    assert abs(duracion_final-segundos)<.2,"La duracion cambio"
    assert hashlib.sha256(origen.read_bytes()).hexdigest()==hash_origen,"La grabacion original cambio durante el proceso"
    assert temporal.stat().st_size<95_000_000,"La copia sigue siendo demasiado grande"
    shutil.copy2(temporal,destino)
    registro={"fuente":"Grabacion directa de la interfaz realizada por Cesar Eduardo Valdez Pinto",
              "duracion_original_s":segundos,"duracion_final_s":duracion_final,"bytes_original":origen.stat().st_size,
              "bytes_final":destino.stat().st_size,"sha256_original":hash_origen,
              "sha256_final":hashlib.sha256(destino.read_bytes()).hexdigest(),
              "compresion_para_distribucion":comprimido,"recortes":False,"rotulos_anadidos":False,
              "presentacion_anadida":False,"cambio_de_velocidad":False,"resolucion_y_pista_de_audio":"Conservadas"}
    (destino.parent/"video_verificado.json").write_text(json.dumps(registro,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"GRABACION PREPARADA: {duracion_final:.2f} s; {destino.stat().st_size/1_000_000:.2f} MB; sin recortes ni elementos anadidos.")


if __name__=="__main__":main()
