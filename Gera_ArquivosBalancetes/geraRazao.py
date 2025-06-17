import os
from datetime import datetime

# Template do arquivo de configuração
template = """\
"ArquivoExportacao"="C:\\\\WKRadar\\\\BI\\\\Registros\\\\Razao\\\\{month}-{year}.txt";

"Separador"="|";

"EliminarCaracteres"="|";

"GerarSemAspas"="1";

"ExpCabecalhoColunas"="1";

"SimboloDecimal"=",";

"SimboloAgrupamento"=".";

"Modulo"="CN";

"Empresa"="Laboratorio";

"Modelo"="Com Debito, Credito e Saldo";

"Relatorio"="Razão";

"DataInicial"="01/{month}/{year_short}";

"DataFinal"="{last_day}/{month}/{year_short}";

"MostrarSubanalitica"="0";

"PonteiroIndice"="0";

"TotalDiario"="0";

"TotalMensal"="0";

"TotalAcumulado"="0";

"SaltarPagina"="0";

"RepetirConta"="0";

"SinalDC"="0";

"ListarSemMovimentacao"="1";

"ListarContaTotalizadora"="0";

"ListarLanGerenciais"="0";

"OrdemAlfabetica"="0";

"OrdemGrupoConta"="0";

"ImprimirLinhaSeparadora"="0";

"NegritarNomeConta"="0";

"EliminarSaldoZero"="0";

"NumeroRazao"="0";

"TamanhoLivro"="0";

"PaginaInicial"="0";

"Hash"="nZ2dn+7jnZ2cnOHMz8LfzNnC38TCnZ2dmP/M124Owp2dn5ruwsCN6cjPxNnCgY3u38jJxNnCjciN/szBycI=";

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
output_dir = "C:\\Users\\guuir\\OneDrive\\1- Implantação\\1- Utilitarios\\Gera_ArquivosBalancetes\\Razao\\"
os.makedirs(output_dir, exist_ok=True)

for year in range(2024, 2027):
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