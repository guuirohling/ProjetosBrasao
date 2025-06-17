def classify(transactions):
    for txn in transactions:
        if txn['type'] == 'IN':
            txn['classification'] = 'Recebimento de Clientes'
        elif txn['type'] == 'OUT':
            if txn['description'] in ['Pix enviado: "Cp :18236120-Sheila de Souza"', 'Pix enviado: "Cp :87795639-Rhalfi Meurer"']:
                txn['classification'] = 'Aluguel'
            elif txn['description'] == 'SIMPLES NACIONAL':
                txn['classification'] = 'Simples Nacional'
            elif txn['description'] == 'DARF NUMERADO':
                txn['classification'] = 'IRRF/INSS'
            elif txn['description'] == 'Pix enviado: "Cp :90400888-Larissa Kuhnen Lehmkuhl"':
                txn['classification'] = 'Distribuição de Lucros'
            else:
                txn['classification'] = ''
    return transactions
