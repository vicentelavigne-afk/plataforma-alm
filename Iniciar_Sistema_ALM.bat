@echo off
title Plataforma ALM Inteligente — Investtools
color 0B
echo.
echo  ==========================================
echo   PLATAFORMA ALM INTELIGENTE — INVESTTOOLS
echo  ==========================================
echo.

:: Ir para a pasta onde este arquivo esta
cd /d "%~dp0"

:: ── Verificar se Python esta instalado ────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ATENCAO: Python nao encontrado no sistema.
    echo.
    echo  Por favor instale o Python primeiro:
    echo  1. Abra o navegador e acesse: https://www.python.org/downloads/
    echo  2. Clique em "Download Python"
    echo  3. Execute o instalador
    echo  4. IMPORTANTE: marque a opcao "Add Python to PATH"
    echo  5. Finalize a instalacao
    echo  6. Feche esta janela e abra novamente o arquivo .bat
    echo.
    start https://www.python.org/downloads/
    pause
    exit
)

echo  Python encontrado! Verificando dependencias...
echo.

:: ── Instalar dependencias ─────────────────────────────────────────────────────
python -m pip install --upgrade pip --quiet
python -m pip install streamlit pandas plotly openpyxl --quiet

echo  Dependencias OK!
echo.
echo  Iniciando o sistema ALM...
echo  O Chrome vai abrir automaticamente em instantes.
echo.
echo  Para ENCERRAR o sistema: feche esta janela preta.
echo.

:: ── Iniciar o Streamlit ───────────────────────────────────────────────────────
python -m streamlit run app.py --server.headless false --browser.gatherUsageStats false

pause
