@echo off
setlocal enabledelayedexpansion

:: CONFIGURAÇÕES
set "CAMINHO_CSV=C:\WKRadar\nfeEmitidas\chaves.csv"
set "PASTA_ORIGEM=C:\WKRadar\nfeEmitidas\todas"
set "PASTA_DESTINO=C:\WKRadar\nfeEmitidas\nfeNaoCanceladas"


:: Criar pasta de destino se necessário
if not exist "%PASTA_DESTINO%" (
    mkdir "%PASTA_DESTINO%"
)

:: PARA CADA CHAVE, BUSCA OS ARQUIVOS QUE A CONTENHAM
for /f "usebackq delims=" %%C in ("%CAMINHO_CSV%") do (
    set "CHAVE=%%C"
    set "CHAVE=!CHAVE: =!"
    echo Buscando arquivos com: !CHAVE!
    
    for %%F in ("%PASTA_ORIGEM%\*!CHAVE!*") do (
        if exist "%%F" (
            echo Copiando: %%~nxF
            copy /Y "%%F" "%PASTA_DESTINO%\" >nul
            echo Copiado: %%~nxF
        )
    )
)

echo.
echo Concluído!
pause