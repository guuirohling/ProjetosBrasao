import pandas as pd
import os

ARQUIVO_LANCAMENTOS = "lancamentos.pkl"
ARQUIVO_PESSOAS = "pessoas.pkl"

def carregar_lancamentos():
    if os.path.exists(ARQUIVO_LANCAMENTOS):
        return pd.read_pickle(ARQUIVO_LANCAMENTOS)
    else:
        return pd.DataFrame(columns=[
            "data", "descricao", "valor", "banco", "titular", "categoria", "quem_paga", "pessoa_deve"
        ])

def salvar_lancamentos(df):
    df.to_pickle(ARQUIVO_LANCAMENTOS)

def carregar_pessoas():
    if os.path.exists(ARQUIVO_PESSOAS):
        return pd.read_pickle(ARQUIVO_PESSOAS)
    else:
        return pd.DataFrame(columns=["nome"])

def salvar_pessoas(df):
    df.to_pickle(ARQUIVO_PESSOAS)
