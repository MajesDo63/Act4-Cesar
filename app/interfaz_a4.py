"""Interfaz de A4: todas las acciones pasan por la API autenticada."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from finnorte.config import config
import requests
import streamlit as st

st.set_page_config(page_title="FinNorte | Revisor A4", page_icon="🔎", layout="wide")
API = os.getenv("API_URL", "http://127.0.0.1:8004").rstrip("/")
st.title("FinNorte · Revisor de código")
st.caption("Actividad 4 · Cesar Eduardo Valdez Pinto · Análisis estático con Ruff")


def llamar(metodo, ruta, datos=None):
    cabeceras = {"Authorization": "Bearer " + st.session_state.token} if st.session_state.get("token") else {}
    try:
        respuesta = requests.request(metodo, API + ruta, json=datos, headers=cabeceras, timeout=420)
        cuerpo = respuesta.json()
        if respuesta.status_code >= 400:
            st.error(f"HTTP {respuesta.status_code}: {cuerpo.get('detail', 'No se pudo completar la solicitud')}")
            if respuesta.status_code == 401:
                st.session_state.pop("token", None)
            return None
        return cuerpo
    except (requests.RequestException, ValueError):
        st.error("No se pudo conectar con la API o terminó el tiempo de espera. Revisa la consola del servicio.")
        return None


with st.sidebar:
    st.header("Sesión")
    if not st.session_state.get("token"):
        with st.form("acceso"):
            correo = st.text_input("Correo", placeholder="cesar@finnorte.mx")
            clave = st.text_input("Contraseña", type="password")
            entrar = st.form_submit_button("Iniciar sesión", use_container_width=True)
            registrar = st.form_submit_button("Crear cuenta", use_container_width=True)
        if entrar or registrar:
            with st.spinner("Validando acceso…"):
                if registrar:
                    creado = llamar("POST", "/auth/registro", {"email": correo, "contrasena": clave})
                    if creado:
                        st.success("Cuenta creada. Inicia sesión con los mismos datos.")
                else:
                    resultado = llamar("POST", "/auth/login", {"email": correo, "contrasena": clave})
                    if resultado:
                        st.session_state.token = resultado["token"]
                        st.session_state.correo = correo
                        st.rerun()
    else:
        st.success("Sesión autenticada")
        st.caption(st.session_state.get("correo", ""))
        if st.button("Cerrar sesión"):
            for clave_estado in ("token", "correo", "resultado", "decision"):
                st.session_state.pop(clave_estado, None)
            st.rerun()
    st.divider()
    st.write("El código revisado se analiza sin ejecutarlo.")
    st.caption("Los informes se guardan únicamente tras aprobar los argumentos mostrados.")

if not st.session_state.get("token"):
    st.info("Crea una cuenta e inicia sesión en el panel izquierdo para revisar un ejemplo.")
    st.stop()

ejemplos = ("usuarios.py", "limites.py", "tokens.py", "reportes.py", "cuentas_api.py", "comisiones.py",
            "transferencias.py", "notificador.py")
elegido = st.selectbox("Ejemplo de código", ejemplos)
izquierda, derecha = st.columns([2, 1])
with izquierda:
    revisar = st.button("Revisar ejemplo", type="primary", use_container_width=True)
with derecha:
    preparar = st.button("Revisar y preparar informe", use_container_width=True)
nombre = st.text_input("Nombre del informe si decides guardarlo", value="revision_cesar.json",
                       help="Solo letras, números, guion y extensión .json. No se reemplazan informes existentes.")
with st.expander("Ver código de entrada"):
    archivo = Path(__file__).resolve().parents[1] / "datos" / "v2-revisor" / "codigo" / elegido
    st.code(archivo.read_text(encoding="utf-8"), language="python", line_numbers=True)

with st.expander("Comprobar un fallo de herramienta"):
    st.write("Solicita un ejemplo inexistente para verificar que el servicio detiene la revisión y muestra el error.")
    fallo = st.button("Probar archivo inexistente")

if revisar or preparar or fallo:
    tarea = f"Revisa {elegido} con correr_linter."
    if preparar:
        tarea += f" Después propone guardar_informe con el nombre {nombre}."
    if fallo:
        tarea = "Llama correr_linter con ruta inexistente.py. Necesito comprobar el fallo del archivo inexistente."
    st.session_state.pop("decision", None)
    with st.spinner("El agente está revisando la entrada. Espera a que termine…"):
        salida = llamar("POST", "/v1/agente", {"tarea": tarea})
        if salida is not None:
            st.session_state.resultado = salida

salida = st.session_state.get("resultado")
if salida:
    st.subheader("Resultado")
    st.write(salida["respuesta"])
    validacion = salida["validador"]
    if validacion["ok"]:
        st.success("Validador: aprobado · Referencias y respuesta dentro del alcance comprobado")
    else:
        st.error("Validador: bloqueado")
        for mensaje in validacion["hallazgos"]:
            st.write("• " + mensaje)
    for paso in salida["pasos"]:
        if paso["estado"] == "fallida":
            st.error(f"Herramienta fallida: {paso['herramienta']} · {paso['resultado']['clase']} · Sin revisión final")
        if paso["herramienta"] == "correr_linter" and paso["estado"] == "ejecutada":
            analisis = paso["resultado"]
            st.metric("Hallazgos de Ruff", len(analisis["hallazgos"]))
            if analisis["hallazgos"]:
                st.dataframe(analisis["hallazgos"], hide_index=True, use_container_width=True)
            else:
                st.info("Cero hallazgos en las reglas configuradas. No equivale a una auditoría completa.")
            with st.expander("Fuentes del corpus y huella de entrada", expanded=True):
                st.caption("SHA-256: " + analisis["huella"])
                for identificador, regla in analisis["reglas_citadas"].items():
                    st.write(f"**{identificador}** · {regla['fuente']}")
                    st.write(regla["texto"])
    with st.expander("Bitácora del agente", expanded=True):
        st.dataframe([{"Paso": p["n"], "Herramienta": p["herramienta"] or "respuesta",
                       "Estado": p["estado"], "Argumentos": str(p["argumentos"] or {})} for p in salida["pasos"]],
                     hide_index=True, use_container_width=True)
    if not st.session_state.get("decision"):
        for pendiente in salida.get("pendientes", []):
            st.warning("Informe pendiente: todavía no se ha creado ningún archivo.")
            st.json({"herramienta": pendiente["herramienta"], "argumentos": pendiente["argumentos"]})
            st.caption(f"La autorización caduca en {pendiente['expira_en_s']} segundos y tiene un solo uso.")
            aprobar_col, rechazar_col = st.columns(2)
            aprobar = aprobar_col.button("Aprobar y guardar", key="aprobar_" + pendiente["id"])
            rechazar = rechazar_col.button("Rechazar · no guardar", key="rechazar_" + pendiente["id"])
            if aprobar or rechazar:
                with st.spinner("Aplicando tu decisión…"):
                    decision = llamar("POST", "/v1/agente/confirmar/" + pendiente["id"], {"aprobar": aprobar})
                if decision:
                    st.session_state.decision = decision
                    st.rerun()
    if st.session_state.get("decision"):
        decision = st.session_state.decision
        if decision["estado"] == "rechazada":
            st.success("Acción rechazada · No se guardó ningún informe · Efecto: False")
        elif decision["estado"] == "ejecutada":
            st.success("Informe guardado con los argumentos aprobados.")
        else:
            st.error("La acción no se ejecutó: " + decision["estado"])
        st.json(decision)

st.divider()
st.caption("Ruff detecta patrones concretos. El validador comprueba referencias y respaldo; la revisión tiene un alcance limitado.")
