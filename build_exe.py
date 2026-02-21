import PyInstaller.__main__
import os

# Compilar a EXE
PyInstaller.__main__.run([
    'network_tools.py',
    '--onefile',
    '--windowed',
    '--name=NetworkToolsPro',
    '--icon=NONE',
    '--clean',
    '--hidden-import=ping_module',
    '--hidden-import=traceroute_module',
])

print("\n✅ Compilación completada!")
print("El archivo EXE está en la carpeta 'dist'")
