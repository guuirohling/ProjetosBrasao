import unidecode
import pandas as pd

EMAILS_TECNICOS = {
    "guilherme@brasaosistemas.com.br": "Guilherme",
    "czravr@gmail.com": "Cezar",
    "rafaelbruning@gmail.com": "Rafael",
    "humbertolocks@gmail.com": "Humberto"
}

def padroniza_tecnico(tecnico):
    t = str(tecnico).strip().lower()
    return EMAILS_TECNICOS.get(t, tecnico)

def normaliza_nome(nome):
    if pd.isna(nome):
        return ""
    return unidecode.unidecode(str(nome)).lower().strip()
