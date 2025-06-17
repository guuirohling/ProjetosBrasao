import pandas as pd
import io
from utils.normalizacao import normaliza_nome, padroniza_tecnico

def processa_agenda_uploaded(uploaded_files):
    dfs = []
    for file in uploaded_files:
        try:
            file.seek(0)
            bytes_data = file.read()
            df = pd.read_excel(io.BytesIO(bytes_data), sheet_name="data")
            df.columns = [c.strip().lower() for c in df.columns]
            df['calendar_id'] = df['calendar_id'].apply(padroniza_tecnico)
            df['tecnico_key'] = df['calendar_id'].apply(normaliza_nome)
            dfs.append(df)
        except Exception as e:
            print(f"Erro ao ler agenda: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()

def processa_rat_uploaded(uploaded_files):
    dfs = []
    for file in uploaded_files:
        try:
            file.seek(0)
            if file.name.endswith('.xlsx'):
                bytes_data = file.read()
                df = pd.read_excel(io.BytesIO(bytes_data), sheet_name="Plan1")
            else:
                df = pd.read_csv(file)
            df.columns = [c.strip().lower() for c in df.columns]
            df.rename(columns={
                'tecnico': 'tecnico',
                'nome cliente': 'cliente',
                'número de horas': 'número de horas'
            }, inplace=True)
            df['tecnico'] = df['tecnico'].apply(padroniza_tecnico)
            df['tecnico_key'] = df['tecnico'].apply(normaliza_nome)
            dfs.append(df)
        except Exception as e:
            print(f"Erro ao ler RAT: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()
