# ================================
# IMPORTS
# ================================
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# ================================
# CONFIG
# ================================
st.set_page_config(page_title="Quiniela Mundial 2026", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

SHEETS_READ_TTL = 30
SHEETS_REFRESH_COOLDOWN = 30

# ================================
# UTILS SHEETS
# ================================
def leer_worksheet(nombre):
    try:
        return conn.read(worksheet=nombre, ttl=SHEETS_READ_TTL).fillna("")
    except:
        return pd.DataFrame()

# ================================
# DB BASE
# ================================
def estructura_base():
    return {
        "configuracion": {},
        "participantes": {},
        "resultados_oficiales": {},
        "bonus": {}
    }

# ================================
# CARGA INICIAL
# ================================
def cargar_db():
    db = estructura_base()

    # CONFIG
    df = leer_worksheet("configuracion")
    for _, row in df.iterrows():
        db["configuracion"][row["clave"]] = row["valor"]

    # PARTICIPANTES
    df = leer_worksheet("participantes")
    for _, row in df.iterrows():
        db["participantes"][row["nombre"]] = {
            "clave": row["clave"],
            "favoritos_guardados": json.loads(row["favoritos_guardados_json"] or "[]")
        }

    # RESULTADOS
    df = leer_worksheet("resultados_oficiales")
    for _, row in df.iterrows():
        db["resultados_oficiales"][str(row["partido_id"])] = {
            "marcador_local": int(row["marcador_local"]),
            "marcador_visitante": int(row["marcador_visitante"])
        }

    return db

# ================================
# REFRESH CONTROLADO
# ================================
def refrescar_db():
    ahora = datetime.now()
    ultimo = st.session_state.get("ultimo_refresh")

    if ultimo and (ahora - ultimo).total_seconds() < SHEETS_REFRESH_COOLDOWN:
        return

    st.session_state.db = cargar_db()
    st.session_state.ultimo_refresh = ahora

# ================================
# PERSISTENCIA POR MÓDULO
# ================================
def persistir_db(modulo=None):
    try:
        if modulo == "participantes":
            filas = []
            for nombre, d in st.session_state.db["participantes"].items():
                filas.append({
                    "nombre": nombre,
                    "clave": d["clave"],
                    "favoritos_guardados_json": json.dumps(d["favoritos_guardados"]),
                    "fecha_envio": "",
                    "fecha_envio_iso": ""
                })
            conn.update(worksheet="participantes", data=pd.DataFrame(filas))

        elif modulo == "resultados":
            filas = []
            for pid, r in st.session_state.db["resultados_oficiales"].items():
                filas.append({
                    "partido_id": pid,
                    "marcador_local": r["marcador_local"],
                    "marcador_visitante": r["marcador_visitante"]
                })
            conn.update(worksheet="resultados_oficiales", data=pd.DataFrame(filas))

    except Exception as e:
        st.warning(f"Error al guardar {modulo}: {e}")

# ================================
# SESIÓN
# ================================
if "db" not in st.session_state:
    st.session_state.db = cargar_db()

# ================================
# UI INICIO
# ================================
st.title("⚽ Quiniela Mundial 2026")

# ================================
# CARD DE PUNTAJE (LO QUE PEDISTE)
# ================================
st.markdown("### 🏆 Sistema de puntuación")

st.markdown("""
<div style="
    background: linear-gradient(180deg, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0.45) 100%);
    padding: 18px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 6px 18px rgba(0,0,0,0.25);
">
    <p style="margin-bottom: 10px;">
        <b>Aciertas ganador o empate:</b> 
        <span style="color:#C9A227; font-weight:700;">1 punto</span>
    </p>
    <p style="margin-bottom: 10px;">
        <b>Aciertas marcador exacto:</b> 
        <span style="color:#C9A227; font-weight:700;">+2 puntos</span>
    </p>
    <p style="margin-bottom: 0;">
        <b>Total marcador exacto:</b> 
        <span style="color:#C9A227; font-weight:800;">3 puntos</span>
    </p>
</div>
""", unsafe_allow_html=True)

# ================================
# PARTICIPANTES
# ================================
st.markdown("### 👤 Participantes")

nombre = st.text_input("Nombre")
clave = st.text_input("Clave", type="password")

if st.button("Crear participante"):
    if nombre not in st.session_state.db["participantes"]:
        st.session_state.db["participantes"][nombre] = {
            "clave": clave,
            "favoritos_guardados": []
        }
        persistir_db("participantes")
        st.success("Participante creado")

# ================================
# RESULTADOS
# ================================
st.markdown("### 🏆 Resultados oficiales")

pid = st.text_input("Partido ID")
local = st.number_input("Local", 0)
visit = st.number_input("Visitante", 0)

if st.button("Guardar resultado"):
    st.session_state.db["resultados_oficiales"][pid] = {
        "marcador_local": local,
        "marcador_visitante": visit
    }
    persistir_db("resultados")
    st.success("Resultado guardado")
