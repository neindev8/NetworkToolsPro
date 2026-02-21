@echo off
echo ================================
echo  NETWORK TOOLS PRO - INSTALADOR
echo ================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    echo Instala Python desde python.org
    pause
    exit /b 1
)

echo [1/2] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar dependencias
    pause
    exit /b 1
)

echo.
echo [2/2] Iniciando aplicacion...
python network_tools.py

pause
