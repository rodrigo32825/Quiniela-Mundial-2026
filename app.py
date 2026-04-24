import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

APP_TZ = "America/Mexico_City"
MEXICO_TZ = ZoneInfo(APP_TZ)

SHEET_CONFIG = "configuracion"
SHEET_PARTICIPANTES = "participantes"
SHEET_PARTIDOS = "partidos"
SHEET_PRONOSTICOS = "pronosticos"
SHEET_RESULTADOS = "resultados_oficiales"
SHEET_PUNTOS = "puntos_partido"
SHEET_BONUS_RESP = "bonus_respuestas"
SHEET_BONUS_PUNTOS = "bonus_puntos"

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

DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "admin123"

st.set_page_config(page_title="Quiniela Mundial 2026", layout="wide")


def now_mx() -> datetime:
    return datetime.now(MEXICO_TZ)


def normalize_text(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def normalize_int(value, default=None):
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    if text == "":
        return default
    try:
        return int(float(text))
    except Exception:
        return default


def safe_json_load(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def parse_match_datetime(row) -> datetime | None:
    fecha = normalize_text(row.get("fecha"))
    hora = normalize_text(row.get("hora"))
    if not fecha:
        return None

    candidates = [f"{fecha} {hora}".strip(), fecha]
    formats = ["%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M", "%d/%m/%Y", "%Y-%m-%d"]

    for text in candidates:
        for fmt in formats:
            try:
                dt = datetime.strptime(text, fmt)
                return dt.replace(tzinfo=MEXICO_TZ)
            except Exception:
                pass
    return None


def get_phase_min_datetime(partidos_df: pd.DataFrame, fase: str) -> datetime | None:
    if partidos_df is None or partidos_df.empty:
        return None
    df = partidos_df[partidos_df["fase"].astype(str).str.strip() == str(fase).strip()].copy()
    if df.empty:
        return None
    dts = [parse_match_datetime(row) for _, row in df.iterrows()]
    dts = [dt for dt in dts if dt is not None]
    return min(dts) if dts else None


def is_phase_closed(partidos_df: pd.DataFrame, fase: str) -> bool:
    phase_min_dt = get_phase_min_datetime(partidos_df, fase)
    return phase_min_dt is not None and now_mx() >= phase_min_dt


def sort_partidos_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df.copy()
    out = df.copy()
    out["_fase_order"] = out["fase"].astype(str).apply(lambda x: FASES_ORDEN.index(x) if x in FASES_ORDEN else 999)
    out["_grupo_order"] = out["grupo"].astype(str).fillna("").replace("nan", "")
    out["fecha_partido_dt"] = out.apply(parse_match_datetime, axis=1)
    out["_fecha_sort"] = out["fecha_partido_dt"].apply(lambda x: x if x is not None else datetime.max.replace(tzinfo=MEXICO_TZ))
    out = out.sort_values(by=["_fase_order", "_grupo_order", "_fecha_sort", "partido_id"], ascending=[True, True, True, True])
    return out.drop(columns=["_fase_order", "_grupo_order", "_fecha_sort"], errors="ignore").reset_index(drop=True)


def get_active_bonus_df(partidos_df: pd.DataFrame) -> pd.DataFrame:
    if partidos_df is None or partidos_df.empty:
        return partidos_df.copy()
    df = partidos_df.copy()
    df["partido_id"] = df["partido_id"].astype(str).str.strip()
    df = df[
        df["bonus_habilitado"].astype(str).apply(to_bool)
        & df["bonus_pregunta"].astype(str).str.strip().ne("")
    ].copy()
    if df.empty:
        return df
    df = sort_partidos_df(df)
    df["bonus_resuelto"] = df["bonus_respuesta_correcta"].astype(str).str.strip().ne("")
    return df


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


def serialize_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].fillna("").astype(str)
    return out


def to_bool(value) -> bool:
    text = normalize_text(value).lower()
    if text in ["1", "1.0", "true", "verdadero", "si", "sí", "x", "yes", "y"]:
        return True
    try:
        return float(text) == 1.0
    except Exception:
        return False


def init_state():
    defaults = {
        "logged_in": False,
        "user_name": "",
        "is_admin": False,
        "nav": "INICIO",
        "nav_radio": "INICIO",
        "draft_resultados": {},
        "draft_pronosticos": {},
        "draft_bonus": {},
        "data_nonce": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_conn():
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception:
        return None


def render_connection_help():
    st.error("No se pudo conectar con Google Sheets.")
    st.code(
        '# .streamlit/secrets.toml\n[connections.gsheets]\nspreadsheet = "TU_URL_O_NOMBRE"',
        language="toml",
    )
    st.caption("En tu caso actual puedes seguir usando la URL del archivo QUINIELA 2026 DB en secrets.")


def read_sheet(sheet_name: str, expected_columns: list[str], required: bool = True, retries: int = 3) -> pd.DataFrame:
    conn = get_conn()
    if conn is None:
        if required:
            raise RuntimeError("No se encontró la conexión a Google Sheets.")
        return pd.DataFrame(columns=expected_columns)

    last_error = None
    for attempt in range(retries):
        try:
            df = conn.read(worksheet=sheet_name, ttl=10)
            if df is None:
                return pd.DataFrame(columns=expected_columns)
            df = pd.DataFrame(df)
            df.columns = [normalize_text(c) for c in df.columns]
            df = ensure_columns(df, expected_columns)
            return df.fillna("")
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(0.6 * (attempt + 1))

    if required:
        raise RuntimeError(f"Error leyendo hoja '{sheet_name}': {last_error}")
    return pd.DataFrame(columns=expected_columns)


def write_sheet(sheet_name: str, df: pd.DataFrame, retries: int = 3):
    conn = get_conn()
    if conn is None:
        raise RuntimeError("No se encontró la conexión a Google Sheets.")

    last_error = None
    for attempt in range(retries):
        try:
            conn.update(worksheet=sheet_name, data=serialize_df(df))
            return
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(0.6 * (attempt + 1))

    raise RuntimeError(f"Error escribiendo hoja '{sheet_name}': {last_error}")


def load_all_data():
    return {
        "config": read_sheet(SHEET_CONFIG, ["clave", "valor"], required=True),
        "participantes": read_sheet(
            SHEET_PARTICIPANTES,
            ["nombre", "clave", "favoritos_guardados_json", "fecha_envio", "fecha_envio_iso", "es_admin"],
            required=True,
        ),
        "partidos": read_sheet(
            SHEET_PARTIDOS,
            [
                "partido_id", "fase", "grupo", "fecha", "hora", "ciudad", "estadio",
                "local", "visitante", "deadline_iso", "bonus_habilitado", "bonus_pregunta",
                "bonus_opciones_json", "bonus_puntos", "bonus_respuesta_correcta", "activo",
            ],
            required=True,
        ),
        "pronosticos": read_sheet(
            SHEET_PRONOSTICOS,
            ["participante", "partido_id", "marcador_local", "marcador_visitante", "fecha_guardado_iso"],
            required=False,
        ),
        "resultados": read_sheet(
            SHEET_RESULTADOS,
            ["partido_id", "marcador_local", "marcador_visitante", "fecha_guardado_iso"],
            required=False,
        ),
        "puntos": read_sheet(
            SHEET_PUNTOS,
            [
                "participante", "partido_id", "fase", "acierto_resultado", "exacto",
                "puntos_base", "puntos_favorito", "total_partido", "fecha_calculo_iso",
            ],
            required=False,
        ),
        "bonus_resp": read_sheet(
            SHEET_BONUS_RESP,
            ["participante", "partido_id", "respuesta", "fecha_guardado_iso"],
            required=False,
        ),
        "bonus_puntos": read_sheet(
            SHEET_BONUS_PUNTOS,
            ["participante", "partido_id", "puntos_bonus", "fecha_calculo_iso"],
            required=False,
        ),
    }


@st.cache_data(ttl=15, show_spinner=False)
def load_all_data_cached(cache_nonce: int = 0):
    return load_all_data()


def clear_data_cache():
    load_all_data_cached.clear()
    st.session_state.data_nonce = st.session_state.get("data_nonce", 0) + 1


def get_config_map(config_df: pd.DataFrame) -> dict:
    result = {}
    for _, row in config_df.iterrows():
        result[normalize_text(row.get("clave"))] = normalize_text(row.get("valor"))
    return result


def upsert_config_value(config_df: pd.DataFrame, clave: str, valor: str) -> pd.DataFrame:
    config_df = ensure_columns(config_df, ["clave", "valor"])
    mask = config_df["clave"].astype(str).str.strip().eq(clave)
    if mask.any():
        config_df.loc[mask, "valor"] = valor
    else:
        config_df.loc[len(config_df)] = [clave, valor]
    return config_df


def get_participantes_solo_usuarios(participantes_df: pd.DataFrame) -> pd.DataFrame:
    if participantes_df.empty:
        return participantes_df.copy()
    df = participantes_df.copy()
    return df[~df["es_admin"].apply(to_bool)].reset_index(drop=True)


def validate_login(participantes_df: pd.DataFrame, nombre: str, clave: str):
    nombre = nombre.strip().lower()
    clave = clave.strip()
    if not nombre or not clave:
        return None

    df = participantes_df.copy()
    df["nombre_norm"] = df["nombre"].astype(str).str.strip().str.lower()
    df["clave_norm"] = df["clave"].astype(str).str.strip()

    row = df[(df["nombre_norm"] == nombre) & (df["clave_norm"] == clave)]
    if row.empty:
        return None

    payload = row.iloc[0].to_dict()
    return {"nombre": normalize_text(payload.get("nombre")), "is_admin": to_bool(payload.get("es_admin"))}


def login_box(participantes_df: pd.DataFrame):
    st.title("Quiniela Mundial 2026")
    st.caption("Acceso multiusuario conectado a Google Sheets")

    col1, col2 = st.columns(2)
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


def ensure_admin_exists(data: dict):
    participantes = read_sheet(
        SHEET_PARTICIPANTES,
        ["nombre", "clave", "favoritos_guardados_json", "fecha_envio", "fecha_envio_iso", "es_admin"],
    ).copy()
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


def ingest_calendar_csv(df_csv: pd.DataFrame, partidos_df: pd.DataFrame) -> pd.DataFrame:
    partidos_df = ensure_columns(
        partidos_df,
        [
            "partido_id", "fase", "grupo", "fecha", "hora", "ciudad", "estadio",
            "local", "visitante", "deadline_iso", "bonus_habilitado", "bonus_pregunta",
            "bonus_opciones_json", "bonus_puntos", "bonus_respuesta_correcta", "activo",
        ],
    )
    df = df_csv.copy()
    df.columns = [normalize_text(c).lower() for c in df.columns]

    mapper = {
        "id": "partido_id",
        "partido_id": "partido_id",
        "fase": "fase",
        "grupo": "grupo",
        "fecha": "fecha",
        "hora": "hora",
        "ciudad": "ciudad",
        "estadio": "estadio",
        "local": "local",
        "visitante": "visitante",
    }

    normalized = pd.DataFrame()
    for source, target in mapper.items():
        if source in df.columns:
            normalized[target] = df[source]

    needed = ["partido_id", "fase", "grupo", "fecha", "hora", "ciudad", "estadio", "local", "visitante"]
    for col in needed:
        if col not in normalized.columns:
            normalized[col] = ""
    normalized = normalized[needed].copy()

    for col in needed:
        normalized[col] = normalized[col].astype(str).str.strip()

    normalized["deadline_iso"] = ""
    normalized["bonus_habilitado"] = "0"
    normalized["bonus_pregunta"] = ""
    normalized["bonus_opciones_json"] = "[]"
    normalized["bonus_puntos"] = "0"
    normalized["bonus_respuesta_correcta"] = ""
    normalized["activo"] = "1"

    for idx, row in normalized.iterrows():
        dt = parse_match_datetime(row)
        normalized.loc[idx, "deadline_iso"] = dt.isoformat() if dt else ""

    partidos_df["partido_id"] = partidos_df["partido_id"].astype(str).str.strip()

    for _, row in normalized.iterrows():
        pid = normalize_text(row["partido_id"])
        if not pid:
            continue
        mask = partidos_df["partido_id"] == pid
        if mask.any():
            preserve_cols = [
                "bonus_habilitado", "bonus_pregunta", "bonus_opciones_json",
                "bonus_puntos", "bonus_respuesta_correcta", "activo",
            ]
            for col in normalized.columns:
                if col not in preserve_cols:
                    partidos_df.loc[mask, col] = row[col]
        else:
            partidos_df.loc[len(partidos_df)] = row.tolist()

    partidos_df = partidos_df.drop_duplicates(subset=["partido_id"], keep="last")
    return sort_partidos_df(partidos_df)


def result_type(local: int, visitante: int) -> str:
    if local > visitante:
        return "L"
    if visitante > local:
        return "V"
    return "E"


def puntos_partido(pron_local: int, pron_visit: int, of_local: int, of_visit: int) -> dict:
    acierto = int(result_type(pron_local, pron_visit) == result_type(of_local, of_visit))
    exacto = int(pron_local == of_local and pron_visit == of_visit)
    puntos_base = acierto * 1 + exacto * 2
    return {"acierto_resultado": acierto, "exacto": exacto, "puntos_base": puntos_base}


def recompute_points(data: dict):
    participantes = get_participantes_solo_usuarios(data["participantes"])
    partidos = data["partidos"].copy()
    pronosticos = data["pronosticos"].copy()
    resultados = data["resultados"].copy()
    bonus_resp = data["bonus_resp"].copy()

    puntos_cols = [
        "participante", "partido_id", "fase", "acierto_resultado", "exacto",
        "puntos_base", "puntos_favorito", "total_partido", "fecha_calculo_iso",
    ]
    bonus_cols = ["participante", "partido_id", "puntos_bonus", "fecha_calculo_iso"]

    if partidos.empty or resultados.empty or pronosticos.empty:
        return pd.DataFrame(columns=puntos_cols), pd.DataFrame(columns=bonus_cols)

    favoritos_map = {}
    for _, row in participantes.iterrows():
        favoritos_map[normalize_text(row.get("nombre"))] = safe_json_load(row.get("favoritos_guardados_json"), [])

    partidos["partido_id"] = partidos["partido_id"].astype(str).str.strip()
    pronosticos["partido_id"] = pronosticos["partido_id"].astype(str).str.strip()
    pronosticos["participante"] = pronosticos["participante"].astype(str).str.strip()
    resultados["partido_id"] = resultados["partido_id"].astype(str).str.strip()

    merged = pronosticos.merge(resultados, on="partido_id", how="inner", suffixes=("_pron", "_of"))
    merged = merged.merge(partidos[["partido_id", "fase", "local", "visitante"]], on="partido_id", how="left")

    ts = now_mx().isoformat()
    puntos_rows = []

    for _, row in merged.iterrows():
        participante = normalize_text(row.get("participante"))
        if participante not in favoritos_map:
            continue

        partido_id = normalize_text(row.get("partido_id"))
        fase = normalize_text(row.get("fase"))

        p_local = normalize_int(row.get("marcador_local_pron"), 0) or 0
        p_visit = normalize_int(row.get("marcador_visitante_pron"), 0) or 0
        o_local = normalize_int(row.get("marcador_local_of"), 0) or 0
        o_visit = normalize_int(row.get("marcador_visitante_of"), 0) or 0

        calc = puntos_partido(p_local, p_visit, o_local, o_visit)

        favorito_pts = 0
        favoritos = favoritos_map.get(participante, [])
        local = normalize_text(row.get("local"))
        visitante = normalize_text(row.get("visitante"))

        ganador = ""
        if o_local > o_visit:
            ganador = local
        elif o_visit > o_local:
            ganador = visitante

        favoritos_normalizados = [str(f).strip().lower() for f in favoritos]
        ganador_normalizado = ganador.strip().lower() if ganador else ""

        fase_normalizada = fase.strip().lower()
        bonus_map = {k.strip().lower(): v for k, v in BONUS_FAVORITOS.items()}

        if ganador and ganador_normalizado in favoritos_normalizados:
            favorito_pts = bonus_map.get(fase_normalizada, 0)

        total = calc["puntos_base"] + favorito_pts

        puntos_rows.append(
            {
                "participante": participante,
                "partido_id": partido_id,
                "fase": fase,
                "acierto_resultado": str(calc["acierto_resultado"]),
                "exacto": str(calc["exacto"]),
                "puntos_base": str(calc["puntos_base"]),
                "puntos_favorito": str(favorito_pts),
                "total_partido": str(total),
                "fecha_calculo_iso": ts,
            }
        )

    bonus_rows = []
    if not bonus_resp.empty and not partidos.empty:
        bonus_resp["participante"] = bonus_resp["participante"].astype(str).str.strip()
        bonus_resp["partido_id"] = bonus_resp["partido_id"].astype(str).str.strip()

        for _, row in bonus_resp.iterrows():
            participante = normalize_text(row.get("participante"))
            if participante not in favoritos_map:
                continue

            partido_id = normalize_text(row.get("partido_id"))
            respuesta = normalize_text(row.get("respuesta"))
            match = partidos[partidos["partido_id"] == partido_id]
            if match.empty:
                continue

            p_row = match.iloc[0]
            if not to_bool(p_row.get("bonus_habilitado")):
                continue

            correcta = normalize_text(p_row.get("bonus_respuesta_correcta"))
            bonus_pts = normalize_int(p_row.get("bonus_puntos"), 0) or 0
            otorgado = bonus_pts if correcta and respuesta == correcta else 0

            bonus_rows.append(
                {
                    "participante": participante,
                    "partido_id": partido_id,
                    "puntos_bonus": str(otorgado),
                    "fecha_calculo_iso": ts,
                }
            )

    puntos_df = pd.DataFrame(puntos_rows, columns=puntos_cols).drop_duplicates(
        subset=["participante", "partido_id"], keep="last"
    )
    bonus_df = pd.DataFrame(bonus_rows, columns=bonus_cols).drop_duplicates(
        subset=["participante", "partido_id"], keep="last"
    )
    return puntos_df, bonus_df


def save_admin_results_batch(partidos_block: pd.DataFrame, draft: dict, resultados_df: pd.DataFrame):
    resultados_df = ensure_columns(resultados_df, ["partido_id", "marcador_local", "marcador_visitante", "fecha_guardado_iso"])
    resultados_df["partido_id"] = resultados_df["partido_id"].astype(str).str.strip()
    ts = now_mx().isoformat()

    for _, row in partidos_block.iterrows():
        pid = normalize_text(row.get("partido_id"))
        if pid not in draft:
            continue
        local = draft[pid].get("marcador_local")
        visitante = draft[pid].get("marcador_visitante")
        if local in [None, ""] or visitante in [None, ""]:
            continue

        mask = resultados_df["partido_id"] == pid
        if mask.any():
            resultados_df.loc[mask, ["marcador_local", "marcador_visitante", "fecha_guardado_iso"]] = [
                str(local), str(visitante), ts
            ]
        else:
            resultados_df.loc[len(resultados_df)] = [pid, str(local), str(visitante), ts]

    resultados_df = resultados_df.drop_duplicates(subset=["partido_id"], keep="last")
    write_sheet(SHEET_RESULTADOS, resultados_df)
    clear_data_cache()


def save_user_predictions_batch(participante: str, partidos_block: pd.DataFrame, draft: dict, pronosticos_df: pd.DataFrame):
    pronosticos_df = ensure_columns(
        pronosticos_df,
        ["participante", "partido_id", "marcador_local", "marcador_visitante", "fecha_guardado_iso"],
    )
    pronosticos_df["participante"] = pronosticos_df["participante"].astype(str).str.strip()
    pronosticos_df["partido_id"] = pronosticos_df["partido_id"].astype(str).str.strip()
    ts = now_mx().isoformat()

    for _, row in partidos_block.iterrows():
        pid = normalize_text(row.get("partido_id"))
        if pid not in draft:
            continue
        local = draft[pid].get("marcador_local")
        visitante = draft[pid].get("marcador_visitante")
        if local in [None, ""] or visitante in [None, ""]:
            continue

        mask = (pronosticos_df["participante"] == participante) & (pronosticos_df["partido_id"] == pid)
        if mask.any():
            pronosticos_df.loc[mask, ["marcador_local", "marcador_visitante", "fecha_guardado_iso"]] = [
                str(local), str(visitante), ts
            ]
        else:
            pronosticos_df.loc[len(pronosticos_df)] = [participante, pid, str(local), str(visitante), ts]

    pronosticos_df = pronosticos_df.drop_duplicates(subset=["participante", "partido_id"], keep="last")
    write_sheet(SHEET_PRONOSTICOS, pronosticos_df)
    clear_data_cache()


def save_bonus_answers_batch(participante: str, partidos_bonus: pd.DataFrame, draft: dict, bonus_df: pd.DataFrame):
    bonus_df = ensure_columns(bonus_df, ["participante", "partido_id", "respuesta", "fecha_guardado_iso"])
    bonus_df["participante"] = bonus_df["participante"].astype(str).str.strip()
    bonus_df["partido_id"] = bonus_df["partido_id"].astype(str).str.strip()
    ts = now_mx().isoformat()

    for _, row in partidos_bonus.iterrows():
        pid = normalize_text(row.get("partido_id"))
        if pid not in draft:
            continue
        answer = normalize_text(draft.get(pid))
        if not answer:
            continue

        mask = (bonus_df["participante"] == participante) & (bonus_df["partido_id"] == pid)

        # Si el participante ya respondió este bonus, no permitir modificación.
        if mask.any():
            continue

        bonus_df.loc[len(bonus_df)] = [participante, pid, answer, ts]

    bonus_df = bonus_df.drop_duplicates(subset=["participante", "partido_id"], keep="first")
    write_sheet(SHEET_BONUS_RESP, bonus_df)
    clear_data_cache()


def save_favoritos(participantes_df: pd.DataFrame, participante: str, favoritos: list[str]):
    participantes_df = read_sheet(
        SHEET_PARTICIPANTES,
        ["nombre", "clave", "favoritos_guardados_json", "fecha_envio", "fecha_envio_iso", "es_admin"],
    )
    participantes_df = ensure_columns(
        participantes_df,
        ["nombre", "clave", "favoritos_guardados_json", "fecha_envio", "fecha_envio_iso", "es_admin"],
    )

    if participantes_df.empty:
        raise RuntimeError("Protección activada: no se puede sobrescribir una hoja participantes vacía.")

    mask = participantes_df["nombre"].astype(str).str.strip().eq(participante)
    if not mask.any():
        raise RuntimeError("Participante no encontrado.")

    participantes_df.loc[mask, "favoritos_guardados_json"] = json.dumps(favoritos, ensure_ascii=False)
    participantes_df.loc[mask, "fecha_envio"] = now_mx().strftime("%d/%m/%Y %H:%M")
    participantes_df.loc[mask, "fecha_envio_iso"] = now_mx().isoformat()
    write_sheet(SHEET_PARTICIPANTES, participantes_df)
    clear_data_cache()


def create_user(participantes_df: pd.DataFrame, nombre: str, clave: str):
    participantes_df = read_sheet(
        SHEET_PARTICIPANTES,
        ["nombre", "clave", "favoritos_guardados_json", "fecha_envio", "fecha_envio_iso", "es_admin"],
    )
    participantes_df = ensure_columns(
        participantes_df,
        ["nombre", "clave", "favoritos_guardados_json", "fecha_envio", "fecha_envio_iso", "es_admin"],
    )

    if participantes_df.empty:
        raise RuntimeError("Protección activada: no se puede sobrescribir una hoja participantes vacía.")

    nombre = nombre.strip()
    clave = clave.strip()
    if not nombre or not clave:
        raise RuntimeError("Nombre y clave son obligatorios.")

    existing = participantes_df[participantes_df["nombre"].astype(str).str.strip().str.lower() == nombre.lower()]
    if not existing.empty:
        raise RuntimeError("Ese usuario ya existe.")

    participantes_df.loc[len(participantes_df)] = [nombre, clave, "[]", "", "", "0"]
    write_sheet(SHEET_PARTICIPANTES, participantes_df)
    clear_data_cache()


def save_config_visibility(config_df: pd.DataFrame, visible: bool):
    config_df = upsert_config_value(config_df, "ver_pronosticos_ajenos", "1" if visible else "0")
    write_sheet(SHEET_CONFIG, config_df)
    clear_data_cache()


def save_bonus_setup(partidos_df: pd.DataFrame, partido_id: str, pregunta: str, opciones: list[str], puntos: int):
    partidos_df = ensure_columns(
        partidos_df,
        [
            "partido_id", "fase", "grupo", "fecha", "hora", "ciudad", "estadio",
            "local", "visitante", "deadline_iso", "bonus_habilitado", "bonus_pregunta",
            "bonus_opciones_json", "bonus_puntos", "bonus_respuesta_correcta", "activo",
        ],
    )
    mask = partidos_df["partido_id"].astype(str).str.strip().eq(str(partido_id).strip())
    if not mask.any():
        raise RuntimeError("Partido no encontrado.")

    partidos_df.loc[mask, "bonus_habilitado"] = "1"
    partidos_df.loc[mask, "bonus_pregunta"] = pregunta.strip()
    partidos_df.loc[mask, "bonus_opciones_json"] = json.dumps(opciones, ensure_ascii=False)
    partidos_df.loc[mask, "bonus_puntos"] = str(int(puntos))
    partidos_df.loc[mask, "bonus_respuesta_correcta"] = ""
    write_sheet(SHEET_PARTIDOS, partidos_df)
    clear_data_cache()


def save_bonus_correct_answer(partidos_df: pd.DataFrame, partido_id: str, respuesta_correcta: str):
    partidos_df = ensure_columns(
        partidos_df,
        [
            "partido_id", "fase", "grupo", "fecha", "hora", "ciudad", "estadio",
            "local", "visitante", "deadline_iso", "bonus_habilitado", "bonus_pregunta",
            "bonus_opciones_json", "bonus_puntos", "bonus_respuesta_correcta", "activo",
        ],
    )
    mask = partidos_df["partido_id"].astype(str).str.strip().eq(str(partido_id).strip())
    if not mask.any():
        raise RuntimeError("Bonus activo no encontrado.")

    if not normalize_text(respuesta_correcta):
        raise RuntimeError("Debes seleccionar la respuesta correcta.")

    partidos_df.loc[mask, "bonus_respuesta_correcta"] = respuesta_correcta.strip()
    write_sheet(SHEET_PARTIDOS, partidos_df)
    clear_data_cache()


def recalculate_and_save_all_points(data: dict):
    puntos_df, bonus_df = recompute_points(data)
    write_sheet(SHEET_PUNTOS, puntos_df)
    write_sheet(SHEET_BONUS_PUNTOS, bonus_df)
    clear_data_cache()


def sidebar_nav():
    st.sidebar.image("Logo mundial numerico.png", width=180)
    st.sidebar.markdown("---")
    st.sidebar.title("Menú")
    options = ["INICIO", "RESULTADOS OFICIALES FIFA", "TABLA GENERAL DE PARTICIPANTES", "BONUS"]
    if st.session_state.is_admin:
        options.insert(1, "ADMINISTRACIÓN")
    else:
        options.insert(1, "CAPTURA DE PRONÓSTICOS")

    if st.session_state.get("nav_radio") not in options:
        st.session_state.nav_radio = st.session_state.nav if st.session_state.nav in options else options[0]

    selected = st.sidebar.radio("Ir a", options, key="nav_radio")

    if selected != st.session_state.nav:
        st.session_state.nav = selected
        st.rerun()

    st.sidebar.divider()
    st.sidebar.write(f"**Usuario:** {st.session_state.user_name}")
    st.sidebar.write(f"**Rol:** {'Administrador' if st.session_state.is_admin else 'Participante'}")
    if st.session_state.is_admin:
        st.sidebar.success("Sesión de administrador activa")
    st.sidebar.caption("Modo de lectura optimizado para Google Sheets")

    if st.sidebar.button("Cerrar sesión", use_container_width=True):
        keys_to_clear = [
            "logged_in",
            "user_name",
            "is_admin",
            "nav",
            "nav_radio",
            "draft_resultados",
            "draft_pronosticos",
            "draft_bonus",
            "data_nonce",
        ]
        for k in keys_to_clear:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()


def render_inicio(config_map: dict):
    st.title("INICIO")
    st.subheader("Cómo funciona la quiniela")
    st.write("Cada participante captura sus pronósticos por bloque y los guarda manualmente. Así evitamos recargas innecesarias y reducimos conflictos multiusuario.")

    st.markdown("### Puntos base")
    st.write("Aciertas ganador o empate: **1 punto**")
    st.write("Aciertas marcador exacto: **+2 puntos**")
    st.write("Total por marcador exacto: **3 puntos**")

    st.markdown("### Bonus por equipos favoritos")
    fav_df = pd.DataFrame(
        [{"Fase": fase, "Puntos extra por victoria del favorito": pts} for fase, pts in BONUS_FAVORITOS.items()]
    )
    st.dataframe(fav_df, use_container_width=True, hide_index=True)

    st.markdown("### Reglas importantes")
    st.write("Cada participante elige **2 equipos favoritos** y no cambian durante todo el mundial.")
    st.write("Los favoritos dan puntos extra solo por **victoria en tiempo regular**.")
    st.write("Los resultados oficiales también se capturan en tiempo regular.")
    st.write("Cada fase se bloquea con base en la fecha mínima de esa fase, usando la hora de **México**.")
    st.write("Las preguntas bonus quedan fijas una vez guardadas.")

    visible = to_bool(config_map.get("ver_pronosticos_ajenos", "0"))
    st.markdown("### Transparencia")
    st.write(f"Actualmente {'sí' if visible else 'no'} está habilitada la visualización de pronósticos de otros participantes.")


def render_admin(data: dict):
    st.title("ADMINISTRACIÓN")
    tab1, tab2, tab3, tab4 = st.tabs(["Usuarios", "Calendario", "Configuración", "Bonus"])

    with tab1:
        st.subheader("Alta de participantes")
        c1, c2 = st.columns(2)
        with c1:
            nuevo_nombre = st.text_input("Nombre del usuario")
        with c2:
            nueva_clave = st.text_input("Clave del usuario")

        if st.button("Crear usuario", use_container_width=True):
            try:
                create_user(data["participantes"], nuevo_nombre, nueva_clave)
                st.success("Usuario creado correctamente.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.markdown("### Participantes")
        st.dataframe(get_participantes_solo_usuarios(data["participantes"]), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Cargar calendario por CSV")
        file = st.file_uploader("Sube la fase en CSV", type=["csv"])
        if file is not None:
            try:
                df_csv = pd.read_csv(file)
            except Exception:
                file.seek(0)
                df_csv = pd.read_csv(file, encoding="latin-1")
            st.dataframe(df_csv.head(10), use_container_width=True, hide_index=True)
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
        calendario_actual = sort_partidos_df(data["partidos"]).copy()
        if "fecha_partido_dt" in calendario_actual.columns:
            calendario_actual = calendario_actual.drop(columns=["fecha_partido_dt"], errors="ignore")
        st.dataframe(calendario_actual, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Configuración")
        config_map = get_config_map(data["config"])
        visible_default = to_bool(config_map.get("ver_pronosticos_ajenos", "0"))
        visible = st.checkbox("Permitir ver pronósticos de otros participantes", value=visible_default)

        if st.button("Guardar configuración", use_container_width=True):
            save_config_visibility(data["config"], visible)
            st.success("Configuración guardada.")
            st.rerun()

        st.divider()
        st.subheader("Auditoría / recalcular")
        if st.button("Recalcular y guardar todos los puntos", use_container_width=True):
            recalculate_and_save_all_points(load_all_data_cached(st.session_state.get("data_nonce", 0)))
            st.success("Puntos recalculados y guardados.")
            st.rerun()

    with tab4:
        st.subheader("Administración de bonus")
        partidos = data["partidos"].copy()
        bonus_resp = data["bonus_resp"].copy()

        if partidos.empty:
            st.info("Primero carga el calendario.")
            return

        partidos["label"] = partidos.apply(
            lambda x: f"{x['partido_id']} | {x['local']} vs {x['visitante']} | {x['fase']} | {x['fecha']} {x['hora']}",
            axis=1,
        )

        st.markdown("### Bloque 1: Configurar bonus")
        selected_label = st.selectbox("Selecciona un partido para activar bonus", partidos["label"].tolist())
        row = partidos[partidos["label"] == selected_label].iloc[0]
        partido_id = normalize_text(row.get("partido_id"))

        pregunta = st.text_input("Pregunta bonus")
        puntos = st.number_input("Puntos bonus", min_value=1, max_value=100, value=1, step=1)
        o1 = st.text_input("Opción 1")
        o2 = st.text_input("Opción 2")
        o3 = st.text_input("Opción 3")
        o4 = st.text_input("Opción 4")
        o5 = st.text_input("Opción 5")
        opciones = [x.strip() for x in [o1, o2, o3, o4, o5] if x.strip()]

        if st.button("Guardar configuración bonus", use_container_width=True):
            try:
                if not pregunta.strip() or len(opciones) < 2:
                    raise RuntimeError("Captura la pregunta y al menos dos opciones.")
                save_bonus_setup(data["partidos"], partido_id, pregunta, opciones, int(puntos))
                st.success("Bonus guardado correctamente.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.divider()
        st.markdown("### Bloque 2: Resolver bonus activo")

        bonus_activos = get_active_bonus_df(partidos)

        if bonus_activos.empty:
            st.info("Aún no hay bonuses activos configurados.")
        else:
            mostrar_resueltos = st.checkbox("Mostrar también bonuses ya resueltos", value=False)

            if not mostrar_resueltos:
                bonus_activos = bonus_activos[~bonus_activos["bonus_resuelto"]].copy()

            if bonus_activos.empty:
                st.info("No hay bonuses activos pendientes por resolver.")
            else:
                bonus_activos["label_bonus"] = bonus_activos.apply(
                    lambda x: (
                        f"{x['partido_id']} | {x['local']} vs {x['visitante']} | "
                        f"{x['fase']} | {normalize_text(x.get('bonus_pregunta'))}"
                    ),
                    axis=1,
                )

                selected_bonus = st.selectbox(
                    "Selecciona un bonus activo",
                    options=bonus_activos["label_bonus"].tolist(),
                    key="resolver_bonus_select",
                )

                bonus_row = bonus_activos[bonus_activos["label_bonus"] == selected_bonus].iloc[0]
                bonus_pid = normalize_text(bonus_row.get("partido_id"))
                bonus_opciones = safe_json_load(bonus_row.get("bonus_opciones_json"), [])

                respuestas_count = 0
                if not bonus_resp.empty:
                    respuestas_count = len(
                        bonus_resp[bonus_resp["partido_id"].astype(str).str.strip() == bonus_pid]
                    )

                st.caption(f"Partido: {bonus_row['local']} vs {bonus_row['visitante']}")
                st.caption(f"Fase: {bonus_row['fase']} | Grupo: {bonus_row['grupo']}")
                st.write(f"**Pregunta:** {normalize_text(bonus_row.get('bonus_pregunta'))}")
                st.write(f"**Opciones:** {', '.join(bonus_opciones) if bonus_opciones else 'Sin opciones'}")
                st.write(f"**Puntos bonus:** {normalize_text(bonus_row.get('bonus_puntos'))}")
                st.write(f"**Respuestas registradas:** {respuestas_count}")
                estado_bonus = "Resuelto" if to_bool(bonus_row.get("bonus_resuelto")) else "Pendiente de resolver"
                st.write(f"**Estatus:** {estado_bonus}")

                respuesta_correcta = st.selectbox(
                    "Respuesta correcta",
                    options=bonus_opciones if bonus_opciones else [""],
                    key=f"correcta_{bonus_pid}",
                )

                if st.button("Guardar respuesta correcta y recalcular bonus", use_container_width=True):
                    try:
                        save_bonus_correct_answer(data["partidos"], bonus_pid, respuesta_correcta)
                        recalculate_and_save_all_points(load_all_data_cached(st.session_state.get("data_nonce", 0)))
                        st.success("Bonus resuelto y puntos recalculados.")
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
    merged = sort_partidos_df(merged)
    fases_presentes = [f for f in FASES_ORDEN if f in merged["fase"].astype(str).unique().tolist()]
    if not fases_presentes:
        fases_presentes = merged["fase"].astype(str).unique().tolist()

    fase = st.selectbox("Fase", options=fases_presentes)
    df_fase = sort_partidos_df(merged[merged["fase"] == fase].copy())

    st.dataframe(
        df_fase[["partido_id", "grupo", "fecha", "hora", "local", "visitante", "marcador_local", "marcador_visitante"]],
        use_container_width=True,
        hide_index=True,
    )

    if not st.session_state.is_admin:
        return

    st.markdown("### Captura de resultados oficiales")
    grupos = sorted([g for g in df_fase["grupo"].astype(str).fillna("").unique().tolist() if g != ""])
    if not grupos:
        grupos = ["Fase completa"]
        df_fase["grupo"] = "Fase completa"

    grupo_sel = st.selectbox("Grupo / bloque a capturar", grupos)
    df_block = df_fase[df_fase["grupo"] == grupo_sel].copy()

    for _, row in df_block.iterrows():
        pid = normalize_text(row.get("partido_id"))
        prev_local = normalize_int(row.get("marcador_local"), 0) or 0
        prev_visit = normalize_int(row.get("marcador_visitante"), 0) or 0
        draft_local = normalize_int(st.session_state.draft_resultados.get(pid, {}).get("marcador_local"), prev_local) or 0
        draft_visit = normalize_int(st.session_state.draft_resultados.get(pid, {}).get("marcador_visitante"), prev_visit) or 0

        c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
        with c1:
            st.write(f"**{row['local']}**")
        with c2:
            val_l = st.number_input(f"res_l_{pid}", min_value=0, step=1, value=draft_local, label_visibility="collapsed")
        with c3:
            val_v = st.number_input(f"res_v_{pid}", min_value=0, step=1, value=draft_visit, label_visibility="collapsed")
        with c4:
            st.write(f"**{row['visitante']}**")

        st.session_state.draft_resultados[pid] = {"marcador_local": val_l, "marcador_visitante": val_v}

    if st.button("Guardar resultados oficiales de este bloque", use_container_width=True):
        try:
            save_admin_results_batch(df_block, st.session_state.draft_resultados, data["resultados"])
            recalculate_and_save_all_points(load_all_data_cached(st.session_state.get("data_nonce", 0)))
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
    df = df.merge(
        puntos[puntos["participante"] == participante][["partido_id", "puntos_base", "puntos_favorito", "total_partido"]],
        on="partido_id",
        how="left",
    )
    df = df.merge(
        bonus[bonus["participante"] == participante][["partido_id", "puntos_bonus"]],
        on="partido_id",
        how="left",
    )
    return sort_partidos_df(df)


def render_predictions_capture(data: dict):
    st.title("CAPTURA DE PRONÓSTICOS")

    partidos = sort_partidos_df(data["partidos"].copy())
    pron = data["pronosticos"].copy()
    participantes = get_participantes_solo_usuarios(data["participantes"])
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
            save_favoritos(data["participantes"], user, favoritos)
            st.success("Favoritos guardados.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    fases_presentes = [f for f in FASES_ORDEN if f in partidos["fase"].astype(str).unique().tolist()]
    if not fases_presentes:
        fases_presentes = partidos["fase"].astype(str).unique().tolist()

    fase = st.selectbox("Fase", options=fases_presentes)
    df_fase = sort_partidos_df(partidos[partidos["fase"] == fase].copy())
    fase_cerrada = is_phase_closed(partidos, fase)
    fecha_min_fase = get_phase_min_datetime(partidos, fase)

    if fecha_min_fase is not None:
        st.caption(
            f"Fecha mínima de cierre para esta fase: {fecha_min_fase.strftime('%d/%m/%Y %H:%M')} (hora de México)"
        )
    st.caption("Fase cerrada" if fase_cerrada else "Fase abierta")

    grupos = sorted([g for g in df_fase["grupo"].astype(str).fillna("").unique().tolist() if g != ""])
    if not grupos:
        grupos = ["Fase completa"]
        df_fase["grupo"] = "Fase completa"

    grupo = st.selectbox("Grupo / bloque", options=grupos)
    df_block = sort_partidos_df(df_fase[df_fase["grupo"] == grupo].copy())

    pron_user = pron[pron["participante"].astype(str).str.strip() == user].copy()
    pron_user["partido_id"] = pron_user["partido_id"].astype(str).str.strip()

    for _, row in df_block.iterrows():
        pid = normalize_text(row.get("partido_id"))
        existing = pron_user[pron_user["partido_id"] == pid]
        prev_local = normalize_int(existing.iloc[0]["marcador_local"], 0) if not existing.empty else 0
        prev_visit = normalize_int(existing.iloc[0]["marcador_visitante"], 0) if not existing.empty else 0

        draft_local = normalize_int(st.session_state.draft_pronosticos.get(pid, {}).get("marcador_local"), prev_local) or 0
        draft_visit = normalize_int(st.session_state.draft_pronosticos.get(pid, {}).get("marcador_visitante"), prev_visit) or 0

        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 2, 2])
        with c1:
            st.write(f"**{row['local']}**")
        with c2:
            val_l = st.number_input(f"pr_l_{pid}", min_value=0, step=1, value=draft_local, disabled=fase_cerrada, label_visibility="collapsed")
        with c3:
            val_v = st.number_input(f"pr_v_{pid}", min_value=0, step=1, value=draft_visit, disabled=fase_cerrada, label_visibility="collapsed")
        with c4:
            st.write(f"**{row['visitante']}**")
        with c5:
            st.caption(f"{row['fecha']} {row['hora']}")
            st.caption("Cerrado" if fase_cerrada else "Abierto")

        st.session_state.draft_pronosticos[pid] = {"marcador_local": val_l, "marcador_visitante": val_v}

    if st.button("Guardar pronósticos de este bloque", use_container_width=True, disabled=fase_cerrada):
        try:
            abiertos_df = df_block.iloc[0:0].copy() if fase_cerrada else df_block.copy()
            save_user_predictions_batch(user, abiertos_df, st.session_state.draft_pronosticos, data["pronosticos"])
            st.success("Pronósticos guardados correctamente.")
            st.rerun()
        except Exception as e:
            st.error(str(e))


def render_tabla_general(data: dict):
    st.title("TABLA GENERAL DE PARTICIPANTES")

    participantes = get_participantes_solo_usuarios(data["participantes"])
    puntos = data["puntos"].copy()
    bonus_puntos = data["bonus_puntos"].copy()
    config_map = get_config_map(data["config"])
    visible = to_bool(config_map.get("ver_pronosticos_ajenos", "0"))

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
        if participantes_list:
            participante_sel = st.selectbox("Participante", options=participantes_list)
            detalle = get_user_predictions_view(data, participante_sel)
            cols = [
                "fase", "grupo", "fecha", "hora", "local", "visitante", "marcador_local",
                "marcador_visitante", "puntos_base", "puntos_favorito", "total_partido", "puntos_bonus",
            ]
            cols_exist = [c for c in cols if c in detalle.columns]
            st.dataframe(detalle[cols_exist], use_container_width=True, hide_index=True)
    else:
        st.info("La visualización de pronósticos de otros participantes aún no está habilitada.")


def render_bonus(data: dict):
    st.title("BONUS")

    partidos = sort_partidos_df(data["partidos"].copy())
    bonus_resp = data["bonus_resp"].copy()
    user = st.session_state.user_name
    is_admin = st.session_state.is_admin

    if partidos.empty:
        st.info("Aún no hay calendario cargado.")
        return

    partidos["partido_id"] = partidos["partido_id"].astype(str).str.strip()
    bonus_resp["partido_id"] = bonus_resp.get("partido_id", pd.Series(dtype=str)).astype(str).str.strip() if not bonus_resp.empty else pd.Series(dtype=str)
    bonus_resp["participante"] = bonus_resp.get("participante", pd.Series(dtype=str)).astype(str).str.strip() if not bonus_resp.empty else pd.Series(dtype=str)

    bonus_activos = get_active_bonus_df(partidos)
    bonus_pendientes = bonus_activos[~bonus_activos["bonus_resuelto"]].copy() if not bonus_activos.empty else bonus_activos.copy()

    if not bonus_pendientes.empty:
        st.subheader("Bonus activo")

        if not is_admin:
            bonus_resp_user = bonus_resp[bonus_resp["participante"] == user].copy() if not bonus_resp.empty else pd.DataFrame(columns=["participante", "partido_id", "respuesta", "fecha_guardado_iso"])

            for _, row in bonus_pendientes.iterrows():
                pid = normalize_text(row.get("partido_id"))
                opciones = safe_json_load(row.get("bonus_opciones_json"), [])
                prev = bonus_resp_user[bonus_resp_user["partido_id"] == pid]
                prev_val = normalize_text(prev.iloc[0].get("respuesta")) if not prev.empty else ""
                ya_respondio = bool(prev_val)
                fase = normalize_text(row.get("fase"))
                fase_cerrada = is_phase_closed(partidos, fase)
                bloqueado = fase_cerrada or ya_respondio

                st.markdown(f"## {row['local']} vs {row['visitante']}")
                st.caption(f"{row['fase']} | Grupo {row['grupo']} | {row['fecha']} {row['hora']}")
                st.write(normalize_text(row.get("bonus_pregunta")))

                if opciones:
                    draft_val = normalize_text(st.session_state.draft_bonus.get(pid))
                    selected_value = prev_val if ya_respondio else draft_val
                    index = opciones.index(selected_value) if selected_value in opciones else 0

                    selected = st.radio(
                        f"bonus_{pid}",
                        options=opciones,
                        index=index,
                        disabled=bloqueado,
                    )

                    if not ya_respondio and not fase_cerrada:
                        st.session_state.draft_bonus[pid] = selected

                if ya_respondio:
                    st.success(f"Tu respuesta quedó guardada y bloqueada: {prev_val}")
                elif fase_cerrada:
                    st.caption("Este bonus ya cerró por fecha mínima de la fase. Ya no admite respuestas.")

                respuestas_bonus = bonus_resp[bonus_resp["partido_id"] == pid].copy() if not bonus_resp.empty else pd.DataFrame()
                if not respuestas_bonus.empty:
                    respuestas_bonus = respuestas_bonus.rename(columns={
                        "participante": "Participante",
                        "respuesta": "Respuesta",
                        "fecha_guardado_iso": "Fecha de guardado",
                    })
                    st.markdown("### Respuestas registradas")
                    st.dataframe(
                        respuestas_bonus[["Participante", "Respuesta", "Fecha de guardado"]],
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("Aún no hay respuestas registradas para este bonus.")

                st.divider()

            if st.button("Guardar respuestas bonus", use_container_width=True):
                try:
                    abiertos = []
                    for _, row in bonus_pendientes.iterrows():
                        fase = normalize_text(row.get("fase"))
                        pid = normalize_text(row.get("partido_id"))
                        prev = bonus_resp_user[bonus_resp_user["partido_id"] == pid]
                        ya_respondio = not prev.empty and normalize_text(prev.iloc[0].get("respuesta")) != ""

                        if not is_phase_closed(partidos, fase) and not ya_respondio:
                            abiertos.append(row)

                    abiertos_df = pd.DataFrame(abiertos) if abiertos else bonus_pendientes.iloc[0:0].copy()
                    save_bonus_answers_batch(user, abiertos_df, st.session_state.draft_bonus, data["bonus_resp"])
                    st.success("Respuestas bonus guardadas.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.info("El administrador no participa en respuestas bonus.")
            for _, row in bonus_pendientes.iterrows():
                pid = normalize_text(row.get("partido_id"))
                st.markdown(f"## {row['local']} vs {row['visitante']}")
                st.caption(f"{row['fase']} | Grupo {row['grupo']} | {row['fecha']} {row['hora']}")
                st.write(normalize_text(row.get("bonus_pregunta")))
                respuestas_bonus = bonus_resp[bonus_resp["partido_id"] == pid].copy() if not bonus_resp.empty else pd.DataFrame()
                if not respuestas_bonus.empty:
                    respuestas_bonus = respuestas_bonus.rename(columns={
                        "participante": "Participante",
                        "respuesta": "Respuesta",
                        "fecha_guardado_iso": "Fecha de guardado",
                    })
                    st.markdown("### Respuestas registradas")
                    st.dataframe(
                        respuestas_bonus[["Participante", "Respuesta", "Fecha de guardado"]],
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("Aún no hay respuestas registradas para este bonus.")
                st.divider()
    else:
        st.subheader("NO HAY BONUS ACTIVO")
        bonus_emitidos = bonus_activos[bonus_activos["bonus_resuelto"]].copy() if not bonus_activos.empty else pd.DataFrame()
        if bonus_emitidos.empty:
            st.info("Aún no hay bonus emitidos o resueltos.")
        else:
            historico = bonus_emitidos.copy()
            historico["Partido"] = historico["local"].astype(str) + " vs " + historico["visitante"].astype(str)
            historico = historico.rename(columns={
                "fase": "Fase",
                "grupo": "Grupo",
                "bonus_pregunta": "Pregunta bonus",
                "bonus_respuesta_correcta": "Respuesta correcta",
                "bonus_puntos": "Puntos bonus",
            })
            st.dataframe(
                historico[["Fase", "Grupo", "Partido", "Pregunta bonus", "Respuesta correcta", "Puntos bonus"]],
                use_container_width=True,
                hide_index=True,
            )


def main():
    init_state()

    if get_conn() is None:
        st.title("Quiniela Mundial 2026")
        render_connection_help()
        return

    try:
        data = load_all_data_cached(st.session_state.get("data_nonce", 0))
    except Exception as e:
        st.title("Quiniela Mundial 2026")
        st.error(str(e))
        st.caption("La app no pudo leer una o más hojas críticas de Google Sheets. No es un tema de cookies del navegador.")
        return

    if data["participantes"].empty:
        try:
            ensure_admin_exists(data)
            data = load_all_data_cached(st.session_state.get("data_nonce", 0))
        except Exception:
            pass

    if not st.session_state.logged_in:
        login_box(data["participantes"])
        return

    sidebar_nav()
    config_map = get_config_map(data["config"])

    if st.session_state.nav == "INICIO":
        render_inicio(config_map)
    elif st.session_state.nav == "ADMINISTRACIÓN":
        render_admin(data)
    elif st.session_state.nav == "CAPTURA DE PRONÓSTICOS":
        render_predictions_capture(data)
    elif st.session_state.nav == "RESULTADOS OFICIALES FIFA":
        render_official_results(data)
    elif st.session_state.nav == "TABLA GENERAL DE PARTICIPANTES":
        render_tabla_general(data)
    elif st.session_state.nav == "BONUS":
        render_bonus(data)


if __name__ == "__main__":
    main()
