import pdfplumber
import pandas as pd
import re

def extrair_transacoes_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        texto = ""
        for page in pdf.pages:
            texto += page.extract_text() + "\n"
    # Exemplo: ajuste o regex ao padrão do seu PDF
    padrao = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([-]?\d+,\d{2})'
    matches = re.findall(padrao, texto)
    dados = []
    for data, descricao, valor in matches:
        valor = float(valor.replace('.','').replace(',','.'))
        dados.append({'data': data, 'descricao': descricao.strip(), 'valor': valor, 'categoria': '', 'pessoa': '', 'status': ''})
    return pd.DataFrame(dados)
