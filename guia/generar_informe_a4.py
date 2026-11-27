"""Genera el informe de siete paginas con resultados y capturas originales de A4."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from pypdf import PdfReader

RAIZ = Path(__file__).resolve().parents[1]
REPO = "https://github.com/MajesDo63/Act4-Cesar"
VIDEO_URL = REPO + "/raw/refs/tags/a4-MajesDo63/evidencias/demo/Actividad4_Cesar.mp4"
AZUL = "17384D"
VERDE = "087F8C"


def arquitectura(destino):
    from reportlab.pdfgen import canvas
    import pypdfium2 as pdfium
    pdf = destino.with_suffix('.pdf')
    c = canvas.Canvas(str(pdf), pagesize=(600,210))
    nodos = [(78,160,'Interfaz Streamlit','Sesion y resultados'),
             (282,160,'API de A3 + A4','Token y limite'),
             (492,160,'Ejecutor propio','IA propone JSON'),
             (78,48,'Confirmacion','Informe por usuario'),
             (282,48,'Validador tradicional','Citas y respaldo'),
             (492,48,'Herramienta Ruff','Solo analisis estatico')]
    for x,y,t1,t2 in nodos:
        c.setFillColor(colors.HexColor('#eef6f7'))
        c.setStrokeColor(colors.HexColor('#087F8C'))
        c.roundRect(x-70,y-23,140,46,5,fill=1,stroke=1)
        c.setFillColor(colors.HexColor('#17384D'))
        c.setFont('Helvetica-Bold',9.2);c.drawCentredString(x,y+4,t1)
        c.setFont('Helvetica',8.6);c.drawCentredString(x,y-10,t2)
    import math
    for x1,y1,x2,y2 in [(153,160,207,160),(357,160,417,160),
                         (492,132,492,76),(417,48,357,48),
                         (282,76,282,132),(78,132,78,76),(153,62,207,132)]:
        c.setStrokeColor(colors.HexColor('#17384D'));c.setFillColor(colors.HexColor('#17384D'))
        c.line(x1,y1,x2,y2)
        ang=math.atan2(y2-y1,x2-x1)
        path=c.beginPath();path.moveTo(x2,y2)
        path.lineTo(x2-7*math.cos(ang-.4),y2-7*math.sin(ang-.4))
        path.lineTo(x2-7*math.cos(ang+.4),y2-7*math.sin(ang+.4));path.close()
        c.drawPath(path,fill=1,stroke=0)
    c.setFont('Helvetica',7.8)
    c.drawString(85,103,'decision')
    c.drawString(291,103,'resultado / pendiente')
    c.save()
    document=pdfium.PdfDocument(str(pdf))
    page=document[0]
    bitmap=page.render(scale=2)
    bitmap.to_pil().save(destino)
    bitmap.close();page.close();document.close()


def crear_paginas(carpeta, video_url):
    metadatos_video = RAIZ / "evidencias/demo/video_verificado.json"
    segundos_video = round(json.loads(metadatos_video.read_text(encoding="utf-8"))["duracion_final_s"]) if metadatos_video.exists() else 133
    etiqueta_video = f"Demo ({segundos_video // 60} min {segundos_video % 60:02d} s): "
    datos = json.loads((carpeta / "resumen.json").read_text(encoding="utf-8"))
    pruebas = json.loads((carpeta / "pruebas.json").read_text(encoding="utf-8"))
    correccion = None
    marcador = RAIZ / "bitacora/a4/ultima_correccion.txt"
    if marcador.exists():
        ruta_correccion = RAIZ / marcador.read_text(encoding="utf-8").strip()
        correccion = json.loads((ruta_correccion / "validacion.json").read_text(encoding="utf-8"))
        assert correccion["estado"] == "completo"
        pruebas = {"aprobadas": correccion["aprobadas"], "omitidas": correccion["omitidas"]}
    entorno = json.loads((RAIZ / "bitacora/a4/entorno_inicial.json").read_text(encoding="utf-8"))
    por_clave = {(d["version"], d["archivo"]): d for d in datos}
    reanalisis = json.loads((RAIZ / "bitacora/a4/reanalisis/resultados.json").read_text(encoding="utf-8"))
    independientes = {(r["version"], r["archivo"]): r for r in reanalisis["resultados"]}
    tabla = [["Entrada", "Referencia SEC", "Detectados v1 / v2", "Omitidos v1 / v2"]]
    for archivo in ("usuarios.py", "limites.py", "tokens.py", "reportes.py", "transferencias.py"):
        a, b = (independientes[v, archivo] for v in ("v1", "v2"))
        tabla.append([archivo, str(b['referencia_problemas']), f"{a['detectados']} / {b['detectados']}",
                      f"{a['omisiones_cobertura']} / {b['omisiones_cobertura']}"])
    imagen = lambda nombre, titulo, alto=7.6: ("imagen", {"ruta": RAIZ / "evidencias/capturas" / nombre, "titulo": titulo, "alto": alto})
    return [
      [("kicker", "LSCA2318 · ACTIVIDAD 4"), ("titulo", "Agente con herramientas y validación"),
       ("p", "Revisor de código Python para FinNorte"),
       ("p", "Cesar Eduardo Valdez Pinto · MajesDo63 · 26 de noviembre de 2026"),
       ("h", "1. Propósito y arquitectura"),
       ("p", "Construí un agente que utiliza Ruff para analizar ejemplos Python. La interfaz unificada app/cliente_api.py tiene dos modos: Mi variante envía código al endpoint /v1/revisor de mi A3; Agente llama a /v1/agente y muestra herramientas, fuentes, validación y confirmación. El modelo propone acciones en JSON y mi ejecutor decide cuáles se admiten."),
       ("diagrama", None),
       ("caption", "Figura 1. Componentes de la implementación. La confirmación de guardado vuelve a la API; el modelo no autoriza sus propios efectos."),
       ("tabla", [["Componente", "Responsabilidad"], ["Streamlit", "Acceso, carga, errores, hallazgos, fuentes, bitácora y decisión."],
                  ["API y autenticación", "Token, control de solicitudes y respuestas problem+json."],
                  ["Ejecutor y herramientas", "Catálogo, esquemas, límites, análisis y propuesta de guardado."],
                  ["Validador", "Regla SEC, línea, evidencia, huella y respuesta respaldada."]]),
       ("p", "Partí de mi entrega A3, commit e80daefcce32d31af562c7ac5c65f998d409009f. El agente de A4 utiliza mi implementación de ejecutar_agente, no el ejecutor de referencia del caso guía."),
       ("link", "Repositorio: " + REPO), ("p", "Etiqueta de entrega: a4-MajesDo63")],
      [("h", "2. Catálogo, controles y validador"),
       ("tabla", [["Herramienta", "Argumentos / tipo", "Control y límite"],
                  ["correr_linter", "ruta: nombre del catálogo. Consulta sin efecto persistente.", "JSON Schema cerrado; archivo .py autorizado; 20 000 bytes; timeout de 10 s."],
                  ["guardar_informe", "ruta, huella SHA-256 y nombre .json. Acción sensible.", "Análisis previo en la misma solicitud; confirmación; usuario; TTL 600 s; un solo uso; sin reemplazo."]]),
       ("p", "Ruff recibe el contenido del archivo por stdin. La invocación utiliza una lista fija de argumentos, shell=False, --isolated y --no-cache. No utiliza --fix, no importa el archivo revisado y no ejecuta su código. El catálogo impide rutas absolutas, traversal, archivos privados y opciones de comando propuestas por el modelo."),
       ("tabla", [["Reglas Ruff", "Regla del corpus", "Patrón revisado"],
                  ["S311, S324", "SEC-06", "Aleatoriedad no criptográfica y algoritmos débiles."],
                  ["S608", "SEC-02", "Consultas SQL construidas como cadenas."],
                  ["S301, S307, S602, S506", "SEC-09", "pickle, eval, shell=True y YAML sin carga segura."]]),
       ("p", "Después de ejecutar las herramientas, valido cada resultado del agente. Compruebo que la regla SEC y la fuente existan en el corpus, que la línea exista, que la evidencia coincida literalmente con el código y que la huella sea la de la entrada. También verifico el código de Ruff y el resumen autorizado. La respuesta final y las fuentes deben coincidir con ese resumen; una salida sin respaldo se bloquea."),
       ("p", "En limites.py exijo cero hallazgos. Ese control es específico del ejemplo; no demuestra seguridad general. Para un fallo de herramienta permito un mensaje de control que informa el fallo y no presenta una revisión exitosa. Por eso el mensaje de fallo puede superar el validador sin que la revisión haya terminado."),
       ("p", "El ejecutor limita los pasos a seis en la API, detecta acciones repetidas, rechaza herramientas desconocidas y registra resultados fallidos. Una acción sensible con decisión False o None no se ejecuta. El guardado vuelve a verificar la huella del archivo y utiliza únicamente los argumentos vistos en la confirmación."),
       ("p", "Alcance: estas reglas no cubren todas las políticas SEC. Por ejemplo, no detectan el control de propiedad ausente en cuentas_api.py ni todos los datos sensibles de los logs. Cero hallazgos se interpreta dentro del alcance configurado.")],
      [("h", "3. Pruebas y entorno de ejecución"),
       ("p", f"La suite corregida aprobó {pruebas['aprobadas']} pruebas y omitió {pruebas['omitidas']} en Windows 11 con Python 3.14.7. Añadí cinco pruebas de interacción de Streamlit y seis del reanálisis. La captura original conserva el resultado previo de 109 pruebas; el registro de la corrección contiene la suite actual completa. La advertencia de Starlette/AnyIO no produjo fallos."),
       ("tabla", [["Grupo", "Qué comprobé"], ["Oficiales y ejecutor", "Tres casos del kit, esquemas, herramientas desconocidas, máximo de pasos, repeticiones y fallo controlado."],
                  ["Ruff y validador", "Reglas reales, límites de rutas y tamaño, citas manipuladas, huellas y respuestas sin respaldo."],
                  ["Confirmaciones", "Rechazo, falta de decisión, otro usuario, expiración, concurrencia, cambio de archivo y no reemplazo."],
                  ["API y base A3", "Token, entradas, rate limit, errores, ruta genérica eliminada y autenticación heredada."],
                  ["Interfaz y evaluación", "Mi variante envía código y token; Agente muestra el fallo sin revisión aprobada; referencia con problemas distintos en una misma línea."]]),
       imagen("06_pruebas_powershell.png", "Figura 2. Captura original de PowerShell: 109 pruebas aprobadas en la ejecución manual.", 2.0),
       ("p", "Ejecuté el proyecto desde C:/Users/cesar/OneDrive/Documentos/ChatGPT/Estudiar/actividad4_cesar con .venv/Scripts/python.exe. Repito las pruebas con python -m pytest tests -q. La corrección se comprueba con guia/VALIDAR_CORRECCION_A4.ps1; su validacion.json y pytest.xml registran el comando, el intérprete y las huellas actuales."),
       ("tabla", [["Dependencia", "Versión usada"], *[[k, entorno["paquetes"][k]] for k in ("fastapi", "starlette", "streamlit", "ruff", "pytest", "jsonschema")]]),
       ("p", "Las pruebas usan fake/hash y HTTP simulado para la interfaz. Conservé las diez respuestas reales de Gemini de la ronda original. Verifiqué que el motor, API, prompts, corpus y entradas de esa ronda no cambiaron; probé por separado la interfaz corregida. El reanálisis no se presenta como una consulta nueva al modelo.")],
      [("h", "4. Evaluación, causas y trazabilidad"),
       ("p", "Comparé las mismas cinco entradas con gemini-3.1-flash-lite y temperatura 0. Después anoté 14 problemas por inspección del código y las políticas SEC, con asistencia, sin utilizar Ruff para definir la referencia. Es una revisión posterior, no ciega ni exhaustiva. Reanalicé los diez registros originales intactos."),
       ("tabla", tabla),
       ("p", "Mejora 1, herramienta: al ampliar las reglas de v1 a v2 detecté tres problemas adicionales de YAML, pickle y shell; aún quedan seis sin cubrir: dos comparaciones de secretos, dos registros de datos sensibles, una llave de ejemplo en código y un monto float. Mejora 2, agente: v1 incumplió el contrato literal en cinco respuestas; al precisar resumen y fuentes, los cinco contratos v2 aprobaron. Eso no demuestra cobertura total ni que las paráfrasis de v1 fueran falsas."),
       ("p", "No observé hallazgos adicionales ni respuestas genéricas en estos diez casos. Las pruebas negativas controladas comprueban el bloqueo de información sin respaldo, pero no se cuentan como alucinaciones observadas de Gemini. La muestra tiene una ejecución por entrada y versión."),
       ("tabla", [["Regla / entrada", "Análisis", "Artefacto", "Hallazgo o prueba", "Validador"],
                  ["SEC-06 usuarios", "MD5 y random", "v2_usuarios.json", "S324 L6/L14; S311 L8", "Aprobado"],
                  ["SEC-09 tokens", "YAML inseguro", "v2_tokens.json", "S506 L6", "Aprobado"],
                  ["SEC-09 reportes", "pickle y shell", "v2_reportes.json", "S301 L9; S602 L13", "Aprobado"],
                  ["SEC-02 transferencias", "SQL interpolado", "v2_transferencias.json", "S608 L8/L11", "Aprobado"],
                  ["Control limites", "Decimal y límite", "v2_limites.json", "0 esperados / 0 emitidos", "Aprobado"]]),
       ("small", "Artefactos: bitacora/a4/evaluacion_20261126T221709Z/. La matriz completa a4/TRAZABILIDAD.md incluye los 14 problemas y el control negativo. Aprobado significa integridad de la respuesta; no significa detectar todos los problemas. Referencia: a4/referencia_revision.json. Resultados: a4/RESULTADOS_INDEPENDIENTES.csv.")],
      [("h", "5. Evidencias de revisión en la interfaz"),
       ("p", "Tomé estas capturas desde la aplicación en mi computadora después de iniciar sesión. Las imágenes originales se conservan en evidencias/capturas."),
       imagen("01_revision_usuarios.png", "Figura 3. usuarios.py: tres hallazgos SEC-06 en las líneas 6, 8 y 14, fuente del corpus y validador aprobado.", 8.0),
       imagen("02_limites_sin_hallazgos.png", "Figura 4. limites.py: cero hallazgos en el alcance configurado, huella y bitácora del agente.", 8.0)],
      [("h", "6. Confirmación y rechazo sin efecto"),
       ("p", "Solicité revisar usuarios.py y preparar revision_cesar.json. La API mostró la herramienta, la ruta, la huella y el nombre antes de decidir. Después rechacé el guardado: la respuesta indicó efecto false y no se creó un informe. Las pruebas también comprueban que el rechazo no crea el directorio de informes."),
       imagen("03_confirmacion_pendiente.png", "Figura 5. Acción pendiente con los argumentos exactos y botones para aprobar o rechazar.", 7.4),
       imagen("04_confirmacion_rechazada.png", "Figura 6. Rechazo confirmado: estado rechazada, efecto false y validador aprobado.", 7.4),
       ("p", "La confirmación pertenece al usuario autenticado, caduca en 600 segundos y tiene un solo uso. Aprobar ejecuta la función guardada, sin pedirle al modelo que vuelva a decidir los argumentos. Los cambios de huella, la repetición y el acceso de otro usuario se bloquean.")],
      [("h", "7. Fallo de herramienta, reflexión y demo"),
       imagen("05_fallo_herramienta.png", "Figura 7. Archivo inexistente: FileNotFoundError, paso fallida y ausencia de revisión final.", 8.0),
       ("p", "Probé inexistente.py para provocar de forma controlada un FileNotFoundError. El servicio detuvo la revisión. La captura original conserva el indicador anterior; en la interfaz corregida aparece Mensaje de fallo validado · El análisis no se completó, separado del error de la herramienta. La prueba no equivale a una revisión aprobada."),
       ("p", "Aprendí que un agente necesita separar propuesta, validación y efecto. El modelo puede elegir una herramienta o redactar una respuesta incompatible con el contrato. Los esquemas, el catálogo, el validador y la confirmación conservan el control en el código. La mejora de cobertura depende de reglas concretas: un resultado sin hallazgos no basta para declarar seguro un programa."),
       ("link", etiqueta_video + video_url),
       ("p", "Grabé la demo directamente desde la interfaz, sin narración ni rótulos añadidos. Muestro la revisión, el caso limpio, el rechazo del guardado, el fallo de herramienta y la bitácora. El uso de asistentes y mis decisiones quedan en ai_log.md, y los registros reales de Gemini respaldan la comparación."),
       ("h", "Referencias"),
       ("small", "Material del curso. Manual del alumno y presentación de Actividades 3 y 4, kit lsca2318-lab-a3-a4. Requisitos y pruebas oficiales de la Actividad 4."),
       ("small", "Astral. Ruff: reglas de análisis estático. https://docs.astral.sh/ruff/rules/"),
       ("small", "Streamlit. Documentación de la interfaz. https://docs.streamlit.io/"),
       ("small", "Fuentes del proyecto: corpus/v2-revisor/sec-02-sql-parametrizado.md, sec-06-criptografia.md y sec-09-deserializacion-comandos.md. Los nombres exactos y textos citados se conservan en las salidas de las herramientas.")]
    ]


def dibujar_pdf(paginas, destino, diagrama):
    pdfmetrics.registerFont(TTFont("A4Arial", "C:/Windows/Fonts/arial.ttf"))
    pdfmetrics.registerFont(TTFont("A4ArialBold", "C:/Windows/Fonts/arialbd.ttf"))
    estilos = {
        "p": ParagraphStyle("P", fontName="A4Arial", fontSize=9.4, leading=13.2, spaceAfter=7, textColor=colors.HexColor("#243746")),
        "h": ParagraphStyle("H", fontName="A4ArialBold", fontSize=15, leading=19, spaceAfter=11, textColor=colors.HexColor("#"+AZUL)),
        "titulo": ParagraphStyle("T", fontName="A4ArialBold", fontSize=24, leading=28, spaceAfter=12, textColor=colors.HexColor("#"+AZUL)),
        "kicker": ParagraphStyle("K", fontName="A4ArialBold", fontSize=10, leading=14, spaceAfter=9, textColor=colors.HexColor("#"+VERDE)),
        "caption": ParagraphStyle("C", fontName="A4Arial", fontSize=8, leading=10.6, spaceAfter=9, textColor=colors.HexColor("#506675")),
        "small": ParagraphStyle("S", fontName="A4Arial", fontSize=8, leading=10.5, spaceAfter=6),
    }
    ancho = 17.9*cm
    def parrafo(texto, tipo="p"):
        return Paragraph(escape(texto).replace("\n", "<br/>"), estilos[tipo])
    def imagen(ruta, maxalto):
        w,h = PILImage.open(ruta).size
        escala = min(ancho/w, maxalto*cm/h)
        return Image(str(ruta), width=w*escala, height=h*escala, hAlign="CENTER")
    elementos = []
    for n, bloques in enumerate(paginas):
        if n:
            elementos.append(PageBreak())
        for tipo, valor in bloques:
            if tipo in estilos:
                elementos.append(parrafo(valor, tipo))
            elif tipo == "link":
                prefix, url = valor.split("https://", 1)
                elementos.append(Paragraph(escape(prefix)+f'<link href="https://{escape(url)}" color="#087F8C">'+escape("https://"+url)+"</link>", estilos["small"]))
            elif tipo == "diagrama":
                elementos.extend([imagen(diagrama, 5.2), Spacer(1, 6)])
            elif tipo == "imagen":
                elementos.append(KeepTogether([imagen(valor["ruta"], valor["alto"]), Spacer(1, 5), parrafo(valor["titulo"], "caption")]))
            elif tipo == "tabla":
                filas = [[parrafo(str(c), "small") for c in fila] for fila in valor]
                proporciones = [1]*len(valor[0])
                if len(proporciones)==2:
                    proporciones=[1,2.5]
                anchos = [ancho*p/sum(proporciones) for p in proporciones]
                t=Table(filas, colWidths=anchos, hAlign="LEFT", repeatRows=1)
                t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e3f1f3")),
                    ("VALIGN",(0,0),(-1,-1),"TOP"),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#cad6dc")),
                    ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
                    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
                elementos.extend([t,Spacer(1,9)])
    def marco(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#"+VERDE))
        canvas.line(1.55*cm,28.15*cm,19.45*cm,28.15*cm)
        canvas.setFont("A4Arial",7.5)
        canvas.setFillColor(colors.HexColor("#506675"))
        canvas.drawString(1.55*cm,28.45*cm,"FINNORTE · ACTIVIDAD 4")
        canvas.drawRightString(19.45*cm,1.0*cm,f"Cesar Eduardo Valdez Pinto · {doc.page}")
    doc=SimpleDocTemplate(str(destino),pagesize=(21*cm,29.7*cm),leftMargin=1.55*cm,rightMargin=1.55*cm,
                          topMargin=1.9*cm,bottomMargin=1.6*cm,title="Actividad 4 · Cesar Eduardo Valdez Pinto",
                          author="Cesar Eduardo Valdez Pinto")
    doc.build(elementos,onFirstPage=marco,onLaterPages=marco)
    if len(PdfReader(str(destino)).pages) != 7:
        raise RuntimeError("El informe debe tener siete paginas; revisa el desbordamiento")


def dibujar_word(paginas, destino, diagrama):
    d=Document()
    s=d.sections[0]
    s.page_width=Cm(21); s.page_height=Cm(29.7)
    s.top_margin=Cm(1.7); s.bottom_margin=Cm(1.5); s.left_margin=Cm(1.55); s.right_margin=Cm(1.55)
    normal=d.styles["Normal"]
    normal.font.name="Arial"; normal.font.size=Pt(9)
    normal.paragraph_format.space_after=Pt(5)
    normal.paragraph_format.line_spacing=1.05
    for nom,tam in [("Title",24),("Heading 1",15),("Heading 2",12)]:
        d.styles[nom].font.name="Arial"; d.styles[nom].font.size=Pt(tam); d.styles[nom].font.color.rgb=RGBColor.from_string(AZUL)
    s.header.paragraphs[0].text="FINNORTE · ACTIVIDAD 4"
    s.header.paragraphs[0].style="Caption"
    pie=s.footer.paragraphs[0]
    pie.text="Cesar Eduardo Valdez Pinto · "
    campo=OxmlElement("w:fldSimple"); campo.set(qn("w:instr"),"PAGE"); pie._p.append(campo)
    def poner_imagen(ruta, maxalto):
        w,h=PILImage.open(ruta).size
        escala=min(17.9/w,maxalto/h)
        p=d.add_paragraph(); p.alignment=1
        p.paragraph_format.space_after=Pt(3)
        p.add_run().add_picture(str(ruta),width=Cm(w*escala),height=Cm(h*escala))
    for n,bloques in enumerate(paginas):
        if n:d.add_page_break()
        for tipo,valor in bloques:
            if tipo=="titulo":d.add_paragraph(valor,"Title")
            elif tipo=="h":d.add_paragraph(valor,"Heading 1")
            elif tipo=="kicker":
                p=d.add_paragraph(valor); p.runs[0].bold=True; p.runs[0].font.color.rgb=RGBColor.from_string(VERDE)
            elif tipo in ("p","link","small","caption"):
                p=d.add_paragraph(valor,"Caption" if tipo=="caption" else None)
                if tipo in ("small","link"):
                    for r in p.runs:r.font.size=Pt(8)
            elif tipo=="diagrama":poner_imagen(diagrama,5.2)
            elif tipo=="imagen":
                poner_imagen(valor["ruta"],valor["alto"])
                d.add_paragraph(valor["titulo"],"Caption")
            elif tipo=="tabla":
                t=d.add_table(rows=0,cols=len(valor[0])); t.style="Light Shading Accent 1"
                for fila in valor:
                    celdas=t.add_row().cells
                    for celda,texto in zip(celdas,fila):
                        celda.text=str(texto)
                        for p in celda.paragraphs:
                            p.paragraph_format.space_after=Pt(3)
                            for r in p.runs:r.font.size=Pt(8)
                d.add_paragraph().paragraph_format.space_after=Pt(1)
    d.core_properties.author="Cesar Eduardo Valdez Pinto"
    d.core_properties.title="Actividad 4 · Agente con herramientas y validación"
    d.save(destino)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--borrador",action="store_true")
    ap.add_argument("--video-url",default=VIDEO_URL)
    args=ap.parse_args()
    carpeta=RAIZ/(RAIZ/"bitacora/a4/ultima_evaluacion.txt").read_text(encoding="utf-8").strip()
    if json.loads((carpeta/"estado.json").read_text(encoding="utf-8"))["estado"]!="completo":
        raise SystemExit("Falta una evaluacion completa")
    if not args.borrador and not (RAIZ/"evidencias/demo/Actividad4_Cesar.mp4").is_file():
        raise SystemExit("Falta la grabacion real de la demo")
    salida=RAIZ/"entrega"; salida.mkdir(exist_ok=True)
    diagrama=salida/"arquitectura_a4.png"
    arquitectura(diagrama)
    paginas=crear_paginas(carpeta,args.video_url)
    prefijo="Borrador_" if args.borrador else ""
    pdf=salida/(prefijo+"Actividad4_Cesar_Informe.pdf")
    word=salida/(prefijo+"Actividad4_Cesar_Informe.docx")
    dibujar_pdf(paginas,pdf,diagrama)
    dibujar_word(paginas,word,diagrama)
    registro={"pdf":pdf.name,"word":word.name,"paginas_pdf":7,"borrador":args.borrador,
              "video_url":args.video_url,"evaluacion":str(carpeta.relative_to(RAIZ)),
              "sha256_pdf":hashlib.sha256(pdf.read_bytes()).hexdigest()}
    marcador_correccion=RAIZ/'bitacora/a4/ultima_correccion.txt'
    if marcador_correccion.exists():
        registro['correccion']=marcador_correccion.read_text(encoding='utf-8').strip()
    (salida/"informe_estado.json").write_text(json.dumps(registro,ensure_ascii=False,indent=2),encoding="utf-8")
    print("INFORME GENERADO: "+str(pdf))
    print("WORD GENERADO: "+str(word))


if __name__=="__main__":main()
