import pandas as pd
import numpy as np

def gerar_resumo_tecnico(df_disponiveis, df_rat, tecnico_valores, tecnicos_map, mes, ano):
    df_disponiveis['date'] = pd.to_datetime(df_disponiveis['date']).dt.date
    df_rat['data emissão'] = pd.to_datetime(df_rat['data emissão'], errors='coerce')
    df_rat['date'] = df_rat['data emissão'].dt.date
    df_rat_filtrado = df_rat[
        (pd.to_datetime(df_rat['date']).dt.month == int(mes))
        & (pd.to_datetime(df_rat['date']).dt.year == int(ano))
    ].copy()

    if 'tecnico_key' in df_rat_filtrado.columns and 'número de horas' in df_rat_filtrado.columns:
        df_rat_filtrado['número de horas'] = pd.to_numeric(
            df_rat_filtrado['número de horas'], errors='coerce').fillna(0)
        df_apontadas = df_rat_filtrado.groupby(['tecnico_key'])['número de horas'].sum().reset_index()
    else:
        df_apontadas = pd.DataFrame(columns=['tecnico_key', 'número de horas'])

    df_disp_ag = df_disponiveis.copy()
    df_disp_ag = df_disp_ag.groupby(['tecnico_key', 'calendar_id'])[
        ['horas_disponiveis', 'horas_agendadas']
    ].sum().reset_index()

    df_merge = df_disp_ag.merge(
        df_apontadas,
        on='tecnico_key',
        how='left'
    ).rename(columns={'número de horas': 'horas_apontadas'}).fillna(0)

    df_merge['horas_ociosas'] = df_merge['horas_disponiveis'] - df_merge['horas_agendadas']
    df_merge['horas_nao_faturadas'] = df_merge['horas_agendadas'] - df_merge['horas_apontadas']

    df_merge['indice_aproveitamento'] = np.where(
        df_merge['horas_agendadas'] > 0,
        df_merge['horas_apontadas'] / df_merge['horas_agendadas']*100,
        0
    )

    df_merge['valor_potencial_perdido'] = df_merge.apply(
        lambda x: x['horas_ociosas'] * tecnico_valores[tecnicos_map.get(x['tecnico_key'], "Guilherme")], axis=1)
    df_merge['comissao_potencial'] = df_merge['valor_potencial_perdido'] * 0.12

    resumo_tecnico = df_merge[[
        'calendar_id', 'horas_disponiveis', 'horas_agendadas', 'horas_apontadas',
        'horas_ociosas', 'horas_nao_faturadas', 'indice_aproveitamento',
        'valor_potencial_perdido', 'comissao_potencial'
    ]].copy()

    total_row = resumo_tecnico.sum(numeric_only=True)
    total_row['calendar_id'] = 'Total Geral'
    if total_row['horas_disponiveis'] > 0:
        total_row['indice_aproveitamento'] = (total_row['horas_apontadas'] / total_row['horas_agendadas'])*100
    else:
        total_row['indice_aproveitamento'] = 0

    resumo_tecnico = pd.concat([resumo_tecnico, pd.DataFrame([total_row])], ignore_index=True)
    return resumo_tecnico

def gerar_resumo_cliente(df_rat, mes, ano):
    df_rat['data emissão'] = pd.to_datetime(
        df_rat['data emissão'], errors='coerce')
    df_rat['date'] = df_rat['data emissão'].dt.date
    df_rat_filtrado = df_rat[
        (pd.to_datetime(df_rat['date']).dt.month == int(mes))
        & (pd.to_datetime(df_rat['date']).dt.year == int(ano))
    ].copy()
    if not df_rat_filtrado.empty and 'cliente' in df_rat_filtrado.columns and 'número de horas' in df_rat_filtrado.columns:
        df_rat_filtrado['número de horas'] = pd.to_numeric(
            df_rat_filtrado['número de horas'], errors='coerce')
        resumo_cliente = df_rat_filtrado.groupby(
            "cliente")["número de horas"].sum().reset_index()
        total_row2 = resumo_cliente.sum(numeric_only=True)
        total_row2['cliente'] = 'Total Geral'
        resumo_cliente = pd.concat(
            [resumo_cliente, pd.DataFrame([total_row2])], ignore_index=True)
        return resumo_cliente
    else:
        return pd.DataFrame([{"cliente": "Sem dados", "número de horas": 0}])

def ordenar_colunas_detalhamento(detalhamento, tecnicos):
    nova_ordem = []
    for tecnico in tecnicos:
        nova_ordem += [
            f"{tecnico} - horas_disponiveis",
            f"{tecnico} - horas_agendadas",
            f"{tecnico} - diferença"
        ]
    nova_ordem = [col for col in nova_ordem if col in detalhamento.columns]
    return detalhamento[nova_ordem]

def gerar_detalhamento_diario(df_disponiveis, df_rat, tecnico_valores, tecnicos_map, mes, ano):
    df_disponiveis['date'] = pd.to_datetime(df_disponiveis['date']).dt.date
    df_rat['data emissão'] = pd.to_datetime(
        df_rat['data emissão'], errors='coerce')
    df_rat['date'] = df_rat['data emissão'].dt.date
    df_rat_filtrado = df_rat[
        (pd.to_datetime(df_rat['date']).dt.month == int(mes))
        & (pd.to_datetime(df_rat['date']).dt.year == int(ano))
    ].copy()

    if 'tecnico' in df_rat_filtrado.columns:
        from utils.normalizacao import padroniza_tecnico, normaliza_nome
        df_rat_filtrado['tecnico'] = df_rat_filtrado['tecnico'].apply(
            padroniza_tecnico)
        df_rat_filtrado['tecnico_key'] = df_rat_filtrado['tecnico'].apply(
            normaliza_nome)

    if 'tecnico_key' in df_rat_filtrado.columns and 'número de horas' in df_rat_filtrado.columns:
        df_rat_filtrado['número de horas'] = pd.to_numeric(
            df_rat_filtrado['número de horas'], errors='coerce').fillna(0)
        df_apontadas = df_rat_filtrado.groupby(['tecnico_key', 'date'])[
            'número de horas'].sum().reset_index()
    else:
        df_apontadas = pd.DataFrame(
            columns=['tecnico_key', 'date', 'número de horas'])

    df_merge = df_disponiveis.merge(
        df_apontadas,
        on=['tecnico_key', 'date'],
        how='left'
    ).rename(columns={'número de horas': 'horas_apontadas'}).fillna(0)

    df_merge['horas_ociosas'] = df_merge['horas_disponiveis'] - \
        df_merge['horas_agendadas']
    df_merge['diferença'] = df_merge['horas_ociosas']

    detalhamento = df_merge.pivot(index="date", columns="calendar_id", values=[
                                  "horas_disponiveis", "horas_agendadas", "diferença"])
    detalhamento.columns = [
        '{} - {}'.format(col[1], col[0]) for col in detalhamento.columns.values]
    detalhamento = detalhamento.sort_index(axis=1)
    detalhamento = ordenar_colunas_detalhamento(
        detalhamento, list(tecnicos_map.values()))
    total_row = detalhamento.sum(numeric_only=True)
    total_row.name = "Total"
    detalhamento = pd.concat([detalhamento, pd.DataFrame([total_row])])
    detalhamento = ordenar_colunas_detalhamento(detalhamento, list(tecnicos_map.values()))
    return detalhamento

# NOVA FUNÇÃO PARA RESUMO POR CLIENTE E POR TÉCNICO EM ABAS
def gerar_resumo_cliente_por_tecnico(df_agenda, df_rat, tecnicos, tecnicos_map, mes, ano):
    resultados = {}

    df_agenda = df_agenda.copy()
    df_rat = df_rat.copy()
    df_agenda["date"] = pd.to_datetime(df_agenda["date"], errors="coerce")
    df_rat["data emissão"] = pd.to_datetime(df_rat["data emissão"], errors="coerce")
    df_rat["date"] = df_rat["data emissão"].dt.date

    # Padroniza o nome da coluna cliente no RAT
    if "cliente" not in df_rat.columns:
        if "nome cliente" in df_rat.columns:
            df_rat["cliente"] = df_rat["nome cliente"]
        else:
            df_rat["cliente"] = "Desconhecido"
    if "cliente" not in df_agenda.columns:
        df_agenda["cliente"] = "Desconhecido"
    if "horas_agendadas" not in df_agenda.columns:
        df_agenda["horas_agendadas"] = 0

    for tecnico in tecnicos:
        agendadas = df_agenda[
            (df_agenda["calendar_id"] == tecnico) &
            (df_agenda["date"].dt.month == int(mes)) &
            (df_agenda["date"].dt.year == int(ano))
        ].groupby("cliente")["horas_agendadas"].sum().reset_index().rename(
            columns={"horas_agendadas": "Horas Agendadas"}
        )

        apontadas = df_rat[
            (df_rat["tecnico"] == tecnico) &
            (pd.to_datetime(df_rat["data emissão"]).dt.month == int(mes)) &
            (pd.to_datetime(df_rat["data emissão"]).dt.year == int(ano))
        ].groupby("cliente")["número de horas"].sum().reset_index().rename(
            columns={"número de horas": "Horas Apontadas"}
        )

        resumo = pd.merge(agendadas, apontadas, on="cliente", how="outer").fillna(0)
        resumo["Diferença"] = resumo["Horas Agendadas"] - resumo["Horas Apontadas"]
        resumo = resumo.sort_values("Horas Agendadas", ascending=False)
        resultados[tecnico] = resumo

    return resultados
