import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

try:
    from streamlit_gsheets import GSheetsConnection
except Exception:
    GSheetsConnection = None


# =========================================================
# CONFIG GENERAL
# =========================================================
APP_TZ = "America/Mexico_City"
REQUIRED_SPREADSHEET_NAME = "QUINIELA 2026 DB"
MEXICO_TZ = ZoneInfo(APP_TZ)
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "admin123"
BONUS_FAVORITOS = {
    "Fase de grupos": 1,
    "Dieciseisavos": 2,
    "Octavos": 3,
    "Cuartos": 5,
    "Semifinal": 7,
    "Tercer Lugar": 8,
    "Final": 10,
}
FASES_ORDEN = [
    "Fase de grupos",
    "Dieciseisavos",
    "Octavos",
    "Cuartos",
    "Semifinal",
    "Tercer Lugar",
    "Final",
]

SHEET_CONFIG = "configuracion"
SHEET_PARTICIPANTES = "participantes"
SHEET_PARTIDOS = "partidos"
SHEET_PRONOSTICOS = "pronosticos"
SHEET_RESULTADOS = "resultados_oficiales"
SHEET_PUNTOS = "puntos_partido"
SHEET_BONUS_RESP = "bonus_respuestas"
SHEET_BONUS_PUNTOS = "bonus_puntos"


# =========================================================
# STREAMLIT BASE
# =========================================================
st.set_page_config(page_title="Quiniela Mundial 2026", layout="wide")


# =========================================================
# UTILIDADES
# =========================================================
def now_mx() -> datetime:
    return datetime.now(MEXICO_TZ)


def safe_json_load(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    value = str(value).strip()
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def normalize_text(v):
    if pd.isna(v):
        return ""
    return str(v).strip()


def normalize_int(v, default=None):
    if pd.isna(v) or v == "":
        return default
    try:
        return int(float(v))
    except Exception:
        return default


def parse_match_datetime(row) -> datetime | None:
    fecha = normalize_text(row.get("fecha"))
    hora = normalize_text(row.get("hora"))
    if not fecha:
        return None

    patterns = [
        f"{fecha} {hora}".strip(),
        fecha,
    ]
    formats = [
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%d",
    ]

    for text in patterns:
        for fmt in formats:
            try:
                dt = datetime.strptime(text, fmt)
                return dt.replace(tzinfo=MEXICO_TZ)
            except Exception:
                pass
    return None


def serialize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


def init_state():
    defaults = {
        "logged_in": False,
        "user_name": "",
        "is_admin": False,
        "draft_resultados": {},
        "draft_pronosticos": {},
        "draft_bonus": {},
        "config_dirty": False,
        "nav": "INICIO",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =========================================================
# GOOGLE SHEETS
# =========================================================
def get_conn():
    if GSheetsConnection is None:
        return None
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception:
        return None


def render_connection_help():
    st.error("No se pudo conectar con Google Sheets.")
    st.code(
        """# .streamlit/secrets.toml
[connections.gsheets]
spreadsheet = \"QUINIELA 2026 DB\""" ,
        language="toml",
    )
    st.caption(
        "Verifica que el archivo exista con ese nombre exacto y que esté compartido con la service account de Streamlit."
    )


def read_sheet(sheet_name: str, expected_columns: list[str]) -> pd.DataFrame:
    conn = get_conn()
    if conn is None:
        return pd.DataFrame(columns=expected_columns)
    try:
        df = conn.read(worksheet=sheet_name, usecols=list(range(len(expected_columns))), ttl=0)
        if df is None:
            return pd.DataFrame(columns=expected_columns)
        df = pd.DataFrame(df)
        df.columns = [str(c).strip() for c in df.columns]
        df = ensure_columns(df, expected_columns)
        return df.fillna("")
    except Exception:
        return pd.DataFrame(columns=expected_columns)


def write_sheet(sheet_name: str, df: pd.DataFrame):
    conn = get_conn()
    if conn is None:
        raise RuntimeError("No se encontró la conexión gsheets.")
    conn.update(worksheet=sheet_name, data=serialize_df(df))


# =========================================================
# ESTRUCTURAS BASE
# =========================================================
def load_all_data():
    config = read_sheet(SHEET_CONFIG, ["clave", "valor"])
    participantes = read_sheet(
        SHEET_PARTICIPANTES,
        [
            "nombre",
            "clave",
            "favoritos_guardados_json",
            "fecha_envio",
            "fecha_envio_iso",
            "es_admin",
        ],
    )
    partidos = read_sheet(
        SHEET_PARTIDOS,
        [
            "partido_id",
            "fase",
            "grupo",
            "fecha",
            "hora",
            "ciudad",
            "estadio",
            "local",
            "visitante",
            "deadline_iso",
            "bonus_habilitado",
            "bonus_pregunta",
            "bonus_opciones_json",
            "bonus_puntos",
            "bonus_respuesta_correcta",
            "activo",
        ],
    )
    pronosticos = read_sheet(
        SHEET_PRONOSTICOS,
        [
            "participante",
            "partido_id",
            "marcador_local",
            "marcador_visitante",
            "fecha_guardado_iso",
        ],
    )
    resultados = read_sheet(
        SHEET_RESULTADOS,
        ["partido_id", "marcador_local", "marcador_visitante", "fecha_guardado_iso"],
    )
    puntos = read_sheet(
        SHEET_PUNTOS,
        [
            "participante",
            "partido_id",
            "fase",
            "acierto_resultado",
            "exacto",
            "puntos_base",
            "puntos_favorito",
            "total_partido",
            "fecha_calculo_iso",
        ],
    )
    bonus_resp = read_sheet(
        SHEET_BONUS_RESP,
        ["participante", "partido_id", "respuesta", "fecha_guardado_iso"],
    )
    bonus_puntos = read_sheet(
        SHEET_BONUS_PUNTOS,
        ["participante", "partido_id", "puntos_bonus", "fecha_calculo_iso"],
    )

    return {
        "config": config,
        "participantes": participantes,
        "partidos": partidos,
        "pronosticos": pronosticos,
        "resultados": resultados,
        "puntos": puntos,
        "bonus_resp": bonus_resp,
        "bonus_puntos": bonus_puntos,
    }


@st.cache_data(ttl=15, show_spinner=False)
def load_all_data_cached(_nonce: int = 0):
    return load_all_data()


def clear_data_cache():
    load_all_data_cached.clear()


def get_config_map(config_df: pd.DataFrame) -> dict:
    result = {}
    for _, row in config_df.iterrows():
        result[normalize_text(row["clave"])] = normalize_text(row["valor"])
    return result


def upsert_config_value(config_df: pd.DataFrame, clave: str, valor: str) -> pd.DataFrame:
    config_df = config_df.copy()
    mask = config_df["clave"].astype(str).str.strip().eq(clave)
    if mask.any():
        config_df.loc[mask, "valor"] = valor
    else:
        config_df.loc[len(config_df)] = [clave, valor]
    return config_df


# =========================================================
# AUTH
# =========================================================
def validate_login(participantes_df: pd.DataFrame, nombre: str, clave: str):
    df = participantes_df.copy()
    df["nombre_norm"] = df["nombre"].astype(str).str.strip().str.lower()
    df["clave_norm"] = df["clave"].astype(str).str.strip()
    row = df[(df["nombre_norm"] == nombre.strip().lower()) & (df["clave_norm"] == clave.strip())]
    if row.empty:
        return None
    data = row.iloc[0].to_dict()
    is_admin = str(data.get("es_admin", "")).strip().lower() in ["1", "true", "si", "sí", "x"]
    return {"nombre": data["nombre"], "is_admin": is_admin}


def login_box(participantes_df: pd.DataFrame):
    st.title("Quiniela Mundial 2026")
    st.caption("Acceso multiusuario con Google Sheets")

    col1, col2 = st.columns([1, 1])
    with col1:
        nombre = st.text_input("Usuario")
    with col2:
        clave = st.text_input("Clave", type="password")

    if st.button("Entrar", use_container_width=True):
        auth = validate_login(participantes_df, nombre, clave)
        if auth:
            st.session_state.logged_in = True
            st.session_state.user_name = auth["nombre"]
            st.session_state.is_admin = auth["is_admin"]
            st.rerun()
        else:
            st.error("Usuario o clave incorrectos.")


# =========================================================
# CARGA DE CALENDARIO
# =========================================================
def ingest_calendar_csv(df_csv: pd.DataFrame, partidos_df: pd.DataFrame) -> pd.DataFrame:
    partidos_df = partidos_df.copy()
    df = df_csv.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    mapper = {
        "id": "partido_id",
        "fase": "fase",
        "grupo": "grupo",
        "fecha": "fecha",
        "hora": "hora",
        "ciudad": "ciudad",
        "estadio": "estadio",
        "local": "local",
        "visitante": "visitante",
    }
    for k in mapper:
        if k not in df.columns:
            df[k] = ""

    df = df[list(mapper.keys())].rename(columns=mapper)
    df["partido_id"] = df["partido_id"].astype(str).str.strip()
    df["fase"] = df["fase"].astype(str).str.strip()
    df["grupo"] = df["grupo"].astype(str).str.strip()
    df["fecha"] = df["fecha"].astype(str).str.strip()
    df["hora"] = df["hora"].astype(str).str.strip()
    df["ciudad"] = df["ciudad"].astype(str).str.strip()
    df["estadio"] = df["estadio"].astype(str).str.strip()
    df["local"] = df["local"].astype(str).str.strip()
    df["visitante"] = df["visitante"].astype(str).str.strip()

    df["deadline_iso"] = ""
    for idx, row in df.iterrows():
        dt = parse_match_datetime(row)
        df.loc[idx, "deadline_iso"] = dt.isoformat() if dt else ""

    df["bonus_habilitado"] = "0"
    df["bonus_pregunta"] = ""
    df["bonus_opciones_json"] = "[]"
    df["bonus_puntos"] = "0"
    df["bonus_respuesta_correcta"] = ""
    df["activo"] = "1"

    partidos_df = ensure_columns(partidos_df, df.columns.tolist())
    partidos_df["partido_id"] = partidos_df["partido_id"].astype(str).str.strip()

    for _, row in df.iterrows():
        pid = row["partido_id"]
        mask = partidos_df["partido_id"].eq(pid)
        if mask.any():
            for col in df.columns:
                if col in ["bonus_habilitado", "bonus_pregunta", "bonus_opciones_json", "bonus_puntos", "bonus_respuesta_correcta", "activo"]:
                    continue
                partidos_df.loc[mask, col] = row[col]
        else:
            partidos_df.loc[len(partidos_df)] = row.tolist()

    return partidos_df.sort_values(by=["fase", "grupo", "partido_id"]).reset_index(drop=True)


# =========================================================
# REGLAS DE PUNTUACIÓN
# =========================================================
def result_type(local, visitante):
    if local > visitante:
        return "L"
    if visitante > local:
        return "V"
    return "E"


def puntos_partido(pron_local, pron_visit, of_local, of_visit):
    acierto = int(result_type(pron_local, pron_visit) == result_type(of_local, of_visit))
    exacto = int(pron_local == of_local and pron_visit == of_visit)
    base = acierto * 1 + exacto * 2
    return {
        "acierto_resultado": acierto,
        "exacto": exacto,
        "puntos_base": base,
    }


def recompute_points(data: dict):
    participantes = data["participantes"].copy()
    partidos = data["partidos"].copy()
    pronosticos = data["pronosticos"].copy()
    resultados = data["resultados"].copy()
    bonus_resp = data["bonus_resp"].copy()

    if participantes.empty or partidos.empty or pronosticos.empty or resultados.empty:
        return (
            pd.DataFrame(
                columns=[
                    "participante",
                    "partido_id",
                    "fase",
                    "acierto_resultado",
                    "exacto",
                    "puntos_base",
                    "puntos_favorito",
                    "total_partido",
                    "fecha_calculo_iso",
                ]
            ),
            pd.DataFrame(columns=["participante", "partido_id", "puntos_bonus", "fecha_calculo_iso"]),
        )

    favoritos_map = {}
    for _, row in participantes.iterrows():
        favoritos_map[normalize_text(row["nombre"])] = safe_json_load(row.get("favoritos_guardados_json"), [])

    pr = pronosticos.copy()
    rs = resultados.copy()
    pt = partidos.copy()

    pr["partido_id"] = pr["partido_id"].astype(str).str.strip()
    pr["participante"] = pr["participante"].astype(str).str.strip()
    rs["partido_id"] = rs["partido_id"].astype(str).str.strip()
    pt["partido_id"] = pt["partido_id"].astype(str).str.strip()

    merged = pr.merge(rs, on="partido_id", how="inner", suffixes=("_pron", "_of"))
    merged = merged.merge(pt[["partido_id", "fase", "local", "visitante"]], on="partido_id", how="left")

    rows = []
    bonus_rows = []
    calc_ts = now_mx().isoformat()

    for _, row in merged.iterrows():
        p_local = normalize_int(row["marcador_local_pron"], 0)
        p_visit = normalize_int(row["marcador_visitante_pron"], 0)
        o_local = normalize_int(row["marcador_local_of"], 0)
        o_visit = normalize_int(row["marcador_visitante_of"], 0)
        calc = puntos_partido(p_local, p_visit, o_local, o_visit)

        favorito_pts = 0
        participante = normalize_text(row["participante"])
        favoritos = favoritos_map.get(participante, [])
        local = normalize_text(row["local"])
        visitante = normalize_text(row["visitante"])
        fase = normalize_text(row["fase"])

        ganador = None
        if o_local > o_visit:
            ganador = local
        elif o_visit > o_local:
            ganador = visitante

        if ganador and ganador in favoritos:
            favorito_pts = BONUS_FAVORITOS.get(fase, 0)

        total = calc["puntos_base"] + favorito_pts
        rows.append(
            {
                "participante": participante,
                "partido_id": normalize_text(row["partido_id"]),
                "fase": fase,
                "acierto_resultado": str(calc["acierto_resultado"]),
                "exacto": str(calc["exacto"]),
                "puntos_base": str(calc["puntos_base"]),
                "puntos_favorito": str(favorito_pts),
                "total_partido": str(total),
                "fecha_calculo_iso": calc_ts,
            }
        )

    partidos_bonus = partidos.copy()
    partidos_bonus["partido_id"] = partidos_bonus["partido_id"].astype(str).str.strip()

    for _, row in bonus_resp.iterrows():
        participante = normalize_text(row["participante"])
        partido_id = normalize_text(row["partido_id"])
        respuesta = normalize_text(row["respuesta"])
        pb = partidos_bonus[partidos_bonus["partido_id"] == partido_id]
        if pb.empty:
            continue
        pb_row = pb.iloc[0]
        habilitado = str(pb_row.get("bonus_habilitado", "0")).strip().lower() in ["1", "true", "si", "sí", "x"]
        correcta = normalize_text(pb_row.get("bonus_respuesta_correcta", ""))
        puntos_bonus = normalize_int(pb_row.get("bonus_puntos", 0), 0) or 0
        otorgado = puntos_bonus if habilitado and correcta and respuesta == correcta else 0
        bonus_rows.append(
            {
                "participante": participante,
                "partido_id": partido_id,
                "puntos_bonus": str(otorgado),
                "fecha_calculo_iso": calc_ts,
            }
        )

    return pd.DataFrame(rows), pd.DataFrame(bonus_rows)


# =========================================================
# GUARDADOS
# =========================================================
def save_admin_results_batch(partidos_fase: pd.DataFrame, draft: dict, resultados_df: pd.DataFrame):
    resultados_df = resultados_df.copy()
    resultados_df["partido_id"] = resultados_df["partido_id"].astype(str).str.strip()

    ts = now_mx().isoformat()
    for _, row in partidos_fase.iterrows():
        pid = normalize_text(row["partido_id"])
        d = draft.get(pid)
        if not d:
            continue
        local = d.get("marcador_local")
        visitante = d.get("marcador_visitante")
        if local in [None, ""] or visitante in [None, ""]:
            continue
        mask = resultados_df["partido_id"] == pid
        payload = [pid, str(local), str(visitante), ts]
        if mask.any():
            resultados_df.loc[mask, ["marcador_local", "marcador_visitante", "fecha_guardado_iso"]] = [str(local), str(visitante), ts]
        else:
            resultados_df.loc[len(resultados_df)] = payload

    resultados_df = resultados_df.drop_duplicates(subset=["partido_id"], keep="last")
    write_sheet(SHEET_RESULTADOS, resultados_df)
    clear_data_cache()



def save_user_predictions_batch(participante: str, partidos_grupo: pd.DataFrame, draft: dict, pronosticos_df: pd.DataFrame):
    pronosticos_df = pronosticos_df.copy()
    pronosticos_df["partido_id"] = pronosticos_df["partido_id"].astype(str).str.strip()
    pronosticos_df["participante"] = pronosticos_df["participante"].astype(str).str.strip()

    ts = now_mx().isoformat()
    for _, row in partidos_grupo.iterrows():
        pid = normalize_text(row["partido_id"])
        d = draft.get(pid)
        if not d:
            continue
        local = d.get("marcador_local")
        visitante = d.get("marcador_visitante")
        if local in [None, ""] or visitante in [None, ""]:
            continue
        keymask = (pronosticos_df["participante"] == participante) & (pronosticos_df["partido_id"] == pid)
        payload = [participante, pid, str(local), str(visitante), ts]
        if keymask.any():
            pronosticos_df.loc[keymask, ["marcador_local", "marcador_visitante", "fecha_guardado_iso"]] = [str(local), str(visitante), ts]
        else:
            pronosticos_df.loc[len(pronosticos_df)] = payload

    pronosticos_df = pronosticos_df.drop_duplicates(subset=["participante", "partido_id"], keep="last")
    write_sheet(SHEET_PRONOSTICOS, pronosticos_df)
    clear_data_cache()



def save_bonus_answers_batch(participante: str, partidos_bonus: pd.DataFrame, draft: dict, bonus_df: pd.DataFrame):
    bonus_df = bonus_df.copy()
    bonus_df["partido_id"] = bonus_df["partido_id"].astype(str).str.strip()
    bonus_df["participante"] = bonus_df["participante"].astype(str).str.strip()

    ts = now_mx().isoformat()
    for _, row in partidos_bonus.iterrows():
        pid = normalize_text(row["partido_id"])
        answer = draft.get(pid)
        if not answer:
            continue
        keymask = (bonus_df["participante"] == participante) & (bonus_df["partido_id"] == pid)
        payload = [participante, pid, str(answer), ts]
        if keymask.any():
            bonus_df.loc[keymask, ["respuesta", "fecha_guardado_iso"]] = [str(answer), ts]
        else:
            bonus_df.loc[len(bonus_df)] = payload

    bonus_df = bonus_df.drop_duplicates(subset=["participante", "partido_id"], keep="last")
    write_sheet(SHEET_BONUS_RESP, bonus_df)
    clear_data_cache()



def save_favoritos(participantes_df: pd.DataFrame, participante: str, favoritos: list[str]):
    participantes_df = participantes_df.copy()
    mask = participantes_df["nombre"].astype(str).str.strip().eq(participante)
    if not mask.any():
        raise RuntimeError("Participante no encontrado.")
    participantes_df.loc[mask, "favoritos_guardados_json"] = json.dumps(favoritos, ensure_ascii=False)
    participantes_df.loc[mask, "fecha_envio"] = now_mx().strftime("%d/%m/%Y %H:%M")
    participantes_df.loc[mask, "fecha_envio_iso"] = now_mx().isoformat()
    write_sheet(SHEET_PARTICIPANTES, participantes_df)
    clear_data_cache()



def create_user(participantes_df: pd.DataFrame, nombre: str, clave: str, is_admin: bool = False):
    participantes_df = participantes_df.copy()
    nombre = nombre.strip()
    clave = clave.strip()
    if not nombre or not clave:
        raise RuntimeError("Nombre y clave son obligatorios.")

    existing = participantes_df[participantes_df["nombre"].astype(str).str.strip().str.lower() == nombre.lower()]
    if not existing.empty:
        raise RuntimeError("Ese usuario ya existe.")

    participantes_df.loc[len(participantes_df)] = [
        nombre,
        clave,
        "[]",
        "",
        "",
        "1" if is_admin else "0",
    ]
    write_sheet(SHEET_PARTICIPANTES, participantes_df)
    clear_data_cache()



def save_config_visibility(config_df: pd.DataFrame, visible: bool):
    config_df = upsert_config_value(config_df, "ver_pronosticos_ajenos", "1" if visible else "0")
    write_sheet(SHEET_CONFIG, config_df)
    clear_data_cache()



def save_bonus_setup(partidos_df: pd.DataFrame, partido_id: str, pregunta: str, opciones: list[str], puntos: int, respuesta_correcta: str):
    partidos_df = partidos_df.copy()
    mask = partidos_df["partido_id"].astype(str).str.strip().eq(str(partido_id).strip())
    if not mask.any():
        raise RuntimeError("Partido no encontrado.")
    partidos_df.loc[mask, "bonus_habilitado"] = "1"
    partidos_df.loc[mask, "bonus_pregunta"] = pregunta.strip()
    partidos_df.loc[mask, "bonus_opciones_json"] = json.dumps(opciones, ensure_ascii=False)
    partidos_df.loc[mask, "bonus_puntos"] = str(int(puntos))
    partidos_df.loc[mask, "bonus_respuesta_correcta"] = respuesta_correcta.strip()
    write_sheet(SHEET_PARTIDOS, partidos_df)
    clear_data_cache()



def recalculate_and_save_all_points(data: dict):
    puntos_df, bonus_puntos_df = recompute_points(data)
    write_sheet(SHEET_PUNTOS, puntos_df)
    write_sheet(SHEET_BONUS_PUNTOS, bonus_puntos_df)
    clear_data_cache()


# =========================================================
# VISTAS
# =========================================================
def sidebar_nav():
    st.sidebar.title("Menú")
    options = [
        "INICIO",
        "RESULTADOS OFICIALES FIFA",
        "TABLA GENERAL DE PARTICIPANTES",
        "BONUS",
    ]
    if st.session_state.is_admin:
        options.insert(1, "ADMINISTRACIÓN")
        options.insert(2, "CAPTURA DE PRONÓSTICOS")
    else:
        options.insert(1, "CAPTURA DE PRONÓSTICOS")

    selected = st.sidebar.radio("Ir a", options, index=options.index(st.session_state.nav) if st.session_state.nav in options else 0)
    st.session_state.nav = selected
    st.sidebar.divider()
    st.sidebar.write(f"**Usuario:** {st.session_state.user_name}")
    st.sidebar.write(f"**Rol:** {'Administrador' if st.session_state.is_admin else 'Participante'}")
    if st.sidebar.button("Cerrar sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.is_admin = False
        st.session_state.draft_resultados = {}
        st.session_state.draft_pronosticos = {}
        st.session_state.draft_bonus = {}
        st.rerun()



def render_inicio(config_map: dict):
    st.title("INICIO")
    st.subheader("Cómo funciona la quiniela")
    st.write(
        "Cada participante captura sus pronósticos por grupo o por fase. Los guardados se hacen manualmente con botón para evitar recargas innecesarias y mejorar la estabilidad multiusuario."
    )

    st.markdown("### Puntos base")
    st.write("Aciertas ganador o empate: **1 punto**")
    st.write("Aciertas marcador exacto: **+2 puntos**")
    st.write("Total por marcador exacto: **3 puntos**")

    st.markdown("### Bonus por equipos favoritos")
    fav_df = pd.DataFrame(
        [{"Fase": k, "Puntos por victoria del favorito": v} for k, v in BONUS_FAVORITOS.items()]
    )
    st.dataframe(fav_df, use_container_width=True, hide_index=True)

    st.markdown("### Reglas importantes")
    st.write("Cada participante elige **2 equipos favoritos**. No cambian durante todo el mundial.")
    st.write("Los favoritos otorgan puntos adicionales únicamente por **victoria en tiempo regular**.")
    st.write("Los resultados oficiales siempre se capturan en tiempo regular.")
    st.write("Cada fase tiene fecha límite y se toma la hora de **México**.")
    st.write("Las preguntas de bonus, una vez registradas, quedan fijas para auditoría.")

    visible = config_map.get("ver_pronosticos_ajenos", "0") in ["1", "true", "si", "sí", "x"]
    st.markdown("### Transparencia")
    st.write(
        f"Actualmente {'sí' if visible else 'no'} está habilitada la visibilidad de pronósticos de otros participantes."
    )



def render_admin(data: dict):
    st.title("ADMINISTRACIÓN")
    tab1, tab2, tab3, tab4 = st.tabs([
        "Usuarios",
        "Calendario",
        "Configuración",
        "Bonus",
    ])

    with tab1:
        st.subheader("Alta de participantes")
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            nuevo_nombre = st.text_input("Nombre del usuario")
        with c2:
            nueva_clave = st.text_input("Clave del usuario")
        with c3:
            es_admin = st.checkbox("Es admin")
        if st.button("Crear usuario", use_container_width=True):
            try:
                create_user(data["participantes"], nuevo_nombre, nueva_clave, es_admin)
                st.success("Usuario creado correctamente.")
                st.rerun()
            except Exception as e:
                st.error(str(e))
        st.dataframe(data["participantes"], use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Cargar calendario por CSV")
        file = st.file_uploader("Sube la fase en CSV", type=["csv"])
        if file is not None:
            df_csv = pd.read_csv(file)
            st.dataframe(df_csv.head(10), use_container_width=True)
            if st.button("Guardar calendario en Google Sheets", use_container_width=True):
                try:
                    partidos_new = ingest_calendar_csv(df_csv, data["partidos"])
                    write_sheet(SHEET_PARTIDOS, partidos_new)
                    clear_data_cache()
                    st.success("Calendario guardado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        st.markdown("### Calendario actual")
        st.dataframe(data["partidos"], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Configuración de visibilidad")
        config_map = get_config_map(data["config"])
        default_visible = config_map.get("ver_pronosticos_ajenos", "0") in ["1", "true", "si", "sí", "x"]
        visible = st.checkbox("Permitir ver pronósticos de otros participantes", value=default_visible)
        if st.button("Guardar configuración", use_container_width=True):
            save_config_visibility(data["config"], visible)
            st.success("Configuración guardada.")
            st.rerun()

        st.markdown("### Recalcular puntos")
        if st.button("Recalcular y guardar todos los puntos", use_container_width=True):
            recalculate_and_save_all_points(data)
            st.success("Puntos recalculados y guardados.")
            st.rerun()

    with tab4:
        st.subheader("Configurar bonus por partido")
        partidos = data["partidos"].copy()
        if partidos.empty:
            st.info("Primero carga el calendario.")
        else:
            partidos["label"] = partidos.apply(
                lambda x: f"{x['partido_id']} | {x['local']} vs {x['visitante']} | {x['fase']} | {x['fecha']} {x['hora']}",
                axis=1,
            )
            selected_label = st.selectbox("Selecciona un partido", partidos["label"].tolist())
            row = partidos[partidos["label"] == selected_label].iloc[0]
            partido_id = normalize_text(row["partido_id"])
            pregunta = st.text_input("Pregunta bonus")
            puntos = st.number_input("Puntos bonus", min_value=1, max_value=100, value=1, step=1)
            o1 = st.text_input("Opción 1")
            o2 = st.text_input("Opción 2")
            o3 = st.text_input("Opción 3")
            o4 = st.text_input("Opción 4")
            o5 = st.text_input("Opción 5")
            opciones = [x.strip() for x in [o1, o2, o3, o4, o5] if x.strip()]
            correcta = st.selectbox("Respuesta correcta", options=opciones if opciones else [""])
            if st.button("Guardar bonus del partido", use_container_width=True):
                try:
                    if not pregunta.strip() or len(opciones) < 2:
                        raise RuntimeError("Captura la pregunta y al menos dos opciones.")
                    save_bonus_setup(data["partidos"], partido_id, pregunta, opciones, int(puntos), correcta)
                    st.success("Bonus guardado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))



def render_official_results(data: dict):
    st.title("RESULTADOS OFICIALES FIFA")

    partidos = data["partidos"].copy()
    resultados = data["resultados"].copy()
    if partidos.empty:
        st.info("Aún no hay calendario cargado.")
        return

    partidos["partido_id"] = partidos["partido_id"].astype(str).str.strip()
    resultados["partido_id"] = resultados["partido_id"].astype(str).str.strip()
    merged = partidos.merge(resultados, on="partido_id", how="left", suffixes=("", "_res"))

    fase = st.selectbox("Fase", options=[f for f in FASES_ORDEN if f in merged["fase"].astype(str).unique().tolist()] or merged["fase"].astype(str).unique().tolist())
    df_fase = merged[merged["fase"] == fase].copy()

    st.dataframe(
        df_fase[["partido_id", "grupo", "fecha", "hora", "local", "visitante", "marcador_local", "marcador_visitante"]],
        use_container_width=True,
        hide_index=True,
    )

    if st.session_state.is_admin:
        st.markdown("### Captura de resultados oficiales")
        grupos = sorted(df_fase["grupo"].astype(str).fillna("").unique().tolist())
        if not grupos:
            grupos = ["Fase completa"]
            df_fase["grupo"] = "Fase completa"

        grupo_sel = st.selectbox("Grupo / bloque a capturar", grupos)
        df_block = df_fase[df_fase["grupo"] == grupo_sel].copy()

        for _, row in df_block.iterrows():
            pid = normalize_text(row["partido_id"])
            c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
            with c1:
                st.write(f"**{row['local']}**")
            with c2:
                val_l = st.number_input(
                    f"{pid}_of_l",
                    min_value=0,
                    step=1,
                    value=normalize_int(st.session_state.draft_resultados.get(pid, {}).get("marcador_local"), normalize_int(row.get("marcador_local"), 0) or 0),
                    label_visibility="collapsed",
                )
            with c3:
                val_v = st.number_input(
                    f"{pid}_of_v",
                    min_value=0,
                    step=1,
                    value=normalize_int(st.session_state.draft_resultados.get(pid, {}).get("marcador_visitante"), normalize_int(row.get("marcador_visitante"), 0) or 0),
                    label_visibility="collapsed",
                )
            with c4:
                st.write(f"**{row['visitante']}**")
            st.session_state.draft_resultados[pid] = {
                "marcador_local": val_l,
                "marcador_visitante": val_v,
            }

        if st.button("Guardar resultados oficiales de este bloque", use_container_width=True):
            try:
                save_admin_results_batch(df_block, st.session_state.draft_resultados, data["resultados"])
                recalculate_and_save_all_points(load_all_data())
                st.success("Resultados oficiales guardados.")
                st.rerun()
            except Exception as e:
                st.error(str(e))



def get_user_predictions_view(data: dict, participante: str) -> pd.DataFrame:
    partidos = data["partidos"].copy()
    pron = data["pronosticos"].copy()
    puntos = data["puntos"].copy()
    bonus = data["bonus_puntos"].copy()

    partidos["partido_id"] = partidos["partido_id"].astype(str).str.strip()
    pron["partido_id"] = pron["partido_id"].astype(str).str.strip()
    pron["participante"] = pron["participante"].astype(str).str.strip()
    puntos["partido_id"] = puntos["partido_id"].astype(str).str.strip()
    puntos["participante"] = puntos["participante"].astype(str).str.strip()
    bonus["partido_id"] = bonus["partido_id"].astype(str).str.strip()
    bonus["participante"] = bonus["participante"].astype(str).str.strip()

    df = partidos.merge(pron[pron["participante"] == participante], on="partido_id", how="left")
    df = df.merge(puntos[puntos["participante"] == participante][["partido_id", "puntos_base", "puntos_favorito", "total_partido"]], on="partido_id", how="left")
    df = df.merge(bonus[bonus["participante"] == participante][["partido_id", "puntos_bonus"]], on="partido_id", how="left")
    return df



def render_predictions_capture(data: dict):
    st.title("CAPTURA DE PRONÓSTICOS")

    partidos = data["partidos"].copy()
    pron = data["pronosticos"].copy()
    participantes = data["participantes"].copy()
    user = st.session_state.user_name

    if partidos.empty:
        st.info("Aún no hay calendario cargado.")
        return

    equipos = sorted(set(partidos["local"].astype(str).tolist() + partidos["visitante"].astype(str).tolist()))
    row_user = participantes[participantes["nombre"].astype(str).str.strip() == user]
    favoritos_current = []
    if not row_user.empty:
        favoritos_current = safe_json_load(row_user.iloc[0].get("favoritos_guardados_json"), [])

    st.subheader("Equipos favoritos")
    favoritos = st.multiselect(
        "Selecciona exactamente 2 equipos favoritos",
        options=equipos,
        default=favoritos_current,
        max_selections=2,
    )
    if st.button("Guardar favoritos", use_container_width=True):
        try:
            if len(favoritos) != 2:
                raise RuntimeError("Debes seleccionar exactamente 2 equipos favoritos.")
            save_favoritos(participantes, user, favoritos)
            st.success("Favoritos guardados.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    fase = st.selectbox("Fase", options=[f for f in FASES_ORDEN if f in partidos["fase"].astype(str).unique().tolist()] or partidos["fase"].astype(str).unique().tolist())
    df_fase = partidos[partidos["fase"] == fase].copy()

    grupos = sorted([g for g in df_fase["grupo"].astype(str).fillna("").unique().tolist() if g != ""])
    if not grupos:
        grupos = ["Fase completa"]
        df_fase["grupo"] = "Fase completa"

    grupo = st.selectbox("Grupo / bloque", options=grupos)
    df_group = df_fase[df_fase["grupo"] == grupo].copy()

    pron_user = pron[pron["participante"].astype(str).str.strip() == user].copy()
    pron_user["partido_id"] = pron_user["partido_id"].astype(str).str.strip()

    for _, row in df_group.iterrows():
        pid = normalize_text(row["partido_id"])
        match_dt = parse_match_datetime(row)
        cerrado = match_dt is not None and now_mx() >= match_dt
        existing = pron_user[pron_user["partido_id"] == pid]
        prev_local = normalize_int(existing.iloc[0]["marcador_local"], 0) if not existing.empty else 0
        prev_visit = normalize_int(existing.iloc[0]["marcador_visitante"], 0) if not existing.empty else 0
        draft = st.session_state.draft_pronosticos.get(pid, {})

        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 2, 2])
        with c1:
            st.write(f"**{row['local']}**")
        with c2:
            val_l = st.number_input(
                f"{pid}_pr_l",
                min_value=0,
                step=1,
                value=normalize_int(draft.get("marcador_local"), prev_local) or 0,
                disabled=cerrado,
                label_visibility="collapsed",
            )
        with c3:
            val_v = st.number_input(
                f"{pid}_pr_v",
                min_value=0,
                step=1,
                value=normalize_int(draft.get("marcador_visitante"), prev_visit) or 0,
                disabled=cerrado,
                label_visibility="collapsed",
            )
        with c4:
            st.write(f"**{row['visitante']}**")
        with c5:
            st.caption(f"{row['fecha']} {row['hora']}")
            if cerrado:
                st.caption("Cerrado")
        st.session_state.draft_pronosticos[pid] = {
            "marcador_local": val_l,
            "marcador_visitante": val_v,
        }

    if st.button("Guardar pronósticos de este bloque", use_container_width=True):
        try:
            abiertos = []
            for _, row in df_group.iterrows():
                match_dt = parse_match_datetime(row)
                if match_dt is None or now_mx() < match_dt:
                    abiertos.append(row)
            abiertos_df = pd.DataFrame(abiertos) if abiertos else df_group.iloc[0:0].copy()
            save_user_predictions_batch(user, abiertos_df, st.session_state.draft_pronosticos, data["pronosticos"])
            recalculate_and_save_all_points(load_all_data())
            st.success("Pronósticos guardados correctamente.")
            st.rerun()
        except Exception as e:
            st.error(str(e))



def render_tabla_general(data: dict):
    st.title("TABLA GENERAL DE PARTICIPANTES")

    participantes = data["participantes"].copy()
    puntos = data["puntos"].copy()
    bonus_puntos = data["bonus_puntos"].copy()
    config_map = get_config_map(data["config"])
    visible = config_map.get("ver_pronosticos_ajenos", "0") in ["1", "true", "si", "sí", "x"]

    participantes_list = participantes["nombre"].astype(str).str.strip().tolist()
    resumen_rows = []

    for p in participantes_list:
        dfp = puntos[puntos["participante"].astype(str).str.strip() == p].copy()
        dfb = bonus_puntos[bonus_puntos["participante"].astype(str).str.strip() == p].copy()
        puntos_base = pd.to_numeric(dfp.get("puntos_base", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
        puntos_favorito = pd.to_numeric(dfp.get("puntos_favorito", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
        puntos_bonus = pd.to_numeric(dfb.get("puntos_bonus", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
        total = puntos_base + puntos_favorito + puntos_bonus
        resumen_rows.append(
            {
                "Participante": p,
                "Puntos Base ganados": int(puntos_base),
                "Puntos por favoritos": int(puntos_favorito),
                "Puntos bonus": int(puntos_bonus),
                "Total Puntos Ganados": int(total),
            }
        )

    resumen = pd.DataFrame(resumen_rows)
    if not resumen.empty:
        resumen = resumen.sort_values(by=["Total Puntos Ganados", "Puntos Base ganados"], ascending=False).reset_index(drop=True)
        resumen.insert(0, "Posición", range(1, len(resumen) + 1))
    st.dataframe(resumen, use_container_width=True, hide_index=True)

    if visible or st.session_state.is_admin:
        st.markdown("### Ver pronósticos de un participante")
        participante_sel = st.selectbox("Participante", options=participantes_list)
        detalle = get_user_predictions_view(data, participante_sel)
        cols = [
            "fase",
            "grupo",
            "fecha",
            "hora",
            "local",
            "visitante",
            "marcador_local",
            "marcador_visitante",
            "puntos_base",
            "puntos_favorito",
            "total_partido",
            "puntos_bonus",
        ]
        st.dataframe(detalle[cols], use_container_width=True, hide_index=True)
    else:
        st.info("La visualización de pronósticos de otros participantes aún no está habilitada.")



def render_bonus(data: dict):
    st.title("BONUS")
    partidos = data["partidos"].copy()
    bonus_resp = data["bonus_resp"].copy()
    user = st.session_state.user_name

    if partidos.empty:
        st.info("Aún no hay calendario cargado.")
        return

    partidos["partido_id"] = partidos["partido_id"].astype(str).str.strip()
    habilitados = partidos[
        partidos["bonus_habilitado"].astype(str).str.strip().str.lower().isin(["1", "true", "si", "sí", "x"])
    ].copy()

    if habilitados.empty:
        st.info("Aún no hay bonus registrados.")
        return

    bonus_resp_user = bonus_resp[bonus_resp["participante"].astype(str).str.strip() == user].copy()
    bonus_resp_user["partido_id"] = bonus_resp_user["partido_id"].astype(str).str.strip()

    for _, row in habilitados.iterrows():
        pid = normalize_text(row["partido_id"])
        st.markdown(f"## {row['local']} vs {row['visitante']}")
        st.caption(f"{row['ciudad']} — {row['fase']} — Grupo {row['grupo']} — {row['fecha']} {row['hora']}")
        st.write(row.get("bonus_pregunta", ""))

        opciones = safe_json_load(row.get("bonus_opciones_json"), [])
        prev = bonus_resp_user[bonus_resp_user["partido_id"] == pid]
        prev_val = prev.iloc[0]["respuesta"] if not prev.empty else None
        match_dt = parse_match_datetime(row)
        cerrado = match_dt is not None and now_mx() >= match_dt
        selected = st.radio(
            f"respuesta_{pid}",
            options=opciones,
            index=opciones.index(prev_val) if prev_val in opciones else None,
            disabled=cerrado,
            key=f"bonus_{pid}",
        )
        st.session_state.draft_bonus[pid] = selected
        st.divider()

    if st.button("Guardar respuestas bonus", use_container_width=True):
        try:
            abiertos = []
            for _, row in habilitados.iterrows():
                match_dt = parse_match_datetime(row)
                if match_dt is None or now_mx() < match_dt:
                    abiertos.append(row)
            abiertos_df = pd.DataFrame(abiertos) if abiertos else habilitados.iloc[0:0].copy()
            save_bonus_answers_batch(user, abiertos_df, st.session_state.draft_bonus, data["bonus_resp"])
            recalculate_and_save_all_points(load_all_data())
            st.success("Respuestas bonus guardadas.")
            st.rerun()
        except Exception as e:
            st.error(str(e))


# =========================================================
# BOOTSTRAP OPCIONAL
# =========================================================
def ensure_admin_exists(data: dict):
    participantes = data["participantes"].copy()
    if participantes.empty:
        participantes.loc[len(participantes)] = [
            DEFAULT_ADMIN_USER,
            DEFAULT_ADMIN_PASS,
            "[]",
            "",
            "",
            "1",
        ]
        write_sheet(SHEET_PARTICIPANTES, participantes)
        clear_data_cache()


# =========================================================
# MAIN
# =========================================================
def main():
    init_state()

    if get_conn() is None:
        st.title("Quiniela Mundial 2026")
        render_connection_help()
        return

    data = load_all_data_cached(0)

    if data["participantes"].empty and get_conn() is not None:
        try:
            ensure_admin_exists(data)
            data = load_all_data()
        except Exception:
            pass

    if not st.session_state.logged_in:
        login_box(data["participantes"])
        return

    sidebar_nav()
    data = load_all_data()
    config_map = get_config_map(data["config"])

    if st.session_state.nav == "INICIO":
        render_inicio(config_map)
    elif st.session_state.nav == "ADMINISTRACIÓN":
        render_admin(data)
    elif st.session_state.nav == "RESULTADOS OFICIALES FIFA":
        render_official_results(data)
    elif st.session_state.nav == "CAPTURA DE PRONÓSTICOS":
        render_predictions_capture(data)
    elif st.session_state.nav == "TABLA GENERAL DE PARTICIPANTES":
        render_tabla_general(data)
    elif st.session_state.nav == "BONUS":
        render_bonus(data)


if __name__ == "__main__":
    main()
