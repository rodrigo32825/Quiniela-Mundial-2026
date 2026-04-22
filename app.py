import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Quiniela Mundial FIFA 2026",
    page_icon="⚽",
    layout="wide"
)

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
            return datetime.strptime(f"{fecha_texto} {hora_texto}", fmt)
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
    return datetime.now() >= cierres_por_fase[fase]


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
# BASE DE DATOS JSON
# =========================================================
def obtener_borrador_resultados_oficiales():
    if "resultados_oficiales_borrador" not in st.session_state or not isinstance(st.session_state.get("resultados_oficiales_borrador"), dict):
        st.session_state.resultados_oficiales_borrador = {}
    return st.session_state.resultados_oficiales_borrador


def limpiar_borrador_resultados_oficiales():
    st.session_state.resultados_oficiales_borrador = {}


def refrescar_resultados_oficiales_desde_sheets(forzar=False, silencioso=True):
    ahora = ahora_mx()
    ultimo_refresh = st.session_state.get("ultimo_refresh_resultados_sheets")

    if not forzar and ultimo_refresh is not None:
        try:
            segundos = (ahora - ultimo_refresh).total_seconds()
            if segundos < SHEETS_REFRESH_COOLDOWN:
                return False
        except Exception:
            pass

    try:
        df_resultados = leer_worksheet_seguro("resultados_oficiales")
        resultados_oficiales = {}

        if not df_resultados.empty:
            for _, row in df_resultados.iterrows():
                partido_id = str(row.get("partido_id", "")).strip()
                if not partido_id:
                    continue
                try:
                    marcador_local = int(float(row.get("marcador_local", 0)))
                    marcador_visitante = int(float(row.get("marcador_visitante", 0)))
                except Exception:
                    continue
                resultados_oficiales[partido_id] = {
                    "marcador_local": marcador_local,
                    "marcador_visitante": marcador_visitante
                }

        if "db" not in st.session_state or not isinstance(st.session_state.db, dict):
            st.session_state.db = estructura_base()

        st.session_state.db["resultados_oficiales"] = resultados_oficiales
        st.session_state.ultimo_refresh_resultados_sheets = ahora
        return True
    except Exception as e:
        if not silencioso:
            st.warning(f"No se pudieron refrescar los resultados oficiales desde Google Sheets: {e}")
        return False


def obtener_resultado_oficial_borrador(partido_id):
    borrador = obtener_borrador_resultados_oficiales()
    pid = str(partido_id)
    if pid in borrador:
        return borrador[pid]
    return obtener_resultado_oficial(partido_id)


def guardar_resultado_oficial_temporal(partido_id, marcador_local, marcador_visitante):
    borrador = obtener_borrador_resultados_oficiales()
    borrador[str(partido_id)] = {
        "marcador_local": int(marcador_local),
        "marcador_visitante": int(marcador_visitante)
    }


def guardar_resultado_oficial_en_sheets_por_partido(partido_id, marcador_local, marcador_visitante):
    resultados = obtener_resultados_oficiales()
    resultados[str(partido_id)] = {
        "marcador_local": int(marcador_local),
        "marcador_visitante": int(marcador_visitante)
    }
    ok = persistir_db("resultados")
    if ok:
        refrescar_resultados_oficiales_desde_sheets(forzar=True, silencioso=True)
        obtener_borrador_resultados_oficiales().pop(str(partido_id), None)
    return ok


def estructura_base():
    return {
        "participantes": {},
        "resultados_oficiales": {}
    }


def participante_base(clave=""):
    return {
        "clave": clave,
        "favoritos_guardados": [],
        "pronosticos_guardados": [],
        "fecha_envio": None,
        "fecha_envio_iso": None
    }


def cargar_db():
    if not os.path.exists(DATA_FILE):
        return estructura_base()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
    except Exception:
        return estructura_base()

    if "participantes" not in db:
        db["participantes"] = {}

    if "resultados_oficiales" not in db:
        db["resultados_oficiales"] = {}

    for nombre, datos in db["participantes"].items():
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
    limpiar_borrador_resultados_oficiales()

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
    limpiar_borrador_resultados_oficiales()
    st.session_state.pop("ultimo_refresh_resultados_sheets", None)


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
    return datetime.now() >= FECHA_LIMITE_FAVORITOS


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


def guardar_envio_oficial(participante_data, pronosticos_fase):
    guardar_pronosticos_fase(participante_data, pronosticos_fase)
    ahora = datetime.now()
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
        except ValueError:
            fecha_envio_dt = None

    return {
        "Participante": nombre,
        "Puntos base": total_puntos_base,
        "Bonus favoritos": bonus_favoritos,
        "Marcadores exactos": exact_hits,
        "Aciertos de resultado": result_hits,
        "Puntos eliminación directa": knockout_points,
        "Puntos fases finales": late_stage_points,
        "Puntos ganados": total_general,
        "_fecha_envio_dt": fecha_envio_dt if fecha_envio_dt else datetime.max
    }


def construir_tabla_general():
    participantes = obtener_participantes()
    filas = []

    for nombre, participante_data in participantes.items():
        stats = estadisticas_participante(nombre, participante_data)
        filas.append({
            "Participante": stats["Participante"],
            "Número de marcadores exactos": stats["Marcadores exactos"],
            "Número de aciertos de resultado": stats["Aciertos de resultado"],
            "Puntos Base ganados": stats["Puntos base"],
            "Puntos por favoitos": stats["Bonus favoritos"],
            "Total Puntos ganados": stats["Puntos ganados"],
            "_desempate_exactos": stats["Marcadores exactos"],
            "_desempate_resultados": stats["Aciertos de resultado"],
            "_desempate_eliminacion": stats["Puntos eliminación directa"],
            "_desempate_fases_finales": stats["Puntos fases finales"],
            "_desempate_fecha": stats["_fecha_envio_dt"],
        })

    if not filas:
        return pd.DataFrame()

    tabla_df = pd.DataFrame(filas)

    tabla_df = tabla_df.sort_values(
        by=[
            "Total Puntos ganados",
            "_desempate_exactos",
            "_desempate_resultados",
            "_desempate_eliminacion",
            "_desempate_fases_finales",
            "_desempate_fecha",
            "Participante"
        ],
        ascending=[False, False, False, False, False, True, True]
    ).reset_index(drop=True)

    tabla_df.insert(0, "Posición", range(1, len(tabla_df) + 1))

    columnas_visibles = [
        "Posición",
        "Participante",
        "Número de marcadores exactos",
        "Número de aciertos de resultado",
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
        vivo = equipo_sigue_vivo(equipo, partidos, resultados)
        estado = "Activo" if vivo else "Eliminado"

        col1, col2, col3 = st.columns([4, 1, 1])
        col1.write(f"• {equipo}")
        col2.write(f"**{puntos_favoritos.get(equipo, 0)} pts**")
        col3.write(estado)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("⚽ Quiniela 2026")
menu = st.sidebar.radio(
    "Menú",
    ["Inicio", "Participante", "Resultados oficiales", "Admin", "Tabla general"]
)

st.title("Quiniela Mundial FIFA 2026")

# =========================================================
# INICIO
# =========================================================
if menu == "Inicio":
    st.subheader("Bienvenido")
    st.write("Esta será la app oficial de la quiniela del Mundial FIFA 2026.")

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

    st.markdown("### Reglas base")
    st.write("- Inscripción: $400 MXN")
    st.write("- 2 equipos favoritos")
    st.write("- Favoritos cierran con la primera fase")
    st.write("- Los pronósticos cierran por fase")
    st.write("- Mientras no venza la fase, se puede editar y reenviar")
    st.write("- La última versión enviada antes del cierre es la válida")
    st.write("- 1 punto por acertar ganador o empate")
    st.write("- 2 puntos extra por marcador exacto")
    st.write("- Si un equipo favorito queda eliminado, deja de sumar puntos")

    st.markdown("### Calendario actual cargado")
    calendario_df = construir_calendario_df()
    if calendario_df.empty:
        st.info("Aún no hay partidos cargados.")
    else:
        st.dataframe(calendario_df, use_container_width=True, hide_index=True)

# =========================================================
# PARTICIPANTE
# =========================================================
elif menu == "Participante":
    st.subheader("Participante")

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

                if fase_seleccionada == "Fase de grupos":
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
                        f"**{p['local']} vs {p['visitante']}**  \n"
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

                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    if st.button("Guardar borrador de la fase", use_container_width=True, disabled=fase_cerrada):
                        guardar_pronosticos_fase(participante_data, pronosticos_temporales)
                        st.success(f"Borrador guardado para la fase '{fase_seleccionada}'.")
                        st.rerun()

                with col_g2:
                    if st.button("Enviar versión oficial de la fase", use_container_width=True, disabled=fase_cerrada):
                        if len(participante_data["favoritos_guardados"]) != 2:
                            st.error("Debes guardar tus 2 equipos favoritos antes de enviar.")
                        else:
                            guardar_envio_oficial(participante_data, pronosticos_temporales)
                            st.success(f"Versión oficial enviada para la fase '{fase_seleccionada}'.")
                            st.rerun()

                if participante_data.get("fecha_envio"):
                    st.info(f"Última versión oficial enviada: {participante_data['fecha_envio']}")

                st.markdown("### 3) Resumen general de pronósticos")

                if participante_data["pronosticos_guardados"]:
                    resumen_df = construir_resumen_pronosticos(participante_data["pronosticos_guardados"])
                    st.dataframe(resumen_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Aún no has guardado pronósticos.")

# =========================================================
# RESULTADOS OFICIALES
# =========================================================
elif menu == "Resultados oficiales":
    st.subheader("Resultados oficiales")

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
# ADMIN
# =========================================================
elif menu == "Admin":
    st.subheader("Admin")

    if not st.session_state.admin_autenticado:
        usuario_admin = st.text_input("Usuario admin")
        clave_admin = st.text_input("Clave admin", type="password")

        if st.button("Entrar como admin", use_container_width=True):
            if autenticar_admin(usuario_admin, clave_admin):
                st.session_state.admin_autenticado = True
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
                limpiar_borrador_resultados_oficiales()
                st.session_state.pop("ultimo_refresh_resultados_sheets", None)
                st.rerun()

        # =====================================================
        # 1) GESTIÓN DE CALENDARIO Y LIMPIEZA
        # =====================================================
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

        # =====================================================
        # 2) ADMINISTRACIÓN DE PARTICIPANTES
        # =====================================================
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
                    "Versión oficial enviada": "Sí" if datos["fecha_envio"] else "No"
                })

            st.dataframe(pd.DataFrame(filas_participantes), use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay participantes registrados.")

        # =====================================================
        # 3) CAPTURA DE RESULTADOS OFICIALES
        # =====================================================
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
            grupo_admin = "Todos"

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
            borrador_resultados = obtener_borrador_resultados_oficiales()

            if not partidos_admin.empty:
                partidos_guardados_visibles = 0
                for _, p in partidos_admin.iterrows():
                    if str(p["id"]) in resultados:
                        partidos_guardados_visibles += 1
                st.caption(f"Partidos visibles ya guardados oficialmente: {partidos_guardados_visibles} de {len(partidos_admin)}")

            for _, p in partidos_admin.iterrows():
                st.markdown(
                    f"**{p['local']} vs {p['visitante']}**  \n"
                    f"{p['ciudad']} — {p['fase']} — Grupo {p['grupo']} — {p['fecha']} {p['hora']}"
                )

                resultado_actual = obtener_resultado_oficial_borrador(p["id"]) or {"marcador_local": 0, "marcador_visitante": 0}

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

                guardar_resultado_oficial_temporal(p["id"], r1, r2)

                col_btn_1, col_btn_2 = st.columns([1.25, 1])

                with col_btn_1:
                    if st.button(f"Guardar resultado oficial partido {p['id']}", key=f"guardar_resultado_{p['id']}"):
                        ok = guardar_resultado_oficial_en_sheets_por_partido(p["id"], r1, r2)
                        if ok:
                            st.success(f"Resultado oficial guardado para {p['local']} vs {p['visitante']}.")
                            st.rerun()

                with col_btn_2:
                    if str(p["id"]) in borrador_resultados:
                        st.caption("Borrador en sesión")
                    elif str(p["id"]) in resultados:
                        st.caption("Guardado en Sheets")
                    else:
                        st.caption("Sin guardar")

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
    st.subheader("Tabla general")

    tabla_general_df = construir_tabla_general()

    if tabla_general_df.empty:
        st.info("Aún no hay información suficiente para mostrar la tabla general.")
    else:
        styled_df = tabla_general_df.style.set_properties(
            subset=["Puntos Base ganados", "Puntos por favoitos", "Total Puntos ganados"],
            **{"font-weight": "bold"}
        )

        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        st.caption(
            "Desempate: Total Puntos ganados → Número de marcadores exactos → "
            "Número de aciertos de resultado → Puntos en eliminación directa "
            "→ Puntos en fases finales → Hora de envío."
        )
