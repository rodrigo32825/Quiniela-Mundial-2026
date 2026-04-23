# VERSION V5 OPTIMIZADA
# Cambios clave:
# - Fix logout (no crash)
# - Menos lecturas a Google Sheets
# - Sin recálculo automático innecesario
# - Cache más largo
# - Uso de nonce para control de refresh

import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("America/Mexico_City")

# ---------- INIT STATE ----------
def init_state():
    defaults = {
        "logged_in": False,
        "user_name": "",
        "is_admin": False,
        "nav": "INICIO",
        "data_nonce": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ---------- CONNECTION ----------
def get_conn():
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except:
        return None

# ---------- CACHE ----------
@st.cache_data(ttl=300)
def read_sheet(name):
    conn = get_conn()
    return conn.read(worksheet=name)

def clear_cache():
    read_sheet.clear()
    st.session_state.data_nonce += 1

# ---------- LOGIN ----------
def login(df):
    st.title("Quiniela 2026")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")

    if st.button("Entrar"):
        row = df[(df["nombre"] == u) & (df["clave"] == p)]
        if not row.empty:
            st.session_state.logged_in = True
            st.session_state.user_name = u
            st.session_state.is_admin = str(row.iloc[0]["es_admin"]) in ["1", "1.0", "True"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# ---------- SIDEBAR ----------
def sidebar():
    opciones = ["INICIO", "RESULTADOS", "TABLA", "BONUS"]
    if st.session_state.is_admin:
        opciones.insert(1, "ADMIN")

    sel = st.sidebar.radio("Menú", opciones)

    if st.sidebar.button("Cerrar sesión"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    return sel

# ---------- ADMIN ----------
def admin(df_part):
    st.header("ADMIN")

    nombre = st.text_input("Nuevo usuario")
    clave = st.text_input("Clave")

    if st.button("Crear"):
        nuevo = pd.DataFrame([[nombre, clave, "0"]], columns=["nombre","clave","es_admin"])
        df_part = pd.concat([df_part, nuevo])
        get_conn().update(worksheet="participantes", data=df_part)
        clear_cache()
        st.success("Usuario creado")

# ---------- MAIN ----------
def main():
    init_state()

    conn = get_conn()
    if not conn:
        st.error("No conexión")
        return

    df_part = read_sheet("participantes")

    if not st.session_state.logged_in:
        login(df_part)
        return

    nav = sidebar()

    if nav == "INICIO":
        st.title("Inicio")

    if nav == "ADMIN":
        admin(df_part)

    if nav == "RESULTADOS":
        st.title("Resultados")

    if nav == "TABLA":
        st.title("Tabla")

    if nav == "BONUS":
        st.title("Bonus")

if __name__ == "__main__":
    main()
