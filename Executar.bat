@echo off
title Instalador e Inicializador do Dashboard Geoespacial
cls

:: Pula para a secao principal de verificacao de libs se o Python ja estiver OK.
goto checkPython

:installPython
:: Esta secao e chamada se o Python nao for encontrado.
echo.
echo -------------------------------------------------------------------
echo ATENCAO: Python nao foi encontrado no seu sistema.
echo -------------------------------------------------------------------
echo.
echo Verificando se o Winget (Gerenciador de Pacotes do Windows) esta disponivel...

where winget >nul 2>nul
if %errorlevel% neq 0 (
    goto manualInstall
)

echo Winget encontrado! Tentando instalar o Python 3.11 automaticamente.
echo.
echo IMPORTANTE: Uma janela de permissao de Administrador (UAC) pode aparecer.
echo             Por favor, aceite para a instalacao continuar.
echo.
pause

:: Comando para instalar o Python 3.11 via Winget de forma silenciosa e adicionando ao PATH
winget install --id Python.Python.3.11 -s --accept-source-agreements --override "/quiet InstallAllUsers=1 PrependPath=1"

echo.
echo Instalacao via Winget finalizada. Verificando novamente...
goto checkPython

:manualInstall
:: Secao para caso o Winget nao seja encontrado.
echo.
echo Winget nao encontrado.
echo.
echo Para usar este dashboard, por favor, instale o Python 3.11 do site oficial:
echo https://www.python.org/downloads/
echo.
echo IMPORTANTE: Na instalacao, marque a caixa que diz "Add Python to PATH".
echo.
pause
exit /b

:checkPython
:: Secao principal de verificacao.
echo Verificando a instalacao do Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    goto installPython
)
echo Python encontrado!
echo.

:libs
:: --- PASSO 2: INSTALAR AS BIBLIOTECAS NECESSARIAS ---
echo Verificando e instalando as bibliotecas necessarias...
echo Isso pode levar alguns minutos na primeira vez.
echo.
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo -------------------------------------------------------------------
    echo ERRO: Ocorreu um problema ao instalar as bibliotecas.
    echo Verifique sua conexao com a internet e tente novamente.
    echo -------------------------------------------------------------------
    echo.
    pause
    exit /b
)
echo Bibliotecas instaladas com sucesso!
echo.

:: --- PASSO 3: EXECUTAR O DASHBOARD ---
echo Tudo pronto! Iniciando o dashboard...
echo O dashboard abrira no seu navegador. Feche esta janela preta para encerrar o programa.
echo.
streamlit run Dashboard.py

pause