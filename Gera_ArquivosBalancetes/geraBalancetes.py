import os
from datetime import datetime

# Template do arquivo de configuração
template = """\
"ArquivoExportacao"="C:\\\\WKRadar\\\\BI\\\\Registros\\\\Balancetes\\\\{month}-{year}.txt";

"Separador"="|";

"EliminarCaracteres"="|";

"GerarSemAspas"="1";

"ExpCabecalhoColunas"="1";

"SimboloDecimal"=",";

"SimboloAgrupamento"=".";

"Modulo"="CN";

"Empresa"="Laboratorio";

"Modelo"="WKBI_ExportaBalancetes";

"Relatorio"="Balancete";

"DataInicial"="01/{month}/{year_short}";

"DataFinal"="{last_day}/{month}/{year_short}";

"BalanceteGerencial"="0";

"SepararMeses"="0";

"PlanoAlternativo"="0";

"DesconsiderarZeramento"="1";

"PonteiroIndice"="0";

"TipoSinal"="0";

"TipoTotalizacao"="0";

"Sintetico"="0";

"SaltarPagina"="0";

"OrdemAlfabetica"="0";

"SepararTitulo"="0";

"NegritarTitulo"="1";

"RelacionarPorFilial"="0";

"SepararPorFilial"="0";

"ImprimirTodasContas"="0";

"EliminarSaldoZero"="0";

"EliminarSaldoZeroIndependente"="0";

"ImpressaoColorida"="0";

"DesconsiderarIFRS"="0";

"DemonstrarVinculo"="0";

"AgruparParalela"="0";

"GrauSintetico"="0";

"PaginaInicial"="1";

"Contrapartida"="";

"AgruparValoresRaizCNPJ"="0";

"Hash"="nZ2dn+7jnZ2cnOHMz8LfzNnC38TCnZ2dlO/MwczDzsjZyJ2dn5/65u/k8ujV3cLf2czvzMHMw87I2cje";
"""

# Função para determinar o último dia do mês
def get_last_day_of_month(year, month):
    if month == 2:  # Fevereiro
        # Verifica se é ano bissexto
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29
        return 28
    elif month in [4, 6, 9, 11]:  # Meses com 30 dias
        return 30
    return 31  # Meses com 31 dias

# Gera arquivos para cada mês de 01/2023 a 12/2026
output_dir = "C:\\Users\\guuir\\OneDrive\\1- Implantação\\1- Utilitarios\\Gera_ArquivosBalancetes\\Arquivos\\"
os.makedirs(output_dir, exist_ok=True)

for year in range(2027, 2029):
    for month in range(1, 13):
        month_str = f"{month:02d}"
        year_short = f"{year % 100:02d}"
        last_day = get_last_day_of_month(year, month)
        filename = f"{output_dir}/{month_str}-{year}.config"
        
        # Substitui os valores no template
        content = template.format(
            month=month_str,
            year=year,
            year_short=year_short,
            last_day=last_day
        )
        
        # Salva o arquivo
        with open(filename, "w", encoding="ANSI") as f:
            f.write(content)
        
        print(f"Arquivo gerado: {filename}")