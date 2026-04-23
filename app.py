# V6 - RESULTADOS + BASE ESTABLE
# Incluye:
# - Login
# - Admin funcional (crear usuarios + cargar resultados)
# - Resultados oficiales guardados en Sheets
# - Sin errores de logout
# - Optimizado para no exceder cuota

import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Mexico_City")

def now():
    return datetime.now(TZ).isoformat()

def init():
    for k, v in {
        "logged": False,
        "user": "",
        "admin": False,
        "nonce": 0
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

def conn():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def read(name):
    return conn().read(worksheet=name)

def write(name, df):
    conn().update(worksheet=name, data=df)
    read.clear()

def login(df):
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        r = df[(df["nombre"]==u)&(df["clave"]==p)]
        if not r.empty:
            st.session_state.logged=True
            st.session_state.user=u
            st.session_state.admin=str(r.iloc[0]["es_admin"]) in ["1","1.0","True"]
            st.rerun()

def sidebar():
    opts=["INICIO","RESULTADOS"]
    if st.session_state.admin:
        opts.insert(1,"ADMIN")
    nav=st.sidebar.radio("Menú",opts)
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()
    return nav

def admin(df_part, df_res):
    st.header("ADMIN")

    # crear usuario
    st.subheader("Crear usuario")
    u=st.text_input("Nuevo usuario")
    p=st.text_input("Clave")
    if st.button("Crear usuario"):
        new=pd.DataFrame([[u,p,"0"]],columns=["nombre","clave","es_admin"])
        df=pd.concat([df_part,new])
        write("participantes",df)
        st.success("Usuario creado")

    st.divider()

    # resultados
    st.subheader("Capturar resultados")

    try:
        df_partidos=read("partidos")
    except:
        st.warning("No hay hoja partidos")
        return

    for i,row in df_partidos.iterrows():
        col1,col2,col3,col4=st.columns([2,1,1,2])
        with col1: st.write(row["local"])
        with col2: l=st.number_input(f"l{i}",0,10,0)
        with col3: v=st.number_input(f"v{i}",0,10,0)
        with col4: st.write(row["visitante"])

        if st.button(f"Guardar {i}"):
            df_res=df_res[df_res["partido_id"]!=row["partido_id"]]
            df_res.loc[len(df_res)]=[row["partido_id"],l,v,now()]
            write("resultados_oficiales",df_res)
            st.success("Guardado")
            st.rerun()

def resultados(df_partidos, df_res):
    st.header("Resultados oficiales")

    df=df_partidos.merge(df_res,on="partido_id",how="left")

    st.dataframe(df[["local","visitante","marcador_local","marcador_visitante"]])

def main():
    init()

    df_part=read("participantes")

    if not st.session_state.logged:
        login(df_part)
        return

    nav=sidebar()

    if nav=="INICIO":
        st.title("Quiniela 2026")

    if nav=="ADMIN":
        df_res=read("resultados_oficiales")
        admin(df_part,df_res)

    if nav=="RESULTADOS":
        df_partidos=read("partidos")
        df_res=read("resultados_oficiales")
        resultados(df_partidos,df_res)

if __name__=="__main__":
    main()
