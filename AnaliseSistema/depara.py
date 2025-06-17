# depara.py

import json
import os
import pandas as pd

DEPARA_PATH = "depara_clientes.json"

def carregar_depara():
    if os.path.exists(DEPARA_PATH):
        with open(DEPARA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_depara(depara):
    with open(DEPARA_PATH, "w", encoding="utf-8") as f:
        json.dump(depara, f, ensure_ascii=False, indent=2)

def detectar_novos_clientes(df_agenda, df_rat, depara_atual):
    # Trabalha SEMPRE com a coluna 'cliente', que já deve estar padronizada no app.py
    nomes_agenda = set(df_agenda['cliente'].dropna().unique())
    nomes_rat = set(df_rat['cliente'].dropna().unique())
    nomes_novos = (nomes_agenda | nomes_rat) - set(depara_atual.keys())
    return sorted(nomes_novos)

def aplicar_de_para_clientes(df, depara_dict):
    df = df.copy()
    if 'cliente' in df.columns:
        df['cliente'] = df['cliente'].map(depara_dict).fillna(df['cliente'])
    return df
