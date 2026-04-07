import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

MX_TZ = ZoneInfo("America/Mexico_City")

def ahora_mx():
    return datetime.now(MX_TZ)
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Quiniela Mundial FIFA 2026",
    page_icon="⚽",
    layout="wide"
)

# =========================================================
# DISEÑO / ASSETS
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


def first_existing_path(candidates):
    for path in candidates:
        if path and Path(path).exists():
            return str(path)
    return None


LOGO_PRINCIPAL = first_existing_path([
    ASSETS_DIR / "Logo mundial numerico.png",
    BASE_DIR / "Logo mundial numerico.png",
])

COLOR_DORADO = "#C9A227"
COLOR_VERDE = "#0B5E3C"
COLOR_VERDE_OSCURO = "#063A25"
COLOR_VERDE_LOGO = "#0A4F36"
COLOR_ROJO = "#C62828"
COLOR_BLANCO = "#FFFFFF"
COLOR_NEGRO = "#0A0A0A"
COLOR_NEGRO_2 = "#111111"
COLOR_NEGRO_3 = "#181818"
COLOR_BORDE_OSCURO = "#2A2A2A"
COLOR_TEXTO_OSCURO = "#111111"
COLOR_TEXTO_SECUNDARIO = "#555555"
COLOR_INPUT_BG = "rgba(255,255,255,0.94)"
COLOR_INPUT_BG_2 = "#F7F7F7"
COLOR_INPUT_BORDER = "rgba(255,255,255,0.50)"


def aplicar_estilo_global():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800&family=Roboto:wght@400;500;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Roboto', sans-serif;
        }}

        .stApp {{
            background:
                linear-gradient(135deg,
                    #071F18 0%,
                    #0E3B2E 38%,
                    #050505 100%
                );
            color: {COLOR_TEXTO_OSCURO};
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Montserrat', sans-serif !important;
            color: {COLOR_BLANCO} !important;
            letter-spacing: 0.3px;
            line-height: 1.20 !important;
            padding-top: 0.10rem !important;
            margin-top: 0 !important;
        }}

        .block-container {{
            padding-top: 2.6rem !important;
            padding-bottom: 2rem;
        }}

        section[data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg,
                    {COLOR_NEGRO} 0%,
                    {COLOR_NEGRO_2} 55%,
                    {COLOR_VERDE_OSCURO} 100%
                );
            border-right: 1px solid rgba(255,255,255,0.08);
        }}

        section[data-testid="stSidebar"] * {{
            color: {COLOR_BLANCO} !important;
        }}

        div[data-testid="stRadio"] > label,
        .stSelectbox label,
        .stTextInput label,
        .stNumberInput label,
        .stFileUploader label,
        .stCheckbox label {{
            font-weight: 700 !important;
            color: {COLOR_DORADO} !important;
        }}

        /* Inputs premium */
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {{
            background: {COLOR_INPUT_BG} !important;
            color: {COLOR_TEXTO_OSCURO} !important;
            border: 1px solid rgba(255,255,255,0.45) !important;
            border-radius: 14px !important;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;
        }}

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus {{
            border: 1px solid {COLOR_DORADO} !important;
            box-shadow: 0 0 0 1px rgba(201,162,39,0.30), 0 8px 20px rgba(0,0,0,0.10) !important;
        }}

        .stSelectbox div[data-baseweb="select"] > div {{
            background: {COLOR_INPUT_BG} !important;
            color: {COLOR_TEXTO_OSCURO} !important;
            border: 1px solid rgba(255,255,255,0.45) !important;
            border-radius: 14px !important;
            min-height: 46px !important;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;
        }}

        .stSelectbox div[data-baseweb="select"] span {{
            color: {COLOR_TEXTO_OSCURO} !important;
        }}

        .stButton > button {{
            background: linear-gradient(135deg, {COLOR_DORADO} 0%, #9f7d18 100%);
            color: #111111 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 800 !important;
            font-family: 'Montserrat', sans-serif !important;
            padding: 0.65rem 1rem !important;
            box-shadow: 0 4px 14px rgba(0,0,0,0.18);
        }}

        .stButton > button:hover {{
            transform: translateY(-1px);
            filter: brightness(1.03);
        }}

        .stButton > button:disabled {{
            background: #BBBBBB !important;
            color: #666666 !important;
        }}

        /* Tablas negras otra vez */
        div[data-testid="stDataFrame"] {{
            background: linear-gradient(180deg, {COLOR_NEGRO_2} 0%, {COLOR_NEGRO_3} 100%) !important;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            overflow: hidden;
        }}

        div[data-testid="stDataFrame"] * {{
            color: {COLOR_BLANCO} !important;
        }}

        div[data-testid="stMetric"] {{
            background: linear-gradient(180deg, {COLOR_NEGRO_2} 0%, {COLOR_NEGRO_3} 100%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 0.8rem;
        }}

        div[data-testid="stMetric"] * {{
            color: {COLOR_BLANCO} !important;
        }}

        div[data-testid="stAlert"] {{
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
        }}

        .quiniela-hero {{
            background:
                linear-gradient(135deg,
                    rgba(14,59,46,0.88) 0%,
                    rgba(10,18,14,0.94) 55%,
                    rgba(5,5,5,0.97) 100%);
            border: 1px solid rgba(255,255,255,0.55);
            border-radius: 26px;
            padding: 1.7rem 2rem 1.45rem 2rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 10px 24px rgba(0,0,0,0.10);
            text-align: center;
            backdrop-filter: blur(3px);
        }}

        .quiniela-hero-title {{
            font-family: 'Montserrat', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            color: {COLOR_BLANCO};
            margin-bottom: 0.35rem;
            line-height: 1.08;
            text-shadow: 0 1px 3px rgba(0,0,0,0.20);
        }}

        .quiniela-hero-subtitle {{
            font-size: 1rem;
            color: rgba(255,255,255,0.96);
            margin-bottom: 0;
            text-shadow: 0 1px 2px rgba(0,0,0,0.18);
        }}

        .quiniela-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.22);
            color: {COLOR_BLANCO};
            border: 1px solid rgba(255,255,255,0.40);
            border-radius: 999px;
            padding: 0.28rem 0.7rem;
            font-size: 0.83rem;
            font-weight: 700;
            margin-bottom: 0.7rem;
            text-shadow: 0 1px 2px rgba(0,0,0,0.16);
        }}

        .quiniela-divider {{
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.70), transparent);
            margin: 1rem 0 1.2rem 0;
        }}

        .texto-dorado {{
            color: {COLOR_DORADO};
            font-weight: 800;
        }}

        .texto-verde {{
            color: #0B8F5A;
            font-weight: 700;
        }}

        .texto-rojo {{
            color: #FF6B6B;
            font-weight: 700;
        }}

        .stMarkdown, .stCaption, .stText, p, li {{
            color: {COLOR_BLANCO};
        }}

        .stCaption {{
            color: rgba(255,255,255,0.92) !important;
        }}

        /* Data editor / table internals */
        table {{
            color: {COLOR_BLANCO} !important;
        }}

        thead tr th {{
            background-color: rgba(255,255,255,0.04) !important;
            color: {COLOR_BLANCO} !important;
        }}

        tbody tr td {{
            background-color: transparent !important;
            color: {COLOR_BLANCO} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


aplicar_estilo_global()

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
PUNTOS_RESULTADO = 1
PUNTOS_MARCADOR_EXACTO = 2

BONOS_FAVORITOS = {
    "Fase de grupos": 1,
    "Dieciseisavos": 2,
    "Octavos": 3,
    "Cuartos": 5,
    "Semifinal": 7,
    "Tercer lugar": 8,
    "Final": 10
}

ADMIN_USER = "admin"
ADMIN_PASSWORD = "quiniela2026"

DATA_FILE = "quiniela_data.json"
PARTIDOS_DIR = "data"
PARTIDOS_FILE = os.path.join(PARTIDOS_DIR, "partidos.csv")

COLUMNAS_PARTIDOS = [
    "id", "fase", "grupo", "fecha", "hora", "ciudad", "estadio", "local", "visitante"
]

FASES_LATE = {"Semifinal", "Tercer lugar", "Final"}

# =========================================================
# SESIÓN
# =========================================================
if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False

if "participante_actual" not in st.session_state:
    st.session_state.participante_actual = ""

if "participante_autenticado" not in st.session_state:
    st.session_state.participante_autenticado = False

if "panel_login_abierto" not in st.session_state:
    st.session_state.panel_login_abierto = False

if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "Inicio"

if "menu_sidebar_last" not in st.session_state:
    st.session_state.menu_sidebar_last = "Inicio"

# =========================================================
# UTILIDADES VISUALES
# =========================================================
def mostrar_logo_sidebar():
    if LOGO_PRINCIPAL:
        st.sidebar.image(LOGO_PRINCIPAL, use_container_width=True)

    st.sidebar.markdown(
        f"""
        <div style="margin-top: 0.35rem; margin-bottom: 0.9rem; text-align:center;">
            <div style="font-family: Montserrat, sans-serif; font-size: 1.15rem; font-weight: 800; color: {COLOR_BLANCO};">
                Quiniela Mundial 2026
            </div>
            <div style="font-size: 0.85rem; color: {COLOR_DORADO};">
                Edición especial FIFA
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def mostrar_encabezado_modulo(titulo, subtitulo=""):
    st.markdown(
        f"""
        <div class="quiniela-hero">
            <div class="quiniela-badge">UNITED STATES · CANADA · MÉXICO</div>
            <div class="quiniela-hero-title">{titulo}</div>
            {f'<p class="quiniela-hero-subtitle">{subtitulo}</p>' if subtitulo else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


def mostrar_divider():
    st.markdown('<div class="quiniela-divider"></div>', unsafe_allow_html=True)

# =========================================================
# UTILIDADES DE FECHA Y CALENDARIO
# =========================================================
def parsear_fecha_hora(fecha_texto: str, hora_texto: str):
    fecha_texto = str(fecha_texto).strip()
    hora_texto = str(hora_texto).strip()

    if not fecha_texto or not hora_texto:
        return None

    formatos = [
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M",
        "%d-%m-%Y %H:%M"
    ]

    for fmt in formatos:
        try:
            return datetime.strptime(f"{fecha_texto} {hora_texto}", fmt).replace(tzinfo=MX_TZ)
        except ValueError:
            continue

    return None


def asegurar_directorio_data():
    os.makedirs(PARTIDOS_DIR, exist_ok=True)


def crear_csv_vacio_calendario():
    asegurar_directorio_data()
    df_vacio = pd.DataFrame(columns=COLUMNAS_PARTIDOS)
    df_vacio.to_csv(PARTIDOS_FILE, index=False, encoding="utf-8-sig")


def validar_dataframe_partidos(df: pd.DataFrame):
    faltantes = [col for col in COLUMNAS_PARTIDOS if col not in df.columns]
    if faltantes:
        return False, f"Al CSV le faltan estas columnas: {', '.join(faltantes)}"

    df_validacion = df.copy()

    ids = pd.to_numeric(df_validacion["id"], errors="coerce")
    if ids.isna().any():
        return False, "La columna 'id' tiene valores no válidos."

    if ids.duplicated().any():
        return False, "La columna 'id' tiene valores duplicados dentro del archivo."

    for col in ["fase", "grupo", "fecha", "hora", "ciudad", "estadio", "local", "visitante"]:
        if df_validacion[col].astype(str).str.strip().eq("").any():
            return False, f"La columna '{col}' tiene celdas vacías."

    fechas_ok = df_validacion.apply(
        lambda row: parsear_fecha_hora(row["fecha"], row["hora"]) is not None,
        axis=1
    )
    if not fechas_ok.all():
        return False, "Hay filas con fecha u hora inválidas. Usa fecha dd/mm/yyyy y hora HH:MM."

    return True, "CSV válido."


def normalizar_dataframe_partidos(df: pd.DataFrame):
    df = df.copy().fillna("")

    for col in COLUMNAS_PARTIDOS:
        if col not in df.columns:
            df[col] = ""

    df = df[COLUMNAS_PARTIDOS].copy()

    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.dropna(subset=["id"]).copy()
    df["id"] = df["id"].astype(int)

    for col in ["fase", "grupo", "fecha", "hora", "ciudad", "estadio", "local", "visitante"]:
        df[col] = df[col].astype(str).str.strip()

    df["kickoff_dt"] = df.apply(
        lambda row: parsear_fecha_hora(row["fecha"], row["hora"]),
        axis=1
    )

    df["_sort"] = df["kickoff_dt"].apply(lambda x: x if x is not None else datetime.max)
    df = df.sort_values(by=["_sort", "id"]).drop(columns=["_sort"]).reset_index(drop=True)

    return df


def cargar_partidos_desde_csv():
    if not os.path.exists(PARTIDOS_FILE):
        return pd.DataFrame(columns=COLUMNAS_PARTIDOS + ["kickoff_dt"])

    try:
        df = pd.read_csv(PARTIDOS_FILE, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame(columns=COLUMNAS_PARTIDOS + ["kickoff_dt"])

    return normalizar_dataframe_partidos(df)


def guardar_dataframe_partidos(df: pd.DataFrame):
    asegurar_directorio_data()
    df_guardar = df[COLUMNAS_PARTIDOS].copy()
    df_guardar.to_csv(PARTIDOS_FILE, index=False, encoding="utf-8-sig")


def guardar_partidos_csv_reemplazo_total(uploaded_file):
    asegurar_directorio_data()

    try:
        df_nuevo = pd.read_csv(uploaded_file, dtype=str).fillna("")
    except Exception as e:
        return False, f"No se pudo leer el archivo CSV: {e}"

    ok, mensaje = validar_dataframe_partidos(df_nuevo)
    if not ok:
        return False, mensaje

    df_nuevo = normalizar_dataframe_partidos(df_nuevo)
    try:
        guardar_dataframe_partidos(df_nuevo)
    except PermissionError:
        return False, (
            "No se pudo guardar el archivo porque 'data/partidos.csv' está siendo usado por otro proceso. "
            "Cierra vistas previas del CSV, pausa OneDrive o reinicia Streamlit e inténtalo de nuevo."
        )
    except Exception as e:
        return False, f"No se pudo guardar el calendario: {e}"

    return True, f"Calendario reemplazado correctamente en {PARTIDOS_FILE}"


def guardar_partidos_csv_agregar_actualizar(uploaded_file):
    asegurar_directorio_data()

    try:
        df_nuevo = pd.read_csv(uploaded_file, dtype=str).fillna("")
    except Exception as e:
        return False, f"No se pudo leer el archivo CSV: {e}"

    ok, mensaje = validar_dataframe_partidos(df_nuevo)
    if not ok:
        return False, mensaje

    df_nuevo = normalizar_dataframe_partidos(df_nuevo)
    df_actual = cargar_partidos_desde_csv()

    if df_actual.empty:
        df_final = df_nuevo.copy()
    else:
        ids_nuevos = set(df_nuevo["id"].tolist())
        df_restante = df_actual[~df_actual["id"].isin(ids_nuevos)].copy()
        df_final = pd.concat([df_restante, df_nuevo], ignore_index=True)
        df_final = normalizar_dataframe_partidos(df_final)

    try:
        guardar_dataframe_partidos(df_final)
    except PermissionError:
        return False, (
            "No se pudo guardar el archivo porque 'data/partidos.csv' está siendo usado por otro proceso. "
            "Cierra vistas previas del CSV, pausa OneDrive o reinicia Streamlit e inténtalo de nuevo."
        )
    except Exception as e:
        return False, f"No se pudo guardar el calendario actualizado: {e}"

    return True, f"Calendario actualizado correctamente en {PARTIDOS_FILE}"


def obtener_fases_ordenadas(df_partidos: pd.DataFrame):
    if df_partidos.empty:
        return []

    fases = []
    for fase in df_partidos["fase"].tolist():
        if fase and fase not in fases:
            fases.append(fase)
    return fases


def obtener_grupos_fase(df_partidos: pd.DataFrame, fase: str):
    if df_partidos.empty:
        return []

    df_fase = df_partidos[df_partidos["fase"] == fase].copy()
    grupos = sorted(df_fase["grupo"].astype(str).str.strip().unique().tolist())
    return [g for g in grupos if g]


def construir_cierres_por_fase(df_partidos: pd.DataFrame):
    cierres = {}
    if df_partidos.empty:
        return cierres

    for fase in obtener_fases_ordenadas(df_partidos):
        partidos_fase = df_partidos[df_partidos["fase"] == fase].copy()
        fechas_validas = [x for x in partidos_fase["kickoff_dt"].tolist() if x is not None]
        if fechas_validas:
            cierres[fase] = min(fechas_validas)

    return cierres


def fase_bloqueada(fase: str, cierres_por_fase: dict):
    if fase not in cierres_por_fase:
        return False
    return ahora_mx() >= cierres_por_fase[fase]


def resumen_fases_cargadas(df_partidos: pd.DataFrame):
    if df_partidos.empty:
        return pd.DataFrame()

    filas = []
    for fase in obtener_fases_ordenadas(df_partidos):
        df_fase = df_partidos[df_partidos["fase"] == fase].copy()
        fechas_validas = [x for x in df_fase["kickoff_dt"].tolist() if x is not None]

        primer_partido = min(fechas_validas).strftime("%d/%m/%Y %H:%M") if fechas_validas else ""
        ultimo_partido = max(fechas_validas).strftime("%d/%m/%Y %H:%M") if fechas_validas else ""

        filas.append({
            "Fase": fase,
            "Partidos cargados": len(df_fase),
            "Primer partido": primer_partido,
            "Último partido": ultimo_partido
        })

    return pd.DataFrame(filas)

# =========================================================
# UTILIDADES DE ETAPAS / ENVÍOS
# =========================================================
def normalizar_nombre_etapa_envio(fase: str):
    fase = str(fase).strip()

    equivalencias = {
        "Fase de grupos": "Fase de grupos",
        "Dieciseisavos": "Dieciseisavos",
        "Diesciseisavos": "Dieciseisavos",
        "Octavos": "Octavos",
        "Cuartos": "Cuartos",
        "Semifinal": "Semifinal",
        "Tercer lugar": "3er/4to lugar",
        "3er/4to lugar": "3er/4to lugar",
        "Final": "Final",
    }

    return equivalencias.get(fase, fase)


def obtener_envio_fase(participante_data, fase):
    etapa = normalizar_nombre_etapa_envio(fase)
    envios = participante_data.get("envios_por_fase", {})
    return envios.get(etapa)


def construir_historial_envios_df(participante_data):
    envios = participante_data.get("envios_por_fase", {})
    if not envios:
        return pd.DataFrame()

    orden_etapas = [
        "Fase de grupos",
        "Dieciseisavos",
        "Octavos",
        "Cuartos",
        "Semifinal",
        "3er/4to lugar",
        "Final"
    ]

    filas = []
    for etapa in orden_etapas:
        info = envios.get(etapa)
        if info:
            filas.append({
                "Etapa": etapa,
                "Fecha de envío": info.get("fecha_envio", ""),
                "Grupo enviado": info.get("grupo", "") or ""
            })

    for etapa, info in envios.items():
        if etapa not in orden_etapas:
            filas.append({
                "Etapa": etapa,
                "Fecha de envío": info.get("fecha_envio", ""),
                "Grupo enviado": info.get("grupo", "") or ""
            })

    return pd.DataFrame(filas)

# =========================================================
# BONUS
# =========================================================
def bonus_base():
    return {
        "activo": False,
        "partido_id": None,
        "pregunta": "",
        "opciones": [],
        "puntos": 0,
        "fecha_apertura": None,
        "fecha_apertura_iso": None,
        "fecha_cierre": None,
        "fecha_cierre_iso": None,
        "respuesta_correcta": None,
        "respuestas_participantes": {},
        "historial": []
    }


def normalizar_bonus_data(bonus_data):
    base = bonus_base()
    if not isinstance(bonus_data, dict):
        return base
    for k, v in base.items():
        if k not in bonus_data:
            bonus_data[k] = v
    if not isinstance(bonus_data.get("opciones"), list):
        bonus_data["opciones"] = []
    if not isinstance(bonus_data.get("respuestas_participantes"), dict):
        bonus_data["respuestas_participantes"] = {}
    if not isinstance(bonus_data.get("historial"), list):
        bonus_data["historial"] = []
    return bonus_data


def obtener_bonus():
    if "bonus" not in st.session_state.db or not isinstance(st.session_state.db.get("bonus"), dict):
        st.session_state.db["bonus"] = bonus_base()
        persistir_db()
    else:
        st.session_state.db["bonus"] = normalizar_bonus_data(st.session_state.db["bonus"])
    return st.session_state.db["bonus"]


def bonus_esta_activo():
    bonus = obtener_bonus()
    return bool(bonus.get("activo")) and bonus.get("partido_id") is not None and not bonus.get("respuesta_correcta")


def obtener_partido_por_id(partido_id):
    if partidos.empty or partido_id in [None, ""]:
        return None
    df = partidos[partidos["id"] == int(partido_id)]
    if df.empty:
        return None
    return df.iloc[0]


def bonus_cerrado_por_hora():
    bonus = obtener_bonus()
    partido = obtener_partido_por_id(bonus.get("partido_id"))
    if partido is None:
        return False
    kickoff = partido.get("kickoff_dt")
    if kickoff is None:
        return False
    return ahora_mx() >= kickoff


def activar_bonus(partido_id, pregunta, opciones, puntos):
    bonus = obtener_bonus()
    ahora = ahora_mx()
    bonus.update({
        "activo": True,
        "partido_id": int(partido_id),
        "pregunta": str(pregunta).strip(),
        "opciones": [str(x).strip() for x in opciones if str(x).strip()],
        "puntos": int(puntos),
        "fecha_apertura": ahora.strftime("%d/%m/%Y %H:%M"),
        "fecha_apertura_iso": ahora.isoformat(),
        "fecha_cierre": None,
        "fecha_cierre_iso": None,
        "respuesta_correcta": None,
        "respuestas_participantes": {},
    })
    persistir_db()


def cerrar_bonus_por_hora_si_aplica():
    bonus = obtener_bonus()
    if bonus.get("activo") and not bonus.get("fecha_cierre") and bonus_cerrado_por_hora():
        ahora = ahora_mx()
        bonus["fecha_cierre"] = ahora.strftime("%d/%m/%Y %H:%M")
        bonus["fecha_cierre_iso"] = ahora.isoformat()
        persistir_db()


def guardar_respuesta_bonus(participante, respuesta):
    bonus = obtener_bonus()
    if not bonus_esta_activo() or bonus_cerrado_por_hora():
        return False, "El bonus ya está cerrado."
    if participante in bonus["respuestas_participantes"]:
        return False, "Tu respuesta bonus ya fue registrada y no se puede cambiar."
    if respuesta not in bonus.get("opciones", []):
        return False, "Debes seleccionar una respuesta válida."

    ahora = ahora_mx()
    bonus["respuestas_participantes"][participante] = {
        "respuesta": respuesta,
        "fecha_respuesta": ahora.strftime("%d/%m/%Y %H:%M"),
        "fecha_respuesta_iso": ahora.isoformat()
    }
    persistir_db()
    return True, "Respuesta bonus guardada correctamente."


def resolver_bonus(respuesta_correcta):
    bonus = obtener_bonus()
    if not bonus.get("activo"):
        return False, "No hay un bonus activo para resolver."
    if respuesta_correcta not in bonus.get("opciones", []):
        return False, "Debes elegir una respuesta correcta válida."

    cerrar_bonus_por_hora_si_aplica()

    partido = obtener_partido_por_id(bonus.get("partido_id"))
    registro = {
        "partido_id": bonus.get("partido_id"),
        "partido": f"{partido['local']} vs {partido['visitante']}" if partido is not None else "",
        "fase": partido["fase"] if partido is not None else "",
        "grupo": partido["grupo"] if partido is not None else "",
        "pregunta": bonus.get("pregunta", ""),
        "opciones": bonus.get("opciones", []),
        "puntos": int(bonus.get("puntos", 0)),
        "fecha_apertura": bonus.get("fecha_apertura"),
        "fecha_cierre": bonus.get("fecha_cierre") or ahora_mx().strftime("%d/%m/%Y %H:%M"),
        "respuesta_correcta": respuesta_correcta,
        "respuestas_participantes": bonus.get("respuestas_participantes", {}),
        "ganadores": []
    }

    for participante, datos in bonus.get("respuestas_participantes", {}).items():
        if datos.get("respuesta") == respuesta_correcta:
            registro["ganadores"].append({
                "participante": participante,
                "puntos_ganados": int(bonus.get("puntos", 0))
            })

    bonus["historial"].append(registro)

    historial = bonus["historial"]
    st.session_state.db["bonus"] = bonus_base()
    st.session_state.db["bonus"]["historial"] = historial
    persistir_db()
    return True, "Bonus resuelto correctamente."


def construir_respuestas_bonus_df():
    bonus = obtener_bonus()
    filas = []
    for participante, datos in sorted(bonus.get("respuestas_participantes", {}).items()):
        filas.append({
            "Participante": participante,
            "Respuesta seleccionada": datos.get("respuesta", ""),
            "Fecha y hora": datos.get("fecha_respuesta", ""),
            "Bloqueada": "Sí"
        })
    return pd.DataFrame(filas)


def construir_historial_bonus_acumulado_df():
    bonus = obtener_bonus()
    acumulado = {}
    for item in bonus.get("historial", []):
        for ganador in item.get("ganadores", []):
            nombre = ganador.get("participante", "")
            acumulado[nombre] = acumulado.get(nombre, 0) + int(ganador.get("puntos_ganados", 0))

    filas = []
    participantes = sorted(obtener_participantes().keys())
    for nombre in participantes:
        filas.append({
            "Participante": nombre,
            "Puntos bonus acumulados": acumulado.get(nombre, 0)
        })

    if not filas:
        return pd.DataFrame()

    filas = sorted(filas, key=lambda x: (-x["Puntos bonus acumulados"], x["Participante"].lower()))
    return pd.DataFrame(filas)


def construir_partidos_bonus_selector():
    if partidos.empty:
        return []
    opciones = []
    for _, p in partidos.iterrows():
        opciones.append({
            "label": f"ID {int(p['id'])} · {p['local']} vs {p['visitante']} · {p['fase']} · Grupo {p['grupo']} · {p['fecha']} {p['hora']}",
            "id": int(p["id"])
        })
    return opciones

# =========================================================
# BASE DE DATOS JSON
# =========================================================
def estructura_base():
    return {
        "configuracion": {
            "mostrar_pronosticos_publicos": False
        },
        "participantes": {},
        "resultados_oficiales": {},
        "bonus": bonus_base()
    }


def participante_base(clave=""):
    return {
        "clave": clave,
        "favoritos_guardados": [],
        "pronosticos_guardados": [],
        "fecha_envio": None,
        "fecha_envio_iso": None,
        "envios_por_fase": {}
    }


def cargar_db():
    if not os.path.exists(DATA_FILE):
        return estructura_base()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
    except Exception:
        return estructura_base()

    if "configuracion" not in db or not isinstance(db["configuracion"], dict):
        db["configuracion"] = {"mostrar_pronosticos_publicos": False}

    if "mostrar_pronosticos_publicos" not in db["configuracion"]:
        db["configuracion"]["mostrar_pronosticos_publicos"] = False

    if "participantes" not in db:
        db["participantes"] = {}

    if "resultados_oficiales" not in db:
        db["resultados_oficiales"] = {}

    if "bonus" not in db:
        db["bonus"] = bonus_base()
    else:
        db["bonus"] = normalizar_bonus_data(db["bonus"])

    for _, datos in db["participantes"].items():
        if "clave" not in datos:
            datos["clave"] = ""
        if "favoritos_guardados" not in datos:
            datos["favoritos_guardados"] = []
        if "pronosticos_guardados" not in datos:
            datos["pronosticos_guardados"] = []
        if "fecha_envio" not in datos:
            datos["fecha_envio"] = None
        if "fecha_envio_iso" not in datos:
            datos["fecha_envio_iso"] = None
        if "envios_por_fase" not in datos or not isinstance(datos["envios_por_fase"], dict):
            datos["envios_por_fase"] = {}

    return db


def persistir_db():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=2)


if "db" not in st.session_state:
    st.session_state.db = cargar_db()


def obtener_participantes():
    return st.session_state.db["participantes"]


def obtener_resultados_oficiales():
    return st.session_state.db["resultados_oficiales"]


def obtener_configuracion():
    return st.session_state.db["configuracion"]


def pronosticos_publicos_habilitados():
    return bool(obtener_configuracion().get("mostrar_pronosticos_publicos", False))


def usuario_puede_ver_detalle_participante(nombre_participante: str):
    if st.session_state.admin_autenticado:
        return True
    if pronosticos_publicos_habilitados():
        return True
    if st.session_state.participante_autenticado and st.session_state.participante_actual == nombre_participante:
        return True
    return False


def seleccion_es_participante_ajeno(nombre_participante: str):
    if st.session_state.admin_autenticado:
        return False
    if not st.session_state.participante_autenticado:
        return True
    return st.session_state.participante_actual != nombre_participante

# =========================================================
# RESETEOS Y LIMPIEZA
# =========================================================
def borrar_archivo_calendario():
    try:
        if os.path.exists(PARTIDOS_FILE):
            os.remove(PARTIDOS_FILE)
            return True, "Calendario eliminado correctamente."
        return False, "No existe un calendario cargado actualmente."
    except PermissionError:
        try:
            crear_csv_vacio_calendario()
            return True, (
                "El archivo estaba en uso y no se pudo borrar físicamente, "
                "pero se reemplazó por un calendario vacío correctamente."
            )
        except Exception as e:
            return False, f"No se pudo borrar ni vaciar el calendario: {e}"
    except Exception as e:
        return False, f"No se pudo eliminar el calendario: {e}"


def limpiar_resultados_oficiales():
    st.session_state.db["resultados_oficiales"] = {}
    persistir_db()
    return True, "Resultados oficiales eliminados correctamente."


def reset_total_prueba():
    st.session_state.db = estructura_base()
    persistir_db()

    try:
        if os.path.exists(PARTIDOS_FILE):
            os.remove(PARTIDOS_FILE)
    except PermissionError:
        crear_csv_vacio_calendario()
    except Exception:
        crear_csv_vacio_calendario()

    st.session_state.admin_autenticado = True
    st.session_state.participante_actual = ""
    st.session_state.participante_autenticado = False

    return True, "Reset total de prueba ejecutado correctamente."

# =========================================================
# PARTIDOS Y CIERRES
# =========================================================
partidos = cargar_partidos_desde_csv()
fases_ordenadas = obtener_fases_ordenadas(partidos)
cierres_por_fase = construir_cierres_por_fase(partidos)
equipos = sorted(set(partidos["local"]).union(set(partidos["visitante"]))) if not partidos.empty else []

FECHA_LIMITE_FAVORITOS = None
if fases_ordenadas:
    primera_fase = fases_ordenadas[0]
    FECHA_LIMITE_FAVORITOS = cierres_por_fase.get(primera_fase)

# =========================================================
# FUNCIONES DE PARTICIPANTES
# =========================================================
def autenticar_admin(usuario, clave):
    return usuario == ADMIN_USER and clave == ADMIN_PASSWORD


def autenticar_participante(nombre, clave):
    participantes = obtener_participantes()
    if nombre in participantes:
        return participantes[nombre].get("clave", "") == clave
    return False


def cerrar_sesion_participante():
    st.session_state.participante_actual = ""
    st.session_state.participante_autenticado = False


def obtener_participante_actual():
    participantes = obtener_participantes()
    nombre = st.session_state.participante_actual
    if not nombre or nombre not in participantes:
        return None
    return participantes[nombre]


def crear_participante(nombre, clave):
    participantes = obtener_participantes()

    nombre = nombre.strip()
    clave = clave.strip()

    if not nombre:
        return False, "Debes capturar el nombre del participante."

    if not clave:
        return False, "Debes capturar una clave."

    if nombre in participantes:
        return False, "Ese participante ya existe."

    participantes[nombre] = participante_base(clave=clave)
    persistir_db()
    return True, f"Participante '{nombre}' creado correctamente."


def eliminar_participante(nombre):
    participantes = obtener_participantes()

    if nombre not in participantes:
        return False, "El participante no existe."

    del participantes[nombre]

    if st.session_state.participante_actual == nombre:
        cerrar_sesion_participante()

    persistir_db()
    return True, f"Participante '{nombre}' eliminado correctamente."


def cambiar_clave_participante(nombre, nueva_clave):
    participantes = obtener_participantes()

    if nombre not in participantes:
        return False, "El participante no existe."

    if not nueva_clave.strip():
        return False, "La nueva clave no puede estar vacía."

    participantes[nombre]["clave"] = nueva_clave.strip()
    persistir_db()
    return True, f"Clave actualizada para '{nombre}'."


def renombrar_participante(nombre_actual, nuevo_nombre):
    participantes = obtener_participantes()

    if nombre_actual not in participantes:
        return False, "El participante no existe."

    nuevo_nombre = nuevo_nombre.strip()

    if not nuevo_nombre:
        return False, "El nuevo nombre no puede estar vacío."

    if nuevo_nombre != nombre_actual and nuevo_nombre in participantes:
        return False, "Ya existe otro participante con ese nombre."

    datos = participantes[nombre_actual]
    del participantes[nombre_actual]
    participantes[nuevo_nombre] = datos

    if st.session_state.participante_actual == nombre_actual:
        st.session_state.participante_actual = nuevo_nombre

    persistir_db()
    return True, f"Participante renombrado a '{nuevo_nombre}'."

# =========================================================
# FUNCIONES DE PRONÓSTICOS Y RESULTADOS
# =========================================================
def obtener_resultado_partido(goles_local, goles_visitante):
    if goles_local > goles_visitante:
        return "local"
    if goles_local < goles_visitante:
        return "visitante"
    return "empate"


def calcular_puntos_partido(pronostico, resultado_oficial):
    puntos = 0

    resultado_pronosticado = obtener_resultado_partido(
        pronostico["marcador_local"],
        pronostico["marcador_visitante"]
    )

    resultado_real = obtener_resultado_partido(
        resultado_oficial["marcador_local"],
        resultado_oficial["marcador_visitante"]
    )

    acierto_resultado = resultado_pronosticado == resultado_real
    acierto_exacto = (
        pronostico["marcador_local"] == resultado_oficial["marcador_local"]
        and pronostico["marcador_visitante"] == resultado_oficial["marcador_visitante"]
    )

    if acierto_resultado:
        puntos += PUNTOS_RESULTADO

    if acierto_exacto:
        puntos += PUNTOS_MARCADOR_EXACTO

    return puntos, acierto_resultado, acierto_exacto


def guardar_resultado_oficial(partido_id, marcador_local, marcador_visitante):
    resultados = obtener_resultados_oficiales()
    resultados[str(partido_id)] = {
        "marcador_local": int(marcador_local),
        "marcador_visitante": int(marcador_visitante)
    }
    persistir_db()


def obtener_resultado_oficial(partido_id):
    resultados = obtener_resultados_oficiales()
    return resultados.get(str(partido_id))


def favoritos_bloqueados():
    if FECHA_LIMITE_FAVORITOS is None:
        return False
    return ahora_mx() >= FECHA_LIMITE_FAVORITOS


def obtener_pronostico_existente(participante_data, partido_id):
    return next(
        (x for x in participante_data["pronosticos_guardados"] if int(x["id"]) == int(partido_id)),
        None
    )


def guardar_pronosticos_fase(participante_data, pronosticos_fase):
    actuales = participante_data["pronosticos_guardados"]
    restantes = [x for x in actuales if int(x["id"]) not in {int(p["id"]) for p in pronosticos_fase}]
    participante_data["pronosticos_guardados"] = restantes + pronosticos_fase
    participante_data["pronosticos_guardados"] = sorted(
        participante_data["pronosticos_guardados"],
        key=lambda x: int(x["id"])
    )
    persistir_db()


def guardar_envio_oficial(participante_data, pronosticos_fase, fase, grupo=None):
    guardar_pronosticos_fase(participante_data, pronosticos_fase)

    ahora = ahora_mx()
    etapa_envio = normalizar_nombre_etapa_envio(fase)

    participante_data["envios_por_fase"][etapa_envio] = {
        "fecha_envio": ahora.strftime("%d/%m/%Y %H:%M"),
        "fecha_envio_iso": ahora.isoformat(),
        "grupo": grupo if etapa_envio == "Fase de grupos" else ""
    }

    participante_data["fecha_envio"] = ahora.strftime("%d/%m/%Y %H:%M")
    participante_data["fecha_envio_iso"] = ahora.isoformat()

    persistir_db()

# =========================================================
# FAVORITOS, PUNTOS Y TABLA GENERAL
# =========================================================
def equipo_sigue_vivo(equipo, df_partidos, resultados):
    partidos_equipo = df_partidos[
        (df_partidos["local"] == equipo) | (df_partidos["visitante"] == equipo)
    ].copy()

    if partidos_equipo.empty:
        return False

    partidos_equipo = partidos_equipo.sort_values(by=["kickoff_dt", "id"])

    ultimo_partido_resuelto = None
    for _, partido in partidos_equipo.iterrows():
        resultado = resultados.get(str(partido["id"]))
        if resultado:
            ultimo_partido_resuelto = (partido, resultado)

    if ultimo_partido_resuelto is None:
        return True

    partido, resultado = ultimo_partido_resuelto
    marcador_local = int(resultado["marcador_local"])
    marcador_visitante = int(resultado["marcador_visitante"])

    if marcador_local == marcador_visitante:
        return True

    if partido["local"] == equipo and marcador_local > marcador_visitante:
        return True

    if partido["visitante"] == equipo and marcador_visitante > marcador_local:
        return True

    if partido["fase"] == "Fase de grupos":
        return True

    return False


def calcular_puntos_favoritos_por_equipo(participante_data):
    puntos_por_equipo = {}
    resultados = obtener_resultados_oficiales()

    for favorito in participante_data["favoritos_guardados"]:
        puntos_por_equipo[favorito] = 0

    if not participante_data["favoritos_guardados"]:
        return puntos_por_equipo

    for _, partido in partidos.iterrows():
        partido_id = str(partido["id"])

        if partido_id not in resultados:
            continue

        resultado = resultados[partido_id]
        fase = partido["fase"]
        bono_fase = BONOS_FAVORITOS.get(fase, 0)

        ganador = obtener_resultado_partido(
            int(resultado["marcador_local"]),
            int(resultado["marcador_visitante"])
        )

        for favorito in participante_data["favoritos_guardados"]:
            if favorito == partido["local"] and ganador == "local":
                puntos_por_equipo[favorito] += bono_fase
            elif favorito == partido["visitante"] and ganador == "visitante":
                puntos_por_equipo[favorito] += bono_fase

    return puntos_por_equipo


def calcular_bonus_favoritos_desglosado(participante_data):
    favoritos = participante_data.get("favoritos_guardados", [])
    resultados = obtener_resultados_oficiales()

    columnas_fases = [
        ("Fase de grupos", "Fase de Grupos"),
        ("Dieciseisavos", "16vos"),
        ("Octavos", "8vos"),
        ("Cuartos", "4tos"),
        ("Semifinal", "Semifinal"),
        ("Tercer lugar", "3er/4to lugar"),
        ("Final", "Final"),
    ]

    detalle = {}
    for favorito in favoritos:
        detalle[favorito] = {visible: 0 for _, visible in columnas_fases}

    for _, partido in partidos.iterrows():
        partido_id = str(partido["id"])
        if partido_id not in resultados:
            continue

        resultado = resultados[partido_id]
        fase_real = partido["fase"]
        ganador = obtener_resultado_partido(
            int(resultado["marcador_local"]),
            int(resultado["marcador_visitante"])
        )

        bono_fase = BONOS_FAVORITOS.get(fase_real, 0)

        for fase_codigo, fase_visible in columnas_fases:
            if fase_real != fase_codigo:
                continue

            for favorito in favoritos:
                if favorito == partido["local"] and ganador == "local":
                    detalle[favorito][fase_visible] += bono_fase
                elif favorito == partido["visitante"] and ganador == "visitante":
                    detalle[favorito][fase_visible] += bono_fase

    return detalle


def construir_tabla_favoritos_participante(participante_data):
    favoritos = participante_data.get("favoritos_guardados", [])
    if not favoritos:
        return pd.DataFrame()

    desglose = calcular_bonus_favoritos_desglosado(participante_data)

    filas = []
    for favorito in favoritos:
        fila = {
            "Favoritos": favorito,
            "Fase de Grupos": desglose[favorito]["Fase de Grupos"],
            "16vos": desglose[favorito]["16vos"],
            "8vos": desglose[favorito]["8vos"],
            "4tos": desglose[favorito]["4tos"],
            "Semifinal": desglose[favorito]["Semifinal"],
            "3er/4to lugar": desglose[favorito]["3er/4to lugar"],
            "Final": desglose[favorito]["Final"],
        }
        filas.append(fila)

    return pd.DataFrame(filas)


def construir_tabla_pronosticos_participante(nombre_participante, participante_data):
    if partidos.empty:
        return pd.DataFrame()

    pronosticos_dict = {
        int(p["id"]): p for p in participante_data.get("pronosticos_guardados", [])
    }
    resultados = obtener_resultados_oficiales()

    filas = []
    for _, p in partidos.iterrows():
        pronostico = pronosticos_dict.get(int(p["id"]))
        resultado = resultados.get(str(p["id"]))

        marcador_local = pronostico["marcador_local"] if pronostico else ""
        marcador_visitante = pronostico["marcador_visitante"] if pronostico else ""

        puntos_partido = ""
        if pronostico and resultado:
            puntos_partido, _, _ = calcular_puntos_partido(pronostico, resultado)

        filas.append({
            "Sede": p["ciudad"],
            "Fase": p["fase"],
            "Grupo": p["grupo"],
            "Fecha": p["fecha"],
            "Hora": p["hora"],
            "Local": p["local"],
            "Marcador local": marcador_local,
            "Marcador visitante": marcador_visitante,
            "Visitante": p["visitante"],
            "Puntos ganados": puntos_partido
        })

    return pd.DataFrame(filas)


def estadisticas_participante(nombre, participante_data):
    resultados = obtener_resultados_oficiales()

    total_puntos_base = 0
    exact_hits = 0
    result_hits = 0
    knockout_points = 0
    late_stage_points = 0

    for pronostico in participante_data["pronosticos_guardados"]:
        resultado = resultados.get(str(pronostico["id"]))
        if not resultado:
            continue

        puntos, acierto_resultado, acierto_exacto = calcular_puntos_partido(pronostico, resultado)
        total_puntos_base += puntos
        result_hits += int(acierto_resultado)
        exact_hits += int(acierto_exacto)

        partido_info = partidos[partidos["id"] == int(pronostico["id"])]
        if not partido_info.empty:
            fase = partido_info.iloc[0]["fase"]
            if fase != "Fase de grupos":
                knockout_points += puntos
            if fase in FASES_LATE:
                late_stage_points += puntos

    puntos_favoritos = calcular_puntos_favoritos_por_equipo(participante_data)
    bonus_favoritos = sum(puntos_favoritos.values())
    total_general = total_puntos_base + bonus_favoritos

    fecha_envio_iso = participante_data.get("fecha_envio_iso") or ""
    fecha_envio_dt = None
    if fecha_envio_iso:
        try:
            fecha_envio_dt = datetime.fromisoformat(fecha_envio_iso)
            if fecha_envio_dt.tzinfo is None:
                fecha_envio_dt = fecha_envio_dt.replace(tzinfo=MX_TZ)
            else:
                fecha_envio_dt = fecha_envio_dt.astimezone(MX_TZ)
        except ValueError:
            fecha_envio_dt = None

    if fecha_envio_dt is None:
        fecha_envio_dt = datetime.max.replace(tzinfo=MX_TZ)

    return {
        "Participante": nombre,
        "Puntos base": total_puntos_base,
        "Bonus favoritos": bonus_favoritos,
        "Marcadores exactos": exact_hits,
        "Aciertos de resultado": result_hits,
        "Puntos eliminación directa": knockout_points,
        "Puntos fases finales": late_stage_points,
        "Puntos ganados": total_general,
        "_fecha_envio_dt": fecha_envio_dt
    }


def construir_tabla_general():
    participantes = obtener_participantes()
    filas = []

    for nombre, participante_data in participantes.items():
        stats = estadisticas_participante(nombre, participante_data)
        filas.append({
            "Participante": str(stats["Participante"]),
            "Puntos Base ganados": int(stats["Puntos base"]),
            "Puntos por favoitos": int(stats["Bonus favoritos"]),
            "Total Puntos ganados": int(stats["Puntos ganados"]),
            "_desempate_exactos": int(stats["Marcadores exactos"]),
            "_desempate_resultados": int(stats["Aciertos de resultado"]),
            "_desempate_eliminacion": int(stats["Puntos eliminación directa"]),
            "_desempate_fases_finales": int(stats["Puntos fases finales"]),
            "_desempate_fecha": stats["_fecha_envio_dt"],
        })

    if not filas:
        return pd.DataFrame()

    filas_ordenadas = sorted(
        filas,
        key=lambda x: (
            -x["Total Puntos ganados"],
            -x["_desempate_exactos"],
            -x["_desempate_resultados"],
            -x["_desempate_eliminacion"],
            -x["_desempate_fases_finales"],
            x["_desempate_fecha"],
            x["Participante"].lower()
        )
    )

    tabla_df = pd.DataFrame(filas_ordenadas).reset_index(drop=True)
    tabla_df.insert(0, "Posición", range(1, len(tabla_df) + 1))

    columnas_visibles = [
        "Posición",
        "Participante",
        "Puntos Base ganados",
        "Puntos por favoitos",
        "Total Puntos ganados"
    ]

    return tabla_df[columnas_visibles]


def construir_bonus_favoritos_admin():
    resultados = obtener_resultados_oficiales()
    filas = []

    for _, partido in partidos.iterrows():
        partido_id = str(partido["id"])

        if partido_id not in resultados:
            continue

        resultado = resultados[partido_id]
        fase = partido["fase"]
        bono_fase = BONOS_FAVORITOS.get(fase, 0)

        ganador = obtener_resultado_partido(
            int(resultado["marcador_local"]),
            int(resultado["marcador_visitante"])
        )

        if ganador == "local":
            equipo_ganador = partido["local"]
        elif ganador == "visitante":
            equipo_ganador = partido["visitante"]
        else:
            equipo_ganador = "Empate"

        if equipo_ganador != "Empate":
            filas.append({
                "Fase": fase,
                "Equipo favorito que suma": equipo_ganador,
                "Partidos ganados en la fase": 1,
                "Puntos por victoria": bono_fase,
                "Puntos totales otorgados": bono_fase
            })

    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(filas)
    df = (
        df.groupby(["Fase", "Equipo favorito que suma", "Puntos por victoria"], as_index=False)
        .agg({
            "Partidos ganados en la fase": "sum",
            "Puntos totales otorgados": "sum"
        })
    )

    return df

# =========================================================
# VISTAS AUXILIARES
# =========================================================
def construir_calendario_df():
    if partidos.empty:
        return pd.DataFrame()

    return partidos[[
        "id", "fase", "grupo", "fecha", "hora", "ciudad", "estadio", "local", "visitante"
    ]].rename(columns={
        "id": "ID",
        "fase": "Fase",
        "grupo": "Grupo",
        "fecha": "Fecha",
        "hora": "Hora",
        "ciudad": "Ciudad",
        "estadio": "Estadio",
        "local": "Local",
        "visitante": "Visitante"
    })



def obtener_ids_partidos_fase(df_partidos, fase):
    if df_partidos.empty:
        return set()
    return set(df_partidos[df_partidos["fase"] == fase]["id"].astype(int).tolist())


def obtener_ids_pronosticados_fase(participante_data, fase):
    ids_fase = obtener_ids_partidos_fase(partidos, fase)
    return {int(p["id"]) for p in participante_data.get("pronosticos_guardados", []) if int(p["id"]) in ids_fase}


def contar_avance_fase(participante_data, fase):
    ids_fase = obtener_ids_partidos_fase(partidos, fase)
    ids_pronosticados = obtener_ids_pronosticados_fase(participante_data, fase)
    return len(ids_pronosticados), len(ids_fase)


def fase_completa_para_envio(participante_data, fase):
    capturados, total = contar_avance_fase(participante_data, fase)
    return total > 0 and capturados == total


def resetear_borrador_fase_actual(participante_data, fase):
    ids_fase = obtener_ids_partidos_fase(partidos, fase)
    participante_data["pronosticos_guardados"] = [
        p for p in participante_data.get("pronosticos_guardados", [])
        if int(p["id"]) not in ids_fase
    ]
    etapa_envio = normalizar_nombre_etapa_envio(fase)
    if etapa_envio in participante_data.get("envios_por_fase", {}):
        del participante_data["envios_por_fase"][etapa_envio]
    persistir_db()


def equipo_sigue_activo_por_fases_posteriores(equipo, df_partidos, resultados):
    partidos_equipo = df_partidos[(df_partidos["local"] == equipo) | (df_partidos["visitante"] == equipo)].copy()
    if partidos_equipo.empty:
        return False

    partidos_equipo = partidos_equipo.sort_values(by=["kickoff_dt", "id"]).reset_index(drop=True)

    indices_resueltos = []
    for _, partido in partidos_equipo.iterrows():
        if resultados.get(str(partido["id"])):
            try:
                indices_resueltos.append(fases_ordenadas.index(partido["fase"]))
            except ValueError:
                continue

    if not indices_resueltos:
        return True

    ultimo_indice = max(indices_resueltos)

    for _, partido in partidos_equipo.iterrows():
        try:
            indice_fase = fases_ordenadas.index(partido["fase"])
        except ValueError:
            continue
        if indice_fase > ultimo_indice:
            return True
        if indice_fase == ultimo_indice and not resultados.get(str(partido["id"])):
            return True

    return False

def construir_resumen_pronosticos(pronosticos_base):
    filas = []

    for pronostico in pronosticos_base:
        partido_info = partidos[partidos["id"] == int(pronostico["id"])]
        if partido_info.empty:
            continue

        partido_info = partido_info.iloc[0]

        filas.append({
            "Sede": partido_info["ciudad"],
            "Fase": partido_info["fase"],
            "Grupo": partido_info["grupo"],
            "Fecha": partido_info["fecha"],
            "Hora": partido_info["hora"],
            "Local": partido_info["local"],
            "Marcador local": pronostico["marcador_local"],
            "Marcador visitante": pronostico["marcador_visitante"],
            "Visitante": partido_info["visitante"]
        })

    return pd.DataFrame(filas)



def mostrar_favoritos_participante(participante_data):
    st.markdown("### Tus equipos favoritos")
    puntos_favoritos = calcular_puntos_favoritos_por_equipo(participante_data)
    resultados = obtener_resultados_oficiales()

    for equipo in participante_data["favoritos_guardados"]:
        vivo = equipo_sigue_activo_por_fases_posteriores(equipo, partidos, resultados)
        estado = "Activo" if vivo else "Eliminado"
        clase_estado = "texto-verde" if vivo else "texto-rojo"

        col1, col2, col3 = st.columns([4, 1, 1])
        col1.markdown(f"• <span class='texto-dorado'>{equipo}</span>", unsafe_allow_html=True)
        col2.markdown(f"<span class='texto-dorado'><b>{puntos_favoritos.get(equipo, 0)} pts</b></span>", unsafe_allow_html=True)
        col3.markdown(f"<span class='{clase_estado}'>{estado}</span>", unsafe_allow_html=True)

def cerrar_toda_sesion():
    st.session_state.admin_autenticado = False
    st.session_state.participante_actual = ""
    st.session_state.participante_autenticado = False
    st.session_state.panel_login_abierto = False
    st.session_state.vista_actual = "Inicio"


def ir_a_panel_actual():
    if st.session_state.admin_autenticado:
        st.session_state.vista_actual = "Admin"
    elif st.session_state.participante_autenticado:
        st.session_state.vista_actual = "Participante"


def mostrar_barra_superior_acceso():
    col_izq, col_der = st.columns([6, 1.35])

    with col_izq:
        if st.session_state.admin_autenticado:
            st.markdown('<div style="padding-top:0.35rem; color: rgba(255,255,255,0.92); font-weight:700;">Panel activo: <span class="texto-dorado">Administrador</span></div>', unsafe_allow_html=True)
        elif st.session_state.participante_autenticado:
            st.markdown(f'<div style="padding-top:0.35rem; color: rgba(255,255,255,0.92); font-weight:700;">Panel activo: <span class="texto-dorado">{st.session_state.participante_actual}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="padding-top:0.35rem; color: rgba(255,255,255,0.82);">Acceso a participante o administrador</div>', unsafe_allow_html=True)

    with col_der:
        if st.session_state.admin_autenticado or st.session_state.participante_autenticado:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Mi panel", use_container_width=True, key="boton_mi_panel_superior"):
                    ir_a_panel_actual()
                    st.rerun()
            with c2:
                if st.button("Cerrar sesión", use_container_width=True, key="boton_cerrar_sesion_superior"):
                    cerrar_toda_sesion()
                    st.rerun()
        else:
            if st.button("Inicio de sesión", use_container_width=True, key="boton_inicio_sesion_superior"):
                st.session_state.panel_login_abierto = not st.session_state.panel_login_abierto
                st.rerun()


def mostrar_panel_login_superior():
    participantes = obtener_participantes()
    nombres_existentes = sorted(participantes.keys())

    st.markdown(
        f"""
        <div class="quiniela-hero" style="margin-top: 0.35rem; padding: 1.2rem 1.35rem 1.05rem 1.35rem;">
            <div class="quiniela-badge">ACCESO</div>
            <div class="quiniela-hero-title" style="font-size:1.45rem;">Inicio de sesión</div>
            <p class="quiniela-hero-subtitle">Elige tu tipo de acceso y entra a tu panel correspondiente.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_participante, tab_admin = st.tabs(["Participante", "Administrador"])

    with tab_participante:
        if not nombres_existentes:
            st.warning("Aún no hay participantes creados. Pídele al administrador que los dé de alta.")
        else:
            participante_seleccionado = st.selectbox(
                "Selecciona tu participante",
                options=[""] + nombres_existentes,
                index=0,
                key="login_superior_participante_nombre"
            )
            clave_ingresada = st.text_input("Clave", type="password", key="login_superior_participante_clave")

            if st.button("Entrar como participante", use_container_width=True, key="login_superior_participante_boton"):
                if not participante_seleccionado.strip():
                    st.error("Debes seleccionar un participante.")
                elif not clave_ingresada.strip():
                    st.error("Debes capturar la clave.")
                elif autenticar_participante(participante_seleccionado, clave_ingresada):
                    st.session_state.participante_actual = participante_seleccionado
                    st.session_state.participante_autenticado = True
                    st.session_state.admin_autenticado = False
                    st.session_state.panel_login_abierto = False
                    st.session_state.vista_actual = "Participante"
                    st.success(f"Bienvenido, {participante_seleccionado}")
                    st.rerun()
                else:
                    st.error("Nombre o clave incorrectos.")

    with tab_admin:
        usuario_admin = st.text_input("Usuario admin", key="login_superior_admin_usuario")
        clave_admin = st.text_input("Clave admin", type="password", key="login_superior_admin_clave")

        if st.button("Entrar como administrador", use_container_width=True, key="login_superior_admin_boton"):
            if autenticar_admin(usuario_admin, clave_admin):
                st.session_state.admin_autenticado = True
                st.session_state.participante_actual = ""
                st.session_state.participante_autenticado = False
                st.session_state.panel_login_abierto = False
                st.session_state.vista_actual = "Admin"
                st.success("Acceso admin correcto.")
                st.rerun()
            else:
                st.error("Usuario o clave de admin incorrectos.")


# =========================================================
# SIDEBAR

# =========================================================
mostrar_logo_sidebar()
menu_sidebar = st.sidebar.radio(
    "Menú",
    ["Inicio", "Resultados oficiales FIFA", "Tabla general participantes", "Bonus"]
)

if menu_sidebar != st.session_state.menu_sidebar_last:
    st.session_state.menu_sidebar_last = menu_sidebar
    if menu_sidebar == "Resultados oficiales FIFA":
        st.session_state.vista_actual = "Resultados oficiales"
    elif menu_sidebar == "Tabla general participantes":
        st.session_state.vista_actual = "Tabla general"
    else:
        st.session_state.vista_actual = menu_sidebar

mostrar_barra_superior_acceso()

if st.session_state.panel_login_abierto and not (st.session_state.admin_autenticado or st.session_state.participante_autenticado):
    mostrar_panel_login_superior()
    mostrar_divider()

cerrar_bonus_por_hora_si_aplica()

menu = st.session_state.vista_actual

# =========================================================
# INICIO
# =========================================================
if menu == "Inicio":
    mostrar_encabezado_modulo(
        "QUINIELA MUNDIAL 2026",
        "Premium, FIFA style y fácil de leer para todos los participantes."
    )

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Inscripción", "$400 MXN")
    col_m2.metric("Punto por resultado", "+1")
    col_m3.metric("Extra por marcador exacto", "+2")

    mostrar_divider()

    st.markdown("### Cómo funciona el puntaje")
    puntos_df = pd.DataFrame([
        {"Concepto": "Aciertas ganador o empate", "Puntos": 1},
        {"Concepto": "Aciertas marcador exacto", "Puntos extra": 2},
        {"Concepto": "Marcador exacto total", "Total obtenido": 3},
    ])
    st.dataframe(puntos_df, use_container_width=True, hide_index=True)

    st.markdown("### Bonus por equipos favoritos")
    bonus_df = pd.DataFrame([
        {"Fase": fase, "Puntos por victoria del favorito": puntos}
        for fase, puntos in BONOS_FAVORITOS.items()
    ])
    st.dataframe(bonus_df, use_container_width=True, hide_index=True)

    mostrar_divider()

    st.markdown("### Cómo llenar tu quiniela")
    st.write("1. Inicia sesión desde el botón superior derecho.")
    st.write("2. Guarda primero tus 2 equipos favoritos.")
    st.write("3. Captura tus pronósticos por fase.")
    st.write("4. Si estás en Fase de grupos, captura un grupo y guarda antes de cambiar a otro.")
    st.write("5. Cuando termines tu fase, envía tu versión oficial.")

    st.warning(
        "Importante: si capturas un grupo y cambias a otro sin presionar 'Guardar borrador de la fase', "
        "lo que escribiste en pantalla todavía no se conserva."
    )

    st.info(
        "Para evitar cansancio visual se mantiene la captura por grupo en Fase de grupos. "
        "La recomendación es llenar un grupo, guardar borrador y después pasar al siguiente."
    )

    mostrar_divider()

    if FECHA_LIMITE_FAVORITOS:
        st.info(
            "Fecha límite para favoritos (primera fase): "
            f"{FECHA_LIMITE_FAVORITOS.strftime('%d/%m/%Y %H:%M')}"
        )

    if cierres_por_fase:
        st.markdown("### Cierres por fase")
        cierres_df = pd.DataFrame([
            {
                "Fase": fase,
                "Cierre": cierres_por_fase[fase].strftime("%d/%m/%Y %H:%M")
            }
            for fase in fases_ordenadas
            if fase in cierres_por_fase
        ])
        st.dataframe(cierres_df, use_container_width=True, hide_index=True)

    st.caption("Tabla de reparto del premio: pendiente por definir.")

# =========================================================
# PARTICIPANTE
# =========================================================
elif menu == "Participante":
    mostrar_encabezado_modulo(
        "PARTICIPANTE",
        "Acceso, favoritos y captura de pronósticos"
    )

    participantes = obtener_participantes()
    nombres_existentes = sorted(participantes.keys())

    if not nombres_existentes:
        st.warning("Aún no hay participantes creados. Pídele al administrador que los dé de alta.")
    elif partidos.empty:
        st.warning("Aún no hay partidos cargados en el calendario.")
    else:
        if not st.session_state.participante_autenticado:
            participante_seleccionado = st.selectbox(
                "Selecciona tu participante",
                options=[""] + nombres_existentes,
                index=0
            )

            clave_ingresada = st.text_input("Clave", type="password")

            if st.button("Entrar", use_container_width=True):
                if not participante_seleccionado.strip():
                    st.error("Debes seleccionar un participante.")
                elif not clave_ingresada.strip():
                    st.error("Debes capturar la clave.")
                elif autenticar_participante(participante_seleccionado, clave_ingresada):
                    st.session_state.participante_actual = participante_seleccionado
                    st.session_state.participante_autenticado = True
                    st.session_state.vista_actual = "Participante"
                    st.success(f"Bienvenido, {participante_seleccionado}")
                    st.rerun()
                else:
                    st.error("Nombre o clave incorrectos.")

        if st.session_state.participante_autenticado:
            participante_data = obtener_participante_actual()

            col_a, col_b = st.columns([3, 1])
            col_a.markdown(f"## Participante actual: {st.session_state.participante_actual}")
            with col_b:
                if st.button("Cerrar sesión", use_container_width=True):
                    cerrar_sesion_participante()
                    st.success("Sesión cerrada.")
                    st.rerun()

            if participante_data is not None:
                st.markdown("### 1) Elige tus 2 equipos favoritos")

                if FECHA_LIMITE_FAVORITOS:
                    if favoritos_bloqueados():
                        st.error("Los equipos favoritos ya están bloqueados.")
                    else:
                        st.success(
                            "Todavía puedes modificar tus favoritos hasta: "
                            f"{FECHA_LIMITE_FAVORITOS.strftime('%d/%m/%Y %H:%M')}"
                        )

                favoritos_actuales = participante_data["favoritos_guardados"]
                favorito_1_actual = favoritos_actuales[0] if len(favoritos_actuales) > 0 else equipos[0]

                opciones_favorito_2 = [e for e in equipos if e != favorito_1_actual]
                favorito_2_actual = favoritos_actuales[1] if len(favoritos_actuales) > 1 else (
                    opciones_favorito_2[0] if opciones_favorito_2 else ""
                )

                favorito_1 = st.selectbox(
                    "Equipo favorito 1",
                    options=equipos,
                    index=equipos.index(favorito_1_actual) if favorito_1_actual in equipos else 0,
                    disabled=favoritos_bloqueados(),
                    key="favorito_1_participante"
                )

                opciones_favorito_2 = [e for e in equipos if e != favorito_1]
                if favorito_2_actual == favorito_1 and opciones_favorito_2:
                    favorito_2_actual = opciones_favorito_2[0]

                favorito_2 = st.selectbox(
                    "Equipo favorito 2",
                    options=opciones_favorito_2,
                    index=opciones_favorito_2.index(favorito_2_actual) if favorito_2_actual in opciones_favorito_2 else 0,
                    disabled=favoritos_bloqueados(),
                    key="favorito_2_participante"
                )

                if st.button("Guardar favoritos", use_container_width=True, disabled=favoritos_bloqueados()):
                    participante_data["favoritos_guardados"] = [favorito_1, favorito_2]
                    persistir_db()
                    st.success("Tus equipos favoritos fueron guardados correctamente.")
                    st.rerun()

                if participante_data["favoritos_guardados"]:
                    mostrar_favoritos_participante(participante_data)
                else:
                    st.info("Aún no has guardado equipos favoritos.")

                mostrar_divider()

                st.markdown("### 2) Pronósticos por fase")

                fase_seleccionada = st.selectbox(
                    "Selecciona la fase a capturar",
                    options=fases_ordenadas,
                    key="fase_pronosticos_participante"
                )

                cierre_fase = cierres_por_fase.get(fase_seleccionada)
                fase_cerrada = fase_bloqueada(fase_seleccionada, cierres_por_fase)

                if cierre_fase:
                    if fase_cerrada:
                        st.error(
                            f"La fase '{fase_seleccionada}' ya está bloqueada desde "
                            f"{cierre_fase.strftime('%d/%m/%Y %H:%M')}."
                        )
                    else:
                        st.success(
                            f"La fase '{fase_seleccionada}' cierra el "
                            f"{cierre_fase.strftime('%d/%m/%Y %H:%M')}."
                        )

                grupo_seleccionado = None

                if fase_seleccionada == "Fase de grupos":
                    st.warning("Guarda el borrador antes de cambiar de grupo. Cambiar de grupo sin guardar descarta lo que aún no se ha guardado en pantalla.")
                    grupos_disponibles = obtener_grupos_fase(partidos, fase_seleccionada)

                    if grupos_disponibles:
                        grupo_seleccionado = st.selectbox(
                            "Selecciona el grupo a capturar",
                            options=grupos_disponibles,
                            key="grupo_pronosticos_participante"
                        )

                        partidos_fase = partidos[
                            (partidos["fase"] == fase_seleccionada) &
                            (partidos["grupo"] == grupo_seleccionado)
                        ].copy()

                        st.caption(
                            f"Estás capturando únicamente los partidos del Grupo {grupo_seleccionado}. "
                            "El cierre sigue siendo para toda la fase."
                        )
                    else:
                        partidos_fase = partidos[partidos["fase"] == fase_seleccionada].copy()
                else:
                    partidos_fase = partidos[partidos["fase"] == fase_seleccionada].copy()

                pronosticos_temporales = []

                for _, p in partidos_fase.iterrows():
                    pronostico_existente = obtener_pronostico_existente(participante_data, p["id"])

                    g1_default = int(pronostico_existente["marcador_local"]) if pronostico_existente else 0
                    g2_default = int(pronostico_existente["marcador_visitante"]) if pronostico_existente else 0

                    st.markdown(
                        f"**{p['local']} vs {p['visitante']}**  \\n"
                        f"{p['ciudad']} — {p['fase']} — Grupo {p['grupo']} — {p['fecha']} {p['hora']}"
                    )

                    col1, col2 = st.columns(2)

                    g1 = col1.number_input(
                        f"Goles de {p['local']} (Partido {p['id']})",
                        min_value=0,
                        max_value=20,
                        value=g1_default,
                        key=f"gol_local_{st.session_state.participante_actual}_{p['id']}",
                        disabled=fase_cerrada
                    )

                    g2 = col2.number_input(
                        f"Goles de {p['visitante']} (Partido {p['id']})",
                        min_value=0,
                        max_value=20,
                        value=g2_default,
                        key=f"gol_visitante_{st.session_state.participante_actual}_{p['id']}",
                        disabled=fase_cerrada
                    )

                    pronosticos_temporales.append({
                        "id": int(p["id"]),
                        "marcador_local": int(g1),
                        "marcador_visitante": int(g2)
                    })

                if not fase_cerrada and pronosticos_temporales:
                    pronosticos_ordenados = sorted(pronosticos_temporales, key=lambda x: int(x["id"]))
                    actuales_fase = [
                        p for p in participante_data.get("pronosticos_guardados", [])
                        if int(p["id"]) in obtener_ids_partidos_fase(partidos, fase_seleccionada)
                    ]
                    actuales_fase = sorted(actuales_fase, key=lambda x: int(x["id"]))
                    if pronosticos_ordenados != actuales_fase:
                        guardar_pronosticos_fase(participante_data, pronosticos_temporales)

                st.info("Tus cambios se guardan automáticamente mientras capturas.")

                capturados, total_fase = contar_avance_fase(participante_data, fase_seleccionada)
                st.caption(f"Avance de la fase: {capturados} de {total_fase} partidos capturados")

                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    if st.button("Resetar borrador de la fase actual", use_container_width=True, disabled=fase_cerrada):
                        resetear_borrador_fase_actual(participante_data, fase_seleccionada)
                        st.success(f"Se limpió el borrador de la fase '{fase_seleccionada}'.")
                        st.rerun()

                with col_g2:
                    puede_enviar_fase = fase_completa_para_envio(participante_data, fase_seleccionada)
                    if st.button("Enviar versión oficial de la fase", use_container_width=True, disabled=(fase_cerrada or not puede_enviar_fase)):
                        if len(participante_data["favoritos_guardados"]) != 2:
                            st.error("Debes guardar tus 2 equipos favoritos antes de enviar.")
                        else:
                            guardar_envio_oficial(
                                participante_data,
                                [p for p in participante_data["pronosticos_guardados"] if int(p["id"]) in obtener_ids_partidos_fase(partidos, fase_seleccionada)],
                                fase_seleccionada,
                                grupo=grupo_seleccionado
                            )
                            st.success(f"Versión oficial enviada para la fase '{fase_seleccionada}'.")
                            st.rerun()

                if not fase_completa_para_envio(participante_data, fase_seleccionada):
                    st.warning("Completa todos los partidos de la fase actual para habilitar el envío oficial.")

                envio_fase_actual = obtener_envio_fase(participante_data, fase_seleccionada)
                if envio_fase_actual:
                    mensaje_envio = f"Última versión oficial enviada para esta fase: {envio_fase_actual.get('fecha_envio', '')}"
                    if fase_seleccionada == "Fase de grupos" and envio_fase_actual.get("grupo"):
                        mensaje_envio += f" | Grupo: {envio_fase_actual.get('grupo')}"
                    st.info(mensaje_envio)

                historial_envios_df = construir_historial_envios_df(participante_data)
                st.markdown("### 3) Historial de envíos oficiales por etapa")
                if historial_envios_df.empty:
                    st.info("Aún no hay envíos oficiales registrados por etapa.")
                else:
                    st.dataframe(historial_envios_df, use_container_width=True, hide_index=True)

                st.markdown("### 4) Resumen general de pronósticos")

                if participante_data["pronosticos_guardados"]:
                    resumen_df = construir_resumen_pronosticos(participante_data["pronosticos_guardados"])
                    st.dataframe(resumen_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Aún no has guardado pronósticos.")

# =========================================================
# RESULTADOS OFICIALES
# =========================================================
elif menu == "Resultados oficiales":
    mostrar_encabezado_modulo(
        "RESULTADOS OFICIALES FIFA",
        "Consulta pública de marcadores capturados"
    )

    if partidos.empty:
        st.warning("Aún no hay partidos cargados.")
    else:
        fase_res = st.selectbox(
            "Filtrar por fase",
            options=["Todas"] + fases_ordenadas,
            key="fase_resultados_publicos"
        )

        partidos_resultados = partidos.copy()

        if fase_res != "Todas":
            partidos_resultados = partidos_resultados[partidos_resultados["fase"] == fase_res]

            if fase_res == "Fase de grupos":
                grupos_resultados = obtener_grupos_fase(partidos_resultados, fase_res)
                if grupos_resultados:
                    grupo_res = st.selectbox(
                        "Filtrar por grupo",
                        options=["Todos"] + grupos_resultados,
                        key="grupo_resultados_publicos"
                    )
                    if grupo_res != "Todos":
                        partidos_resultados = partidos_resultados[partidos_resultados["grupo"] == grupo_res]

        filas = []
        resultados = obtener_resultados_oficiales()

        for _, p in partidos_resultados.iterrows():
            resultado = resultados.get(str(p["id"]))
            filas.append({
                "Sede": p["ciudad"],
                "Fase": p["fase"],
                "Grupo": p["grupo"],
                "Fecha": p["fecha"],
                "Hora": p["hora"],
                "Local": p["local"],
                "Marcador local": resultado["marcador_local"] if resultado else "",
                "Marcador visitante": resultado["marcador_visitante"] if resultado else "",
                "Visitante": p["visitante"]
            })

        df_resultados = pd.DataFrame(filas)
        if df_resultados.empty:
            st.info("No hay partidos para mostrar.")
        else:
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)


# =========================================================
# BONUS
# =========================================================
elif menu == "Bonus":
    mostrar_encabezado_modulo(
        "BONUS",
        "Dinámica adicional con respuesta única, cierre automático y auditoría."
    )

    bonus = obtener_bonus()

    if bonus_esta_activo():
        partido_bonus = obtener_partido_por_id(bonus.get("partido_id"))
        col_bonus_izq, col_bonus_der = st.columns([1.15, 1])

        with col_bonus_izq:
            st.metric("Puntos bonus", f"{int(bonus.get('puntos', 0))} pts")

            if partido_bonus is not None:
                st.markdown(
                    f"""
                    <div class="quiniela-hero" style="text-align:left; padding:1.2rem 1.35rem;">
                        <div class="quiniela-hero-title" style="font-size:1.25rem;">{partido_bonus['local']} vs {partido_bonus['visitante']}</div>
                        <p class="quiniela-hero-subtitle">{partido_bonus['ciudad']} — {partido_bonus['fase']} — Grupo {partido_bonus['grupo']} — {partido_bonus['fecha']} {partido_bonus['hora']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown(f"### {bonus.get('pregunta', 'Pregunta bonus')}")
            opciones_bonus = bonus.get("opciones", [])

            if bonus_cerrado_por_hora():
                st.error("El bonus ya está bloqueado porque el partido inició.")
            else:
                st.success("Bonus abierto. Responde antes del inicio del partido.")

            if not st.session_state.participante_autenticado:
                st.info("Inicia sesión como participante para responder el bonus.")
            else:
                respuesta_existente = bonus.get("respuestas_participantes", {}).get(st.session_state.participante_actual)

                if respuesta_existente:
                    st.info(f"Tu respuesta registrada: {respuesta_existente.get('respuesta', '')}")
                    st.caption("Las respuestas bonus no se pueden modificar.")
                elif bonus_cerrado_por_hora():
                    st.warning("Ya no puedes responder este bonus.")
                else:
                    respuesta_bonus = st.radio(
                        "Selecciona tu respuesta",
                        options=opciones_bonus,
                        key=f"respuesta_bonus_{bonus.get('partido_id')}"
                    )
                    if st.button("Guardar respuesta bonus", use_container_width=True):
                        ok, mensaje = guardar_respuesta_bonus(st.session_state.participante_actual, respuesta_bonus)
                        if ok:
                            st.success(mensaje)
                            st.rerun()
                        else:
                            st.error(mensaje)

        with col_bonus_der:
            st.markdown("### Respuestas registradas")
            respuestas_df = construir_respuestas_bonus_df()
            if respuestas_df.empty:
                st.info("Aún no hay respuestas registradas.")
            else:
                st.dataframe(respuestas_df, use_container_width=True, hide_index=True)

    else:
        st.markdown("### Historial acumulado de puntos bonus")
        bonus_hist_df = construir_historial_bonus_acumulado_df()
        if bonus_hist_df.empty:
            st.info("Aún no hay puntos bonus acumulados para mostrar.")
        else:
            st.dataframe(bonus_hist_df, use_container_width=True, hide_index=True)
            st.caption("Aquí se muestran los puntos bonus acumulados por participante a lo largo de toda la quiniela.")

# =========================================================
# ADMIN
# =========================================================
elif menu == "Admin":
    mostrar_encabezado_modulo(
        "ADMIN",
        "Gestión de calendario, participantes, resultados y visibilidad"
    )

    if not st.session_state.admin_autenticado:
        usuario_admin = st.text_input("Usuario admin")
        clave_admin = st.text_input("Clave admin", type="password")

        if st.button("Entrar como admin", use_container_width=True):
            if autenticar_admin(usuario_admin, clave_admin):
                st.session_state.admin_autenticado = True
                st.session_state.vista_actual = "Admin"
                st.success("Acceso admin correcto.")
                st.rerun()
            else:
                st.error("Usuario o clave de admin incorrectos.")

    else:
        col_admin_a, col_admin_b = st.columns([3, 1])
        col_admin_a.success("Sesión de administrador iniciada.")
        with col_admin_b:
            if st.button("Cerrar sesión admin", use_container_width=True):
                st.session_state.admin_autenticado = False
                st.rerun()

        st.markdown("## 0) Configuración general")

        config = obtener_configuracion()
        mostrar_pronosticos = st.checkbox(
            "Permitir ver pronósticos de otros participantes",
            value=bool(config.get("mostrar_pronosticos_publicos", False)),
            key="toggle_pronosticos_publicos_admin"
        )

        if st.button("Guardar configuración general", use_container_width=True):
            st.session_state.db["configuracion"]["mostrar_pronosticos_publicos"] = mostrar_pronosticos
            persistir_db()
            st.success("Configuración actualizada correctamente.")
            st.rerun()

        if pronosticos_publicos_habilitados():
            st.success("Los pronósticos de otros participantes están visibles para el público.")
        else:
            st.warning("Los pronósticos de otros participantes están ocultos para el público.")

        st.markdown("## Bonus")

        bonus = obtener_bonus()
        opciones_partidos_bonus = construir_partidos_bonus_selector()

        if bonus_esta_activo():
            partido_bonus = obtener_partido_por_id(bonus.get("partido_id"))
            st.success("Hay un bonus activo en curso.")
            if partido_bonus is not None:
                st.markdown(
                    f"**Partido activo:** ID {int(partido_bonus['id'])} · {partido_bonus['local']} vs {partido_bonus['visitante']} · {partido_bonus['fase']} · Grupo {partido_bonus['grupo']} · {partido_bonus['fecha']} {partido_bonus['hora']}"
                )
            st.write(f"**Pregunta:** {bonus.get('pregunta', '')}")
            st.write(f"**Puntos bonus:** {int(bonus.get('puntos', 0))}")

            if bonus_cerrado_por_hora():
                respuesta_correcta = st.selectbox(
                    "Selecciona la respuesta correcta",
                    options=bonus.get("opciones", []),
                    key="admin_bonus_respuesta_correcta"
                )
                if st.button("Resolver bonus y asignar puntos", use_container_width=True):
                    ok, mensaje = resolver_bonus(respuesta_correcta)
                    if ok:
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.error(mensaje)
            else:
                st.info("El bonus sigue abierto. La resolución se habilita cuando el partido inicie.")
        else:
            st.info("No hay un bonus activo. Puedes configurar uno nuevo.")
            if opciones_partidos_bonus:
                labels = [x["label"] for x in opciones_partidos_bonus]
                label_sel = st.selectbox("Selecciona el partido bonus por ID", options=labels, key="admin_bonus_partido")
                partido_id_sel = next(x["id"] for x in opciones_partidos_bonus if x["label"] == label_sel)

                pregunta_bonus = st.text_input("Pregunta bonus", key="admin_bonus_pregunta")
                opcion_1 = st.text_input("Opción 1", key="admin_bonus_opcion_1")
                opcion_2 = st.text_input("Opción 2", key="admin_bonus_opcion_2")
                opcion_3 = st.text_input("Opción 3", key="admin_bonus_opcion_3")
                opcion_4 = st.text_input("Opción 4", key="admin_bonus_opcion_4")
                puntos_bonus = st.number_input("Puntos bonus", min_value=1, max_value=100, value=3, step=1, key="admin_bonus_puntos")

                if st.button("Activar bonus", use_container_width=True):
                    opciones_bonus = [opcion_1, opcion_2, opcion_3, opcion_4]
                    if not str(pregunta_bonus).strip():
                        st.error("Debes escribir la pregunta del bonus.")
                    elif len([x for x in opciones_bonus if str(x).strip()]) < 2:
                        st.error("Debes capturar al menos dos opciones de respuesta.")
                    else:
                        activar_bonus(partido_id_sel, pregunta_bonus, opciones_bonus, puntos_bonus)
                        st.success("Bonus activado correctamente.")
                        st.rerun()
            else:
                st.warning("No hay partidos disponibles para configurar bonus.")

        historial_bonus_df = construir_historial_bonus_acumulado_df()
        st.markdown("### Historial acumulado bonus")
        if historial_bonus_df.empty:
            st.info("Aún no hay puntos bonus acumulados.")
        else:
            st.dataframe(historial_bonus_df, use_container_width=True, hide_index=True)

        st.markdown("## 1) Gestión de calendario y limpieza")

        resumen_fases_df = resumen_fases_cargadas(partidos)
        if resumen_fases_df.empty:
            st.info("Aún no hay fases cargadas en el calendario maestro.")
        else:
            st.markdown("### Fases actualmente cargadas")
            st.dataframe(resumen_fases_df, use_container_width=True, hide_index=True)

        st.markdown("### Cargar archivo CSV")
        st.caption("Columnas requeridas: id,fase,grupo,fecha,hora,ciudad,estadio,local,visitante")

        archivo_csv = st.file_uploader(
            "Selecciona el archivo CSV del calendario",
            type=["csv"],
            key="uploader_partidos_csv"
        )

        modo_carga = st.radio(
            "Modo de carga",
            options=[
                "Reemplazar calendario completo",
                "Agregar / actualizar partidos por ID"
            ],
            index=0
        )

        if st.button("Procesar archivo CSV", use_container_width=True):
            if archivo_csv is None:
                st.error("Debes seleccionar un archivo CSV.")
            else:
                if modo_carga == "Reemplazar calendario completo":
                    ok, mensaje = guardar_partidos_csv_reemplazo_total(archivo_csv)
                else:
                    ok, mensaje = guardar_partidos_csv_agregar_actualizar(archivo_csv)

                if ok:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(mensaje)

        if os.path.exists(PARTIDOS_FILE):
            st.success(f"Archivo actual: {PARTIDOS_FILE}")
        else:
            st.warning("Aún no hay un archivo partidos.csv guardado.")

        st.markdown("### Calendario actualmente cargado")
        calendario_df = construir_calendario_df()
        if calendario_df.empty:
            st.info("Aún no hay partidos cargados.")
        else:
            st.dataframe(calendario_df, use_container_width=True, hide_index=True)

        st.markdown("### Limpieza de prueba")

        col_limp_1, col_limp_2, col_limp_3 = st.columns(3)

        with col_limp_1:
            confirmar_borrar_cal = st.checkbox(
                "Confirmo borrar solo el calendario",
                key="confirmar_borrar_calendario"
            )
            if st.button("Borrar calendario", use_container_width=True):
                if not confirmar_borrar_cal:
                    st.error("Debes confirmar la eliminación del calendario.")
                else:
                    ok, mensaje = borrar_archivo_calendario()
                    if ok:
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.warning(mensaje)

        with col_limp_2:
            confirmar_borrar_res = st.checkbox(
                "Confirmo borrar solo resultados oficiales",
                key="confirmar_borrar_resultados"
            )
            if st.button("Borrar resultados oficiales", use_container_width=True):
                if not confirmar_borrar_res:
                    st.error("Debes confirmar la eliminación de resultados.")
                else:
                    ok, mensaje = limpiar_resultados_oficiales()
                    if ok:
                        st.success(mensaje)
                        st.rerun()

        with col_limp_3:
            confirmar_reset_total = st.checkbox(
                "Confirmo reset total de prueba",
                key="confirmar_reset_total_prueba"
            )
            if st.button("Reset total de prueba", use_container_width=True):
                if not confirmar_reset_total:
                    st.error("Debes confirmar el reset total.")
                else:
                    ok, mensaje = reset_total_prueba()
                    if ok:
                        st.success(mensaje)
                        st.rerun()

        st.markdown("## 2) Administración de participantes")

        participantes = obtener_participantes()
        nombres_existentes = sorted(participantes.keys())

        nombre_nuevo = st.text_input("Nombre del nuevo participante")
        clave_nueva = st.text_input("Clave del nuevo participante", type="password")

        participante_edicion = st.selectbox(
            "Selecciona participante a editar",
            options=[""] + nombres_existentes,
            key="participante_edicion_admin"
        )

        col_adm_1, col_adm_2, col_adm_3 = st.columns(3)

        with col_adm_1:
            if st.button("Crear participante", use_container_width=True):
                ok, mensaje = crear_participante(nombre_nuevo, clave_nueva)
                if ok:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(mensaje)

        with col_adm_2:
            nuevo_nombre_edicion = st.text_input("Nuevo nombre", key="nuevo_nombre_participante")
            if st.button("Guardar nuevo nombre", use_container_width=True):
                if not participante_edicion:
                    st.error("Selecciona un participante.")
                else:
                    ok, mensaje = renombrar_participante(participante_edicion, nuevo_nombre_edicion)
                    if ok:
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.error(mensaje)

        with col_adm_3:
            nueva_clave_edicion = st.text_input("Nueva clave", type="password", key="nueva_clave_participante")
            if st.button("Guardar nueva clave", use_container_width=True):
                if not participante_edicion:
                    st.error("Selecciona un participante.")
                else:
                    ok, mensaje = cambiar_clave_participante(participante_edicion, nueva_clave_edicion)
                    if ok:
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.error(mensaje)

        st.markdown("### Eliminar participante")
        participante_eliminar = st.selectbox(
            "Selecciona participante a eliminar",
            options=[""] + nombres_existentes,
            key="participante_eliminar_admin"
        )

        confirmar_eliminacion = st.checkbox(
            "Confirmo que quiero eliminar al participante seleccionado",
            key="confirmar_eliminacion_admin"
        )

        if st.button("Eliminar participante", use_container_width=True):
            if not participante_eliminar:
                st.error("Selecciona un participante.")
            elif not confirmar_eliminacion:
                st.error("Debes confirmar la eliminación.")
            else:
                ok, mensaje = eliminar_participante(participante_eliminar)
                if ok:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(mensaje)

        if participantes:
            filas_participantes = []
            for nombre, datos in sorted(participantes.items()):
                filas_participantes.append({
                    "Participante": nombre,
                    "Clave asignada": datos.get("clave", "SIN CLAVE"),
                    "Favoritos capturados": len(datos["favoritos_guardados"]),
                    "Pronósticos capturados": len(datos["pronosticos_guardados"]),
                    "Etapas enviadas oficialmente": len(datos.get("envios_por_fase", {}))
                })

            st.dataframe(pd.DataFrame(filas_participantes), use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay participantes registrados.")

        st.markdown("## 3) Captura de resultados oficiales")

        if partidos.empty:
            st.warning("Aún no hay partidos cargados.")
        else:
            fase_admin = st.selectbox(
                "Filtrar partidos por fase",
                options=["Todas"] + fases_ordenadas,
                key="fase_admin_resultados"
            )

            partidos_admin = partidos.copy()

            if fase_admin != "Todas":
                partidos_admin = partidos_admin[partidos_admin["fase"] == fase_admin]

                if fase_admin == "Fase de grupos":
                    grupos_admin = obtener_grupos_fase(partidos_admin, fase_admin)
                    if grupos_admin:
                        grupo_admin = st.selectbox(
                            "Filtrar por grupo",
                            options=["Todos"] + grupos_admin,
                            key="grupo_admin_resultados"
                        )
                        if grupo_admin != "Todos":
                            partidos_admin = partidos_admin[partidos_admin["grupo"] == grupo_admin]

            resultados = obtener_resultados_oficiales()

            for _, p in partidos_admin.iterrows():
                st.markdown(
                    f"**{p['local']} vs {p['visitante']}**  \n"
                    f"{p['ciudad']} — {p['fase']} — Grupo {p['grupo']} — {p['fecha']} {p['hora']}"
                )

                resultado_actual = resultados.get(str(p["id"]), {"marcador_local": 0, "marcador_visitante": 0})

                col1, col2 = st.columns(2)

                r1 = col1.number_input(
                    f"Resultado oficial {p['local']} (Partido {p['id']})",
                    min_value=0,
                    max_value=20,
                    value=int(resultado_actual["marcador_local"]),
                    key=f"admin_local_{p['id']}"
                )

                r2 = col2.number_input(
                    f"Resultado oficial {p['visitante']} (Partido {p['id']})",
                    min_value=0,
                    max_value=20,
                    value=int(resultado_actual["marcador_visitante"]),
                    key=f"admin_visitante_{p['id']}"
                )

                if st.button(f"Guardar resultado oficial partido {p['id']}", key=f"guardar_resultado_{p['id']}"):
                    guardar_resultado_oficial(p["id"], r1, r2)
                    st.success(f"Resultado oficial guardado para {p['local']} vs {p['visitante']}.")
                    st.rerun()

                st.divider()

        st.markdown("## 4) Resultados oficiales capturados")
        resultados = obtener_resultados_oficiales()

        if resultados:
            filas_resultados = []
            for _, p in partidos.iterrows():
                resultado = resultados.get(str(p["id"]))
                if resultado:
                    filas_resultados.append({
                        "Sede": p["ciudad"],
                        "Fase": p["fase"],
                        "Grupo": p["grupo"],
                        "Fecha": p["fecha"],
                        "Hora": p["hora"],
                        "Local": p["local"],
                        "Marcador local": resultado["marcador_local"],
                        "Marcador visitante": resultado["marcador_visitante"],
                        "Visitante": p["visitante"]
                    })

            st.dataframe(pd.DataFrame(filas_resultados), use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay resultados oficiales capturados.")

        st.markdown("## 5) Bonus de favoritos por fase")
        bonus_admin_df = construir_bonus_favoritos_admin()

        if bonus_admin_df.empty:
            st.info("Aún no hay resultados suficientes para mostrar qué favoritos están dando puntos.")
        else:
            st.dataframe(bonus_admin_df, use_container_width=True, hide_index=True)

# =========================================================
# TABLA GENERAL
# =========================================================
elif menu == "Tabla general":
    mostrar_encabezado_modulo(
        "TABLA GENERAL PARTICIPANTES",
        "Ranking acumulado con desempates activos"
    )

    tabla_general_df = construir_tabla_general()

    if tabla_general_df.empty:
        st.info("Aún no hay información suficiente para mostrar la tabla general.")
    else:
        styled_df = tabla_general_df.style.set_properties(
            subset=["Puntos Base ganados", "Puntos por favoitos", "Total Puntos ganados"],
            **{"font-weight": "bold", "color": "#FFFFFF", "background-color": "#111111"}
        )

        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        st.caption(
            "El ranking considera puntos totales y criterios internos de desempate."
        )

        participantes = obtener_participantes()
        nombres_participantes = sorted(participantes.keys())

        st.markdown("### Detalle por participante")
        participante_filtro = st.selectbox(
            "Filtrar participante",
            options=[""] + nombres_participantes,
            index=0,
            key="filtro_participante_tabla_general"
        )

        if participante_filtro:
            participante_data = participantes.get(participante_filtro)

            if not usuario_puede_ver_detalle_participante(participante_filtro):
                if seleccion_es_participante_ajeno(participante_filtro):
                    st.warning("👉 No seas metiche 😎. Los pronósticos de otros participantes no están visibles por el momento.")
                else:
                    st.warning("No tienes permiso para ver este detalle.")
            else:
                favoritos_df = construir_tabla_favoritos_participante(participante_data)
                st.markdown("### Favoritos y puntos por fase")
                if favoritos_df.empty:
                    st.info("Este participante aún no tiene favoritos guardados.")
                else:
                    st.dataframe(favoritos_df, use_container_width=True, hide_index=True)

                pronosticos_participante_df = construir_tabla_pronosticos_participante(
                    participante_filtro,
                    participante_data
                )
                st.markdown("### Pronósticos del participante")
                if pronosticos_participante_df.empty:
                    st.info("Este participante aún no tiene pronósticos capturados.")
                else:
                    st.dataframe(pronosticos_participante_df, use_container_width=True, hide_index=True)
