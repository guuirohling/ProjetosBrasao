import streamlit as st
import pandas as pd
import config
from etl.leitura import processa_agenda_uploaded, processa_rat_uploaded
from etl.processamento import descontar_almoco_e_sobreposicao
from etl.relatorios import (
    gerar_resumo_tecnico,
    gerar_resumo_cliente,
    gerar_detalhamento_diario
)

st.set_page_config(layout="wide")
st.title("Controle de Técnicos — Indicadores de Agendas e RATs")

def formata_tabela_resumida(df):
    df_fmt = df.copy()
    # Corrige para float caso venha string/objeto
    if "Índice de Aproveitamento" in df_fmt.columns:
        df_fmt["Índice de Aproveitamento"] = (
            df_fmt["Índice de Aproveitamento"].astype(float)
        ).round(2).astype(str) + " %"
    for col in ["Valor Potencial Perdido", "Comissão Potencial"]:
        if col in df_fmt.columns:
            df_fmt[col] = df_fmt[col].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else ""
            )
    return df_fmt

# Dicionários de nomes amigáveis
cabecalhos_resumido = {
    "calendar_id": "Técnico",
    "horas_disponiveis": "Horas Disponíveis",
    "horas_agendadas": "Horas Agendadas",
    "horas_apontadas": "Horas Apontadas",
    "horas_ociosas": "Horas Ociosas",
    "horas_nao_faturadas": "Horas Não Faturadas",
    "indice_aproveitamento": "Índice de Aproveitamento",
    "valor_potencial_perdido": "Valor Potencial Perdido",
    "comissao_potencial": "Comissão Potencial"
}
cabecalhos_cliente = {
    "cliente": "Cliente",
    "número de horas": "Horas Apontadas"
}

# SIDEBAR - PARÂMETROS E UPLOAD
with st.sidebar:
    st.header("Configuração de Técnicos")
    tecnico_valores, tecnico_horas = config.parametros_sidebar()
    st.divider()
    ano = st.number_input("Ano de referência", min_value=2022,
                          max_value=2100, value=2025, step=1)
    mes = st.selectbox("Mês de referência", list(range(1, 13)),
                       index=3, format_func=lambda x: f"{x:02d}")
    st.divider()
    st.subheader("Importação dos Arquivos")
    uploaded_agendas = st.file_uploader(
        "Selecione os arquivos de AGENDA (.xlsx, sheet: 'data')", type="xlsx", accept_multiple_files=True)
    uploaded_rats = st.file_uploader(
        "Selecione os arquivos de RAT/RADAR (.xlsx/.csv, sheet: 'Plan1')", type=["xlsx", "csv"], accept_multiple_files=True)
    show_diag = st.checkbox(
        "Exibir diagnóstico dos arquivos de dados", value=False)

df_agenda = None
df_rat = None
if uploaded_agendas and uploaded_rats:
    df_agenda = processa_agenda_uploaded(uploaded_agendas)
    df_rat = processa_rat_uploaded(uploaded_rats)

if show_diag:
    st.subheader("Diagnóstico dos Arquivos de Dados")
    if df_agenda is not None:
        st.write("Agenda - Linhas x Colunas:", df_agenda.shape)
        st.write("Agenda - Colunas:", df_agenda.columns.tolist())
        st.dataframe(df_agenda.head())
    else:
        st.write("Agenda não carregada.")

    if df_rat is not None:
        st.write("RAT - Linhas x Colunas:", df_rat.shape)
        st.write("RAT - Colunas:", df_rat.columns.tolist())
        st.dataframe(df_rat.head())
    else:
        st.write("RAT não carregado.")

if df_agenda is not None and df_rat is not None and not df_agenda.empty and not df_rat.empty:
    dias = config.dias_uteis(mes, ano)
    dfs_tecnicos = []
    for tecnico in config.tecnicos:
        base = descontar_almoco_e_sobreposicao(
            df_agenda, tecnico, dias, tecnico_horas[tecnico]
        )
        dfs_tecnicos.append(base)
    df_disponiveis = config.concat_dfs(dfs_tecnicos)

    # Resumo por Técnico - renomeia cabeçalhos e formata
    resumo_tecnico = gerar_resumo_tecnico(
        df_disponiveis, df_rat, tecnico_valores, config.tecnicos_map, mes, ano)
    st.subheader("Tabela Resumida por Técnico")
    st.dataframe(formata_tabela_resumida(
        resumo_tecnico.rename(columns=cabecalhos_resumido)))

    # Resumo por Cliente
    resumo_cliente = gerar_resumo_cliente(df_rat, mes, ano)
    st.subheader("Resumo por Cliente (do RAT)")
    st.dataframe(resumo_cliente.rename(columns=cabecalhos_cliente))

    # Detalhamento Diário - agora em abas por técnico
    detalhamento_diario = gerar_detalhamento_diario(
        df_disponiveis, df_rat, tecnico_valores, config.tecnicos_map, mes, ano)
    detalhamento_diario.columns = [
        col.replace("horas_disponiveis", "Horas Disponíveis")
           .replace("horas_agendadas", "Horas Agendadas")
           .replace("diferença", "Horas Ociosas")
        for col in detalhamento_diario.columns
    ]
    st.subheader("Detalhamento Diário (por Técnico)")
    tabs = st.tabs(config.tecnicos)
    for i, tecnico in enumerate(config.tecnicos):
        colunas = [
            f"{tecnico} - Horas Disponíveis",
            f"{tecnico} - Horas Agendadas",
            f"{tecnico} - Horas Ociosas"
        ]
        cols_existentes = [c for c in colunas if c in detalhamento_diario.columns]
        with tabs[i]:
            st.subheader(f"{tecnico}")
            st.dataframe(detalhamento_diario[cols_existentes])

    st.download_button("Baixar tabela detalhada (CSV)",
                       data=detalhamento_diario.to_csv(index=True).encode('utf-8'),
                       file_name="detalhamento_diario.csv", mime="text/csv")
else:
    st.info("Faça upload dos arquivos de AGENDA (sheet 'data') e RAT/RADAR (sheet 'Plan1') para prosseguir.")
