# VERSION CORREGIDA SIN ERRORES DE STRING
# (solo se ajustó el bloque que rompía el syntax)

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from streamlit_gsheets import GSheetsConnection

APP_TZ = "America/Mexico_City"
MEXICO_TZ = ZoneInfo(APP_TZ)

st.set_page_config(page_title="Quiniela Mundial 2026", layout="wide")

# ===============================
# CONEXIÓN
# ===============================
def get_conn():
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception:
        return None


def render_connection_help():
    st.error("No se pudo conectar con Google Sheets.")
    st.code(
        "# .streamlit/secrets.toml\n[connections.gsheets]\nspreadsheet = \"QUINIELA 2026 DB\"",
        language="toml",
    )

# ===============================
# UTILIDADES
# ===============================
def now_mx():
    return datetime.now(MEXICO_TZ)

# ===============================
# MAIN
# ===============================
def main():

    conn = get_conn()

    if conn is None:
        st.title("Quiniela Mundial 2026")
        render_connection_help()
        return

    st.title("✅ Conexión exitosa a Google Sheets")
    st.write("Tu app ya está conectada correctamente.")

    # PRUEBA DE LECTURA
    try:
        df = conn.read(worksheet="participantes", ttl=0)
        st.subheader("Lectura de hoja 'participantes'")
        st.dataframe(df)
    except Exception as e:
        st.error("Error leyendo hoja participantes")
        st.write(e)


if __name__ == "__main__":
    main()
