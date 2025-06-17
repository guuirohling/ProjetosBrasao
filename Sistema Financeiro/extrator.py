import pdfplumber
import re
import pandas as pd

def extrair_texto_pdf(file, senha=None):
    """
    Extrai todo o texto de um PDF usando pdfplumber.
    """
    with pdfplumber.open(file, password=senha) as pdf:
        texto = ""
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texto += t + "\n"
    return texto

def identificar_banco_e_titular(texto):
    """
    Tenta identificar o banco e o titular do cartão com base em padrões do texto extraído.
    Adapte ou expanda conforme seu uso.
    """
    if "Banco Inter" in texto or "inter.co" in texto:
        banco = "Inter"
        if "GUILHERME ROHLING LEMBECK" in texto:
            titular = "Guilherme"
        else:
            titular = "Desconhecido"
    elif "Itaú" in texto or "itau" in texto:
        banco = "Itaú"
        if "GUILHERME ROHLING LEMBECK" in texto:
            titular = "Guilherme"
        else:
            titular = "Desconhecido"
    elif "Santander" in texto or "Santander Way" in texto:
        banco = "Santander"
        if "LARISSA KUHNEN LEHMKUHL" in texto:
            titular = "Larissa"
        else:
            titular = "Desconhecido"
    else:
        banco, titular = "Desconhecido", "Desconhecido"
    return banco, titular

def extrair_lancamentos(texto, banco, titular):
    linhas = []

    if banco == "Inter":
        # Exemplo: 26 de abr. 2025 ZP BLACK WHITE SPORTS Parcela 01 de 03 - R$ 39,95
        pattern = r'(\d{2} de \w+\. \d{4}) (.+?)(?: Parcela (\d{2}) de (\d{2}))? - R\$ ?([\d\.,\-]+)'
        for data, desc, parcela_atual, parcela_total, valor in re.findall(pattern, texto):
            valor = float(valor.replace('.', '').replace(',', '.').replace(' ', ''))
            descricao = desc.strip()
            if parcela_atual and parcela_total:
                descricao += f" Parcela {parcela_atual}/{parcela_total}"
            if not any(x in descricao.upper() for x in ["PAGAMENTO", "ANTECIPADO", "CREDITO", "AJUSTE", "ESTORNO"]):
                linhas.append({
                    "data": data,
                    "descricao": descricao,
                    "valor": valor,
                    "banco": banco,
                    "titular": titular,
                    "categoria": "",
                    "quem_paga": "",
                    "pessoa_deve": ""
                })

    elif banco == "Santander":
        # Pega tanto despesas quanto parcelamentos do detalhamento (colunas R$)
        # Exemplo: 03/05 BISTEK SUPERMERCADOS 381,03   ou   03/05 RI HAPPY 01/02 139,99
        pattern = r'(\d{2}/\d{2}) ([A-Za-z0-9\*\-\. \/]+?)(?: (\d{2}/\d{2}))? ?(\d+,\d{2})'
        for data, desc, parcela, valor in re.findall(pattern, texto):
            valor = float(valor.replace('.', '').replace(',', '.'))
            descricao = desc.strip()
            if parcela:
                descricao += f" {parcela}"
            if not any(x in descricao.upper() for x in ["PAGAMENTO", "CREDITO", "AJUSTE", "ESTORNO"]):
                linhas.append({
                    "data": data + "/2025",
                    "descricao": descricao,
                    "valor": valor,
                    "banco": banco,
                    "titular": titular,
                    "categoria": "",
                    "quem_paga": "",
                    "pessoa_deve": ""
                })

    elif banco == "Itaú":
        # 1. Ignorar o bloco de "Compras parceladas - próximas faturas"
        texto = texto.split("Comprasparceladas-próximasfaturas")[0]
        
        # Exemplo: 03/05 Basicoisas 30,37   ou   27/06 PG *MINIMAL CLUB 12/12 99,90
        pattern = r'(\d{2}/\d{2}) ([\w\*\-\.\ /]+?)(?: (\d{2}/\d{2}))? ?([\-]?\d+,\d{2})'
        for data, desc, parcela, valor in re.findall(pattern, texto):
            valor = float(valor.replace('.', '').replace(',', '.'))
            descricao = desc.strip()
            if parcela:
                descricao += f" {parcela}"
            if not any(x in descricao.upper() for x in ["PAGAMENTO", "CREDITO", "AJUSTE", "ESTORNO"]):
                linhas.append({
                    "data": data + "/2025",
                    "descricao": descricao,
                    "valor": valor,
                    "banco": banco,
                    "titular": titular,
                    "categoria": "",
                    "quem_paga": "",
                    "pessoa_deve": ""
                })

    return pd.DataFrame(linhas)
