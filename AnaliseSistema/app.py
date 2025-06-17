# app.py

import streamlit as st
import pandas as pd
import config
from etl.leitura import processa_agenda_uploaded, processa_rat_uploaded
from etl.processamento import descontar_almoco_e_sobreposicao
from etl.relatorios import (
    gerar_resumo_tecnico,
    gerar_resumo_cliente,
    gerar_detalhamento_diario,
    gerar_resumo_cliente_por_tecnico
)
from depara import carregar_depara, salvar_depara, detectar_novos_clientes, aplicar_de_para_clientes

st.set_page_config(layout="wide")
st.title("Controle de Técnicos — Indicadores de Agendas e RATs")

col1, col2 = st.columns([1, 1])
with col1:
    mes = st.selectbox("Mês de referência", list(range(1, 13)), index=3, format_func=lambda x: f"{x:02d}")
with col2:
    ano = st.number_input("Ano de referência", min_value=2022, max_value=2100, value=2025, step=1)

with st.expander("Configurações Avançadas", expanded=False):
    valor_hora = st.number_input("Valor/hora (padrão para todos)", min_value=0.0, value=218.0, step=1.0)
    st.write("Importar exceções de horas disponíveis em dias específicos (opcional)")
    uploaded_excecoes = st.file_uploader(
        "Importar exceções (Excel/csv, colunas: tecnico, data, horas_disponiveis)",
        type=["xlsx", "csv"], key="excecoes"
    )

uploaded_agendas = st.file_uploader(
    "Selecione os arquivos de AGENDA (.xlsx, sheet: 'data')", type="xlsx", accept_multiple_files=True, key="agenda")
uploaded_rats = st.file_uploader(
    "Selecione os arquivos de RAT/RADAR (.xlsx/.csv, sheet: 'Plan1')", type=["xlsx", "csv"], accept_multiple_files=True, key="rat")

tecnico_valores = {tec: valor_hora for tec in config.tecnicos}

def aplicar_excecoes(df_disponiveis, uploaded_excecoes):
    if uploaded_excecoes is not None:
        if uploaded_excecoes.name.endswith("xlsx"):
            df_exc = pd.read_excel(uploaded_excecoes)
        else:
            df_exc = pd.read_csv(uploaded_excecoes)
        df_exc.columns = [c.lower() for c in df_exc.columns]
        for idx, row in df_exc.iterrows():
            mask = (
                (df_disponiveis["calendar_id"] == row["tecnico"])
                & (pd.to_datetime(df_disponiveis["date"]).dt.date == pd.to_datetime(row["data"]).date())
            )
            df_disponiveis.loc[mask, "horas_disponiveis"] = row["horas_disponiveis"]
    return df_disponiveis

def formata_tabela_resumida(df):
    df_fmt = df.copy()
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

df_agenda = None
df_rat = None
if uploaded_agendas and uploaded_rats:
    df_agenda = processa_agenda_uploaded(uploaded_agendas)
    df_rat = processa_rat_uploaded(uploaded_rats)

    # Padronização dos nomes de coluna para 'cliente'
    if "cliente" not in df_agenda.columns:
        if "event_name" in df_agenda.columns:
            df_agenda = df_agenda.rename(columns={"event_name": "cliente"})
        else:
            df_agenda["cliente"] = "Desconhecido"

    if "cliente" not in df_rat.columns:
        if "nome cliente" in df_rat.columns:
            df_rat = df_rat.rename(columns={"nome cliente": "cliente"})
        else:
            df_rat["cliente"] = "Desconhecido"

    # ----------- INÍCIO DO BLOCO DE-PARA CLIENTES -----------
    if not df_agenda.empty and not df_rat.empty:
        st.subheader("Mapeamento de nomes de clientes (De-Para)")

        # Carrega o de-para salvo, se existir
        depara_clientes = carregar_depara()

        # Detecta novos nomes para mapear
        novos_nomes = detectar_novos_clientes(df_agenda, df_rat, depara_clientes)

        if novos_nomes:
            st.warning(f"⚠️ Foram encontrados {len(novos_nomes)} nomes de clientes não mapeados. Relacione-os abaixo.")
            novos_map = pd.DataFrame({
                'Nome original': novos_nomes,
                'Cliente unificado': novos_nomes,
            })
            edit_map = st.data_editor(novos_map, num_rows="fixed", hide_index=True, use_container_width=True, key="depara_novos")
            for i, row in edit_map.iterrows():
                depara_clientes[row['Nome original']] = row['Cliente unificado']
            salvar_depara(depara_clientes)
            st.success("Novos mapeamentos de clientes salvos!")
        else:
            st.info("Todos os nomes de clientes já estão mapeados.")

        # Revisão do mapeamento completo (opcional)
        with st.expander("Revisar/Editar mapeamento completo de clientes (opcional)"):
            full_map_df = pd.DataFrame(list(depara_clientes.items()), columns=['Nome original', 'Cliente unificado'])
            full_map_edit = st.data_editor(full_map_df, hide_index=True, use_container_width=True, key="depara_full")
            if st.button("Salvar revisão do mapeamento"):
                depara_clientes = dict(zip(full_map_edit['Nome original'], full_map_edit['Cliente unificado']))
                salvar_depara(depara_clientes)
                st.success("Mapeamento revisado e salvo!")

        # Aplica o de-para antes dos relatórios
        df_agenda = aplicar_de_para_clientes(df_agenda, depara_clientes)
        df_rat = aplicar_de_para_clientes(df_rat, depara_clientes)
    # ----------- FIM DO BLOCO DE-PARA CLIENTES -----------

if df_agenda is not None and df_rat is not None and not df_agenda.empty and not df_rat.empty:
    dias = config.dias_uteis(mes, ano)
    dfs_tecnicos = []
    for tecnico in config.tecnicos:
        base = descontar_almoco_e_sobreposicao(
            df_agenda, tecnico, dias, 8.5
        )
        dfs_tecnicos.append(base)
    df_disponiveis = config.concat_dfs(dfs_tecnicos)
    df_disponiveis = aplicar_excecoes(df_disponiveis, uploaded_excecoes)

    resumo_tecnico = gerar_resumo_tecnico(
        df_disponiveis, df_rat, tecnico_valores, config.tecnicos_map, mes, ano)
    st.subheader("Tabela Resumida por Técnico")
    st.dataframe(formata_tabela_resumida(
        resumo_tecnico.rename(columns=cabecalhos_resumido)))

    # Resumo por Cliente (em abas por técnico)
    resumo_cliente_tecnico = gerar_resumo_cliente_por_tecnico(
        df_agenda, df_rat, config.tecnicos, config.tecnicos_map, mes, ano
    )
    st.subheader("Resumo por Cliente (por Técnico)")
    tabs_cliente = st.tabs(config.tecnicos)
    for i, tecnico in enumerate(config.tecnicos):
        with tabs_cliente[i]:
            st.subheader(f"{tecnico}")
            st.dataframe(resumo_cliente_tecnico[tecnico])
            st.download_button(
                "Baixar CSV deste técnico",
                data=resumo_cliente_tecnico[tecnico].to_csv(index=False).encode('utf-8'),
                file_name=f"resumo_cliente_{tecnico.lower()}.csv",
                mime="text/csv"
            )

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
