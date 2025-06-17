def sugerir_categoria(descricao, historico):
    for _, row in historico.iterrows():
        if row["descricao"] in descricao and row["categoria"]:
            return row["categoria"]
    return ""

def aprender_classificacao(descricao, categoria):
    # Aqui você pode salvar associações em um arquivo ou usar ML incremental futuramente
    pass
