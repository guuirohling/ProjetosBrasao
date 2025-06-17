import pandas as pd
import numpy as np


def gerar_resumo_tecnico(df_agendas, df_rat, tecnico_valores, tecnicos_map, mes, ano):
    resumo = []

    # Padroniza nomes no RAT
    df_rat = df_rat.copy()
    if "Tecnico" in df_rat.columns:
        df_rat["tecnico_padrao"] = df_rat["Tecnico"].astype(
            str).str.strip().str.lower()
    else:
        df_rat["tecnico_padrao"] = ""

    # Padroniza nomes no agendas
    df_agendas = df_agendas.copy()
    df_agendas["tecnico_padrao"] = df_agendas["calendar_id"].astype(
        str).str.strip().str.lower()

    tecnicos = df_agendas["tecnico_padrao"].unique()

    for tecnico_padrao in tecnicos:
        nome_tecnico = tecnicos_map.get(
            tecnico_padrao, tecnico_padrao.capitalize())
        dados_ag = df_agendas[df_agendas["tecnico_padrao"] == tecnico_padrao]
        horas_disponiveis = dados_ag["horas_disponiveis"].sum()
        horas_agendadas = dados_ag["horas_agendadas"].sum()
        horas_ociosas = (dados_ag["horas_disponiveis"] -
                         dados_ag["horas_agendadas"]).sum()

        # Match exato no RAT pelo nome padronizado
        dados_rat = df_rat[df_rat["tecnico_padrao"] == tecnico_padrao]
        horas_apontadas = dados_rat["número de horas"].sum(
        ) if not dados_rat.empty and "número de horas" in dados_rat.columns else 0
        horas_nao_faturadas = horas_agendadas - horas_apontadas

        if horas_agendadas > 0:
            indice_aproveitamento = horas_apontadas / horas_agendadas
        else:
            indice_aproveitamento = 0
        valor_potencial_perdido = horas_ociosas * \
            tecnico_valores.get(nome_tecnico, 0)
        comissao_potencial = valor_potencial_perdido * 0.12

        resumo.append({
            "calendar_id": nome_tecnico,
            "horas_disponiveis": horas_disponiveis,
            "horas_agendadas": horas_agendadas,
            "horas_apontadas": horas_apontadas,
            "horas_ociosas": horas_ociosas,
            "horas_nao_faturadas": horas_nao_faturadas,
            "indice_aproveitamento": indice_aproveitamento,
            "valor_potencial_perdido": valor_potencial_perdido,
            "comissao_potencial": comissao_potencial,
        })

    df_resumo = pd.DataFrame(resumo)

    # Linha de total geral
    total_row = {
        "calendar_id": "Total Geral",
        "horas_disponiveis": df_resumo["horas_disponiveis"].sum(),
        "horas_agendadas": df_resumo["horas_agendadas"].sum(),
        "horas_apontadas": df_resumo["horas_apontadas"].sum(),
        "horas_ociosas": df_resumo["horas_ociosas"].sum(),
        "horas_nao_faturadas": df_resumo["horas_nao_faturadas"].sum(),
        "valor_potencial_perdido": df_resumo["valor_potencial_perdido"].sum(),
        "comissao_potencial": df_resumo["comissao_potencial"].sum()
    }
    if total_row["horas_agendadas"] > 0:
        total_row["indice_aproveitamento"] = total_row["horas_apontadas"] / \
            total_row["horas_agendadas"]
    else:
        total_row["indice_aproveitamento"] = 0

    df_resumo = pd.concat(
        [df_resumo, pd.DataFrame([total_row])], ignore_index=True)
    return df_resumo


def gerar_resumo_cliente(df_rat, mes=None, ano=None):
    # Opcional: filtro por mês/ano
    if mes and ano and "data emissão" in df_rat.columns:
        df_rat["data emissão"] = pd.to_datetime(
            df_rat["data emissão"], errors="coerce")
        df_rat = df_rat[(df_rat["data emissão"].dt.month == mes)
                        & (df_rat["data emissão"].dt.year == ano)]

    if "nome cliente" in df_rat.columns:
        df = df_rat.groupby("nome cliente")[
            "número de horas"].sum().reset_index()
        df.columns = ["cliente", "número de horas"]
    elif "cliente" in df_rat.columns:
        df = df_rat.groupby("cliente")["número de horas"].sum().reset_index()
    else:
        df = pd.DataFrame({"cliente": ["Sem dados"], "número de horas": [0]})

    return df


def gerar_detalhamento_diario(df_disponiveis, df_rat, tecnico_valores, tecnicos_map, mes, ano):
    # df_disponiveis já deve conter colunas: data, calendar_id, horas_disponiveis, horas_agendadas, horas_ociosas

    # Gera a matriz no formato: linha = data, colunas = técnico x (Horas Disponíveis, Horas Agendadas, Horas Ociosas)
    df_pivot = df_disponiveis.pivot_table(
        index="date",
        columns="calendar_id",
        values=["horas_disponiveis", "horas_agendadas", "horas_ociosas"],
        aggfunc="sum"
    )
    # Ordena colunas para o padrão desejado
    col_ordem = []
    for tecnico in tecnicos_map.values():
        for campo in ["horas_disponiveis", "horas_agendadas", "horas_ociosas"]:
            col_ordem.append((campo, tecnico))
    # Só mantém as colunas presentes (em caso de ausência de algum técnico)
    col_ordem = [c for c in col_ordem if c in df_pivot.columns]
    df_pivot = df_pivot[col_ordem]
    # Ajuste: nomes amigáveis nas colunas
    novo_nome = {
        "horas_disponiveis": "Horas Disponíveis",
        "horas_agendadas": "Horas Agendadas",
        "horas_ociosas": "Horas Ociosas",
    }
    df_pivot.columns = [
        f"{tecnico} - {novo_nome.get(campo, campo)}"
        for campo, tecnico in df_pivot.columns
    ]
    df_pivot = df_pivot.reset_index()
    return df_pivot
