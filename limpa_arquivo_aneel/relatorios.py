import os
import shutil

# Caminho da pasta de origem e destino
pasta_origem = "C:\WKRadar\Relatorios"
pasta_destino = "C:\WKRadar\Relatorios_erros"

# Adicione aqui todos os caracteres especiais que você deseja checar  tirado !@#$%^&*()[]{};:,./<>?\\|`~-=+"\'áàâãéèêíïóôõöúçñ
caracteres_especiais = set('ß¾├þÝÒÛÝ=')

# Cria a pasta destino, se não existir
os.makedirs(pasta_destino, exist_ok=True)

# Para armazenar quais caracteres especiais apareceram
caracteres_encontrados = set()

# Percorre os arquivos na pasta de origem
for nome_arquivo in os.listdir(pasta_origem):
    if any(char in caracteres_especiais for char in nome_arquivo):
        # Move o arquivo para a pasta de destino
        origem = os.path.join(pasta_origem, nome_arquivo)
        destino = os.path.join(pasta_destino, nome_arquivo)
        shutil.move(origem, destino)
        print(f"Arquivo movido: {nome_arquivo}")
        # Adiciona caracteres encontrados
        for char in nome_arquivo:
            if char in caracteres_especiais:
                caracteres_encontrados.add(char)

# Exibe todos os caracteres especiais encontrados
print("\nCaracteres especiais encontrados nos nomes dos arquivos:")
print(caracteres_encontrados)
