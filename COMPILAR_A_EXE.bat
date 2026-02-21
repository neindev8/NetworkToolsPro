@echo off
echo ===============================
echo  COMPILAR A EXE
echo ===============================
echo.

echo Instalando PyInstaller...
pip install pyinstaller

echo.
echo Compilando...
python build_exe.py

echo.
echo ================================
echo  LISTO!
echo  El archivo EXE esta en: dist\NetworkToolsPro.exe
echo ================================
pause
