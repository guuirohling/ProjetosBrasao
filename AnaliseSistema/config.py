import streamlit as st
import os
import pandas as pd
import calendar

tecnicos = ["Guilherme", "Rafael", "Cezar", "Humberto"]
tecnicos_map = {
    "guilherme": "Guilherme",
    "rafael": "Rafael",
    "cezar": "Cezar",
    "humberto": "Humberto"
}

def parametros_sidebar():
    st.sidebar.header("Configuração de Técnicos")
    tecnico_valores = {}
    tecnico_horas = {}
    for tecnico in tecnicos:
        tecnico_valores[tecnico] = st.sidebar.number_input(
            f"Valor/hora ({tecnico})", min_value=0.0, value=218.0, key=f"vh_{tecnico}")
        tecnico_horas[tecnico] = st.sidebar.number_input(
            f"Horas disponíveis/dia ({tecnico})", min_value=0.0, value=8.5, key=f"hd_{tecnico}")
    return tecnico_valores, tecnico_horas

def parametros_gerais_sidebar():
    hoje = pd.Timestamp.today()
    ano = st.sidebar.number_input("Ano de referência", min_value=2022, max_value=2100, value=hoje.year, step=1)
    mes = st.sidebar.selectbox("Mês de referência", list(range(1, 13)), index=hoje.month-1, format_func=lambda x: f"{x:02d}")
    pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")
    st.sidebar.write(f"Pasta de dados fixa: {pasta}")
    st.sidebar.write("Agendas em: dados/agendas\nRATs em: dados/rats_radar")
    return pasta, ano, mes

def valida_pasta(pasta):
    return os.path.exists(pasta)

FERIADOS_FIXOS = [
    "2025-01-01", "2025-03-03", "2025-03-04", "2025-03-05", "2025-04-18", "2025-04-21", "2025-05-01", "2025-06-19", "2025-09-07", "2025-10-12", "2025-11-02", "2025-11-15", "2025-12-25"
]

def dias_uteis(mes, ano, feriados=FERIADOS_FIXOS):
    # Gera todos os dias úteis do mês
    datas = pd.date_range(f"{ano}-{mes:02d}-01", f"{ano}-{mes:02d}-{calendar.monthrange(ano, mes)[1]}", freq="B")
    # Remove os feriados
    feriados = pd.to_datetime(feriados)
    datas = datas[~datas.isin(feriados)]
    return datas

def concat_dfs(dfs):
    return pd.concat(dfs, ignore_index=True)

def filtra_rat_periodo(df_rat, mes, ano):
    if 'data emissão' in df_rat.columns:
        df_rat['data emissão'] = pd.to_datetime(df_rat['data emissão'], dayfirst=True, errors="coerce")
        df_rat = df_rat[
            (df_rat['data emissão'].dt.month == mes) &
            (df_rat['data emissão'].dt.year == ano)
        ]
    return df_rat
